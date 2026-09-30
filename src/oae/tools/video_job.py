"""Governed metadata contract for OAE video jobs.

This module is intentionally renderer-agnostic. HyperFrames produces the media;
this contract records what OAE must know before an artifact can be accepted.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class VideoVariant:
    name: str
    width: int
    height: int


@dataclass(frozen=True)
class VideoJob:
    job_id: str
    title: str
    source_revision: str
    composition_hash: str
    asset_manifest_hash: str
    variants: tuple[VideoVariant, ...]


@dataclass(frozen=True)
class ArtifactReceipt:
    job_id: str
    variant: str
    output_path: str
    output_sha256: str
    verified: bool
    approved: bool


def sha256_file(path: Path) -> str:
    """Return a content hash suitable for governed artifact provenance."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def job_manifest(job: VideoJob) -> str:
    """Serialize stable job metadata for audit logs and idempotency keys."""
    payload = asdict(job)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
