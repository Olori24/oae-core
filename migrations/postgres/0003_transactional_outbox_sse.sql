-- OAE transactional outbox projection and replayable SSE event foundation.
-- PostgreSQL is the durable event authority; NOTIFY is only a low-latency wake-up signal.

ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS tenant_sequence BIGINT;
ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS aggregate_sequence BIGINT;
ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS correlation_id TEXT;
ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS causation_id TEXT;
ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS relay_lease_token TEXT;
ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS relay_lease_expires_at TIMESTAMPTZ;
ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS last_error_redacted TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_outbox_tenant_sequence_positive'
    ) THEN
        ALTER TABLE outbox_events
            ADD CONSTRAINT ck_outbox_tenant_sequence_positive
            CHECK (tenant_sequence IS NULL OR tenant_sequence > 0);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_outbox_aggregate_sequence_positive'
    ) THEN
        ALTER TABLE outbox_events
            ADD CONSTRAINT ck_outbox_aggregate_sequence_positive
            CHECK (aggregate_sequence IS NULL OR aggregate_sequence > 0);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_outbox_event_sequences_paired'
    ) THEN
        ALTER TABLE outbox_events
            ADD CONSTRAINT ck_outbox_event_sequences_paired
            CHECK (
                (tenant_sequence IS NULL AND aggregate_sequence IS NULL)
                OR (tenant_sequence IS NOT NULL AND aggregate_sequence IS NOT NULL)
            );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS tenant_event_cursors (
    tenant_id TEXT PRIMARY KEY REFERENCES tenants(id),
    last_sequence BIGINT NOT NULL DEFAULT 0 CHECK (last_sequence >= 0)
);

CREATE TABLE IF NOT EXISTS aggregate_event_cursors (
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    last_sequence BIGINT NOT NULL DEFAULT 0 CHECK (last_sequence >= 0),
    PRIMARY KEY (tenant_id, aggregate_type, aggregate_id)
);

CREATE TABLE IF NOT EXISTS tenant_event_publication_cursors (
    tenant_id TEXT PRIMARY KEY REFERENCES tenants(id),
    last_published_sequence BIGINT NOT NULL DEFAULT 0 CHECK (last_published_sequence >= 0)
);

CREATE TABLE IF NOT EXISTS realtime_events (
    id TEXT PRIMARY KEY,
    outbox_event_id TEXT NOT NULL UNIQUE,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    tenant_sequence BIGINT NOT NULL CHECK (tenant_sequence > 0),
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    aggregate_sequence BIGINT NOT NULL CHECK (aggregate_sequence > 0),
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    occurred_at TIMESTAMPTZ NOT NULL,
    projected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, tenant_sequence),
    UNIQUE (tenant_id, aggregate_type, aggregate_id, aggregate_sequence)
);

-- Replace the pre-lease publishable index from migration 0002 with the relay-oriented name.
DROP INDEX IF EXISTS idx_outbox_publishable;
CREATE INDEX IF NOT EXISTS idx_outbox_relay_claim
    ON outbox_events (next_publish_at, occurred_at)
    WHERE published_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_outbox_relay_lease
    ON outbox_events (relay_lease_expires_at)
    WHERE published_at IS NULL AND relay_lease_expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_outbox_tenant_sequence
    ON outbox_events (tenant_id, tenant_sequence)
    WHERE tenant_sequence IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_outbox_events_tenant_sequence
    ON outbox_events (tenant_id, tenant_sequence)
    WHERE tenant_sequence IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_outbox_events_aggregate_sequence
    ON outbox_events (tenant_id, aggregate_type, aggregate_id, aggregate_sequence)
    WHERE aggregate_sequence IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_realtime_events_tenant_replay
    ON realtime_events (tenant_id, tenant_sequence);
CREATE INDEX IF NOT EXISTS idx_realtime_events_aggregate_replay
    ON realtime_events (tenant_id, aggregate_type, aggregate_id, aggregate_sequence);
CREATE INDEX IF NOT EXISTS idx_realtime_events_retention
    ON realtime_events (occurred_at);

CREATE OR REPLACE FUNCTION oae_notify_realtime_event()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- Payload is the durable event identifier only; clients always replay from realtime_events.
    PERFORM pg_notify('oae_realtime_event', NEW.id);
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_oae_notify_realtime_event ON realtime_events;
CREATE TRIGGER trg_oae_notify_realtime_event
AFTER INSERT ON realtime_events
FOR EACH ROW
EXECUTE FUNCTION oae_notify_realtime_event();

COMMENT ON TABLE realtime_events IS
    'Immutable tenant-safe replay log for SSE and future WebSocket delivery.';
COMMENT ON COLUMN realtime_events.outbox_event_id IS
    'Stable outbox idempotency key; projection retries must reuse it.';
COMMENT ON TABLE tenant_event_cursors IS
    'Tenant-wide sequence allocation state; increment only in the domain mutation transaction.';
COMMENT ON TABLE aggregate_event_cursors IS
    'Per-aggregate sequence allocation state for job and workspace replay.';
COMMENT ON TABLE tenant_event_publication_cursors IS
    'Contiguous relay publication fence for monotonic tenant SSE cursors.';
