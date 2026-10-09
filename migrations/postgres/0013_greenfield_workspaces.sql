-- Allow OAE to create governed greenfield workspaces before a GitHub repository exists.
ALTER TABLE workspaces ALTER COLUMN repository_id DROP NOT NULL;
ALTER TABLE workspaces ALTER COLUMN source_revision_id DROP NOT NULL;
