-- Preserve request-correlation metadata in the durable replay log.

ALTER TABLE realtime_events ADD COLUMN IF NOT EXISTS correlation_id TEXT;
ALTER TABLE realtime_events ADD COLUMN IF NOT EXISTS causation_id TEXT;

CREATE INDEX IF NOT EXISTS idx_realtime_events_tenant_occurred
    ON realtime_events (tenant_id, occurred_at DESC);
