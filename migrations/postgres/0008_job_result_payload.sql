-- Add the persisted job result payload used by API projections.

ALTER TABLE jobs
    ADD COLUMN IF NOT EXISTS result JSONB;
