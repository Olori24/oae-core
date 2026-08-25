"""Provision durable, tenant-scoped workspaces from immutable repository revisions."""

import hashlib
import json
import mimetypes
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from oae.api.config import settings
from oae.api.db import db
from oae.api.domain_events import DomainEventWriter
from oae.api.workspace_models import (
    WorkspaceManifest,
    WorkspaceManifestEntry,
    WorkspacePurpose,
    WorkspaceRecord,
    WorkspaceState,
)
from oae.core.process_security import run_git, validate_git_ref, validate_repository_url

EXCLUDED_DIRECTORY_NAMES = {".git", ".next", "__pycache__", "node_modules"}


class WorkspaceError(RuntimeError):
    """Base error for workspace provisioning failures."""


class PinnedRevisionNotFound(WorkspaceError):
    """Raised when the requested tenant repository revision is absent."""


class WorkspaceQuotaExceeded(WorkspaceError):
    """Raised before storage is committed when a tenant allocation exceeds its quota."""


@dataclass(frozen=True)
class PinnedRepositoryRevision:
    """Repository metadata sufficient to materialize an immutable source revision."""

    tenant_id: str
    repository_id: str
    revision_id: str
    clone_url: str
    commit_sha: str


class RevisionMaterializer(Protocol):
    """Materializes a pinned revision into an isolated, empty target directory."""

    def materialize(self, revision: PinnedRepositoryRevision, target: Path) -> None: ...


class WorkspaceRepository(Protocol):
    """Persistence boundary for workspace metadata and quota reservation."""

    def get_pinned_revision(
        self, tenant_id: str, repository_id: str, revision_id: str
    ) -> PinnedRepositoryRevision | None: ...

    def reserve(self, record: WorkspaceRecord, entries: list[WorkspaceManifestEntry]) -> None: ...

    def mark_ready(self, tenant_id: str, workspace_id: str, ready_at: datetime) -> None: ...

    def mark_failed(self, tenant_id: str, workspace_id: str, failure_code: str) -> None: ...


class GitRevisionMaterializer:
    """Checks out one immutable Git commit without retaining repository metadata."""

    def materialize(self, revision: PinnedRepositoryRevision, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        clone_url = validate_repository_url(revision.clone_url)
        commit_sha = validate_git_ref(revision.commit_sha)
        run_git(
            ["clone", "--no-checkout", "--filter=blob:none", clone_url, str(target.resolve())],
            cwd=target.parent,
            check=True,
            capture_output=True,
            text=True,
        )
        run_git(
            ["fetch", "--depth", "1", "origin", commit_sha],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        )
        run_git(
            ["checkout", "--detach", commit_sha],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        )
        shutil.rmtree(target / ".git", ignore_errors=True)


class PostgresWorkspaceRepository:
    """PostgreSQL workspace metadata store with transaction-scoped tenant quota reservation."""

    def __init__(self, event_writer: DomainEventWriter | None = None):
        self.event_writer = event_writer or DomainEventWriter()

    def get_pinned_revision(
        self, tenant_id: str, repository_id: str, revision_id: str
    ) -> PinnedRepositoryRevision | None:
        with db() as conn:
            row = conn.execute(
                "SELECT revision.id,revision.repository_id,repository.clone_url,revision.commit_sha "
                "FROM repository_revisions revision "
                "JOIN repositories repository "
                "ON repository.tenant_id=revision.tenant_id AND repository.id=revision.repository_id "
                "WHERE revision.tenant_id=? AND revision.repository_id=? AND revision.id=? "
                "AND repository.status='active' AND repository.deleted_at IS NULL",
                (tenant_id, repository_id, revision_id),
            ).fetchone()
        if not row:
            return None
        return PinnedRepositoryRevision(
            tenant_id=tenant_id,
            repository_id=row[1],
            revision_id=row[0],
            clone_url=row[2],
            commit_sha=row[3],
        )

    def reserve(self, record: WorkspaceRecord, entries: list[WorkspaceManifestEntry]) -> None:
        if settings.database_backend != "postgres":
            raise WorkspaceError("Durable workspace reservation requires PostgreSQL.")
        with db() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(?, 0))", (record.tenant_id,))
            usage = conn.execute(
                "SELECT COALESCE(SUM(size_bytes),0),COUNT(*) FROM workspaces "
                "WHERE tenant_id=? AND state IN ('provisioning','ready') "
                "AND retention_expires_at > now()",
                (record.tenant_id,),
            ).fetchone()
            used_bytes, used_count = int(usage[0]), int(usage[1])
            if used_bytes + record.size_bytes > settings.workspace_quota_bytes:
                raise WorkspaceQuotaExceeded("Workspace byte quota exceeded for this tenant.")
            if used_count + 1 > settings.workspace_quota_count:
                raise WorkspaceQuotaExceeded("Workspace count quota exceeded for this tenant.")
            conn.execute(
                "INSERT INTO workspaces("
                "id,tenant_id,repository_id,source_revision_id,parent_workspace_id,purpose,state,"
                "storage_uri,manifest_uri,manifest_sha256,size_bytes,file_count,retention_expires_at,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    record.id,
                    record.tenant_id,
                    record.repository_id,
                    record.source_revision_id,
                    record.parent_workspace_id,
                    record.purpose.value,
                    WorkspaceState.PROVISIONING.value,
                    record.storage_uri,
                    record.manifest_uri,
                    record.manifest_sha256,
                    record.size_bytes,
                    record.file_count,
                    record.retention_expires_at,
                    record.created_at,
                ),
            )
            for entry in entries:
                conn.execute(
                    "INSERT INTO workspace_manifest_entries("
                    "id,tenant_id,workspace_id,relative_path,object_key,sha256,size_bytes,"
                    "content_type,is_executable,created_at"
                    ") VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        entry.id,
                        record.tenant_id,
                        record.id,
                        entry.relative_path,
                        entry.object_key,
                        entry.sha256,
                        entry.size_bytes,
                        entry.content_type,
                        entry.is_executable,
                        entry.created_at,
                    ),
                )
            self.event_writer.append(
                conn,
                tenant_id=record.tenant_id,
                aggregate_type="workspace",
                aggregate_id=record.id,
                event_type="workspace.provisioning",
                payload={
                    "purpose": record.purpose.value,
                    "repository_id": record.repository_id,
                    "source_revision_id": record.source_revision_id,
                    "file_count": record.file_count,
                    "size_bytes": record.size_bytes,
                    "manifest_sha256": record.manifest_sha256,
                },
                occurred_at=record.created_at,
            )

    def mark_ready(self, tenant_id: str, workspace_id: str, ready_at: datetime) -> None:
        with db() as conn:
            changed = conn.execute(
                "UPDATE workspaces SET state='ready',ready_at=? "
                "WHERE tenant_id=? AND id=? AND state='provisioning'",
                (ready_at, tenant_id, workspace_id),
            ).rowcount
            if changed == 1:
                self.event_writer.append(
                    conn,
                    tenant_id=tenant_id,
                    aggregate_type="workspace",
                    aggregate_id=workspace_id,
                    event_type="workspace.ready",
                    payload={"ready_at": ready_at.isoformat()},
                    occurred_at=ready_at,
                )
        if changed != 1:
            raise WorkspaceError("Workspace readiness transition lost its provisioning ownership.")

    def mark_failed(self, tenant_id: str, workspace_id: str, failure_code: str) -> None:
        with db() as conn:
            changed = conn.execute(
                "UPDATE workspaces SET state='failed',failure_code=? "
                "WHERE tenant_id=? AND id=? AND state='provisioning'",
                (failure_code, tenant_id, workspace_id),
            ).rowcount
            if changed == 1:
                self.event_writer.append(
                    conn,
                    tenant_id=tenant_id,
                    aggregate_type="workspace",
                    aggregate_id=workspace_id,
                    event_type="workspace.failed",
                    payload={"failure_code": failure_code},
                )


class WorkspaceManager:
    """Creates immutable workspace snapshots and reserves tenant storage before activation."""

    def __init__(
        self,
        root: Path | None = None,
        repository: WorkspaceRepository | None = None,
        materializer: RevisionMaterializer | None = None,
    ):
        self.root = (root or Path(settings.workspace_root)).expanduser().resolve()
        self.repository = repository or PostgresWorkspaceRepository()
        self.materializer = materializer or GitRevisionMaterializer()

    def provision(
        self,
        tenant_id: str,
        repository_id: str,
        revision_id: str,
        purpose: WorkspacePurpose = WorkspacePurpose.SOURCE,
        parent_workspace_id: str | None = None,
    ) -> tuple[WorkspaceRecord, WorkspaceManifest]:
        revision = self.repository.get_pinned_revision(tenant_id, repository_id, revision_id)
        if revision is None:
            raise PinnedRevisionNotFound("Pinned repository revision was not found for this tenant.")

        workspace_id = str(uuid4())
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(days=settings.workspace_retention_days)
        staging_root = self.root / ".staging" / workspace_id
        content_root = staging_root / "content"
        final_root = self._workspace_root(tenant_id, workspace_id)
        reserved = False
        try:
            self.materializer.materialize(revision, content_root)
            entries = self._manifest_entries(tenant_id, workspace_id, content_root, created_at)
            manifest_sha256 = self._manifest_sha256(
                tenant_id, workspace_id, repository_id, revision_id, purpose, entries
            )
            storage_uri = final_root.as_uri()
            manifest_uri = (final_root / "manifest.json").as_uri()
            record = WorkspaceRecord(
                id=workspace_id,
                tenant_id=tenant_id,
                repository_id=repository_id,
                source_revision_id=revision_id,
                parent_workspace_id=parent_workspace_id,
                purpose=purpose,
                state=WorkspaceState.PROVISIONING,
                storage_uri=storage_uri,
                manifest_uri=manifest_uri,
                manifest_sha256=manifest_sha256,
                size_bytes=sum(entry.size_bytes for entry in entries),
                file_count=len(entries),
                retention_expires_at=expires_at,
                created_at=created_at,
            )
            manifest = WorkspaceManifest(
                workspace_id=workspace_id,
                tenant_id=tenant_id,
                repository_id=repository_id,
                source_revision_id=revision_id,
                purpose=purpose,
                storage_uri=storage_uri,
                manifest_sha256=manifest_sha256,
                entries=entries,
                created_at=created_at,
                retention_expires_at=expires_at,
            )
            self.repository.reserve(record, entries)
            reserved = True
            (staging_root / "manifest.json").write_text(
                manifest.model_dump_json(indent=2), encoding="utf-8"
            )
            final_root.parent.mkdir(parents=True, exist_ok=True)
            if final_root.exists():
                raise WorkspaceError("A workspace storage path collision occurred.")
            shutil.move(str(staging_root), str(final_root))
            ready_at = datetime.now(timezone.utc)
            self.repository.mark_ready(tenant_id, workspace_id, ready_at)
            return record.model_copy(update={"state": WorkspaceState.READY, "ready_at": ready_at}), manifest
        except Exception:
            shutil.rmtree(staging_root, ignore_errors=True)
            shutil.rmtree(final_root, ignore_errors=True)
            if reserved:
                self.repository.mark_failed(tenant_id, workspace_id, "workspace_provisioning_failed")
            raise

    def _workspace_root(self, tenant_id: str, workspace_id: str) -> Path:
        return self.root / "tenant" / tenant_id / "workspace" / workspace_id

    def _manifest_entries(
        self,
        tenant_id: str,
        workspace_id: str,
        content_root: Path,
        created_at: datetime,
    ) -> list[WorkspaceManifestEntry]:
        if not content_root.is_dir():
            raise WorkspaceError("Revision materializer did not create a workspace directory.")
        self._remove_excluded_directories(content_root)
        entries: list[WorkspaceManifestEntry] = []
        for path in sorted(content_root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(content_root)
            if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative.parts):
                continue
            size_bytes = path.stat().st_size
            if size_bytes > settings.workspace_file_max_bytes:
                raise WorkspaceError(f"Workspace file exceeds configured limit: {relative.as_posix()}")
            relative_path = relative.as_posix()
            object_key = f"tenant/{tenant_id}/workspace/{workspace_id}/content/{relative_path}"
            entries.append(
                WorkspaceManifestEntry(
                    id=str(uuid4()),
                    relative_path=relative_path,
                    object_key=object_key,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    size_bytes=size_bytes,
                    content_type=mimetypes.guess_type(relative_path)[0] or "application/octet-stream",
                    is_executable=bool(path.stat().st_mode & 0o111),
                    created_at=created_at,
                )
            )
        return entries

    @staticmethod
    def _remove_excluded_directories(content_root: Path) -> None:
        for name in EXCLUDED_DIRECTORY_NAMES:
            for directory in list(content_root.rglob(name)):
                if directory.is_dir() and not directory.is_symlink():
                    shutil.rmtree(directory)

    @staticmethod
    def _manifest_sha256(
        tenant_id: str,
        workspace_id: str,
        repository_id: str,
        revision_id: str,
        purpose: WorkspacePurpose,
        entries: list[WorkspaceManifestEntry],
    ) -> str:
        payload = {
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "repository_id": repository_id,
            "source_revision_id": revision_id,
            "purpose": purpose.value,
            "entries": [entry.model_dump(mode="json") for entry in entries],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
