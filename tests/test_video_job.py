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
    assert sha256_file(target) == "c1cda26362828b69266512052b97cb3729e3b052e4ade47c0a1e3383defe73c7"
