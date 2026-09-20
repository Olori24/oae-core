from pathlib import Path

from oae.tools.video_job import VideoJob, VideoVariant, job_manifest, sha256_file


def test_job_manifest_is_stable() -> None:
    job = VideoJob(
        job_id="job-001",
        title="Demo",
        source_revision="abc123",
        composition_hash="comp",
        asset_manifest_hash="assets",
        variants=(VideoVariant("portrait", 1080, 1920),),
    )
    assert job_manifest(job) == job_manifest(job)


def test_sha256_file(tmp_path: Path) -> None:
    target = tmp_path / "video.mp4"
    target.write_bytes(b"proof")
    assert sha256_file(target) == "a4f0f4b5b7e6c2f2d0b4f2f0b7e7e6e7c4c7b4b7c0e3e2c4c0e1f5f0b4d6e7a9"
