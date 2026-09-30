from pathlib import Path

import pytest

from oae.tools.hyperframes import HyperFramesError, HyperFramesRunner, RenderRequest


def test_render_requires_index_html(tmp_path: Path) -> None:
    with pytest.raises(HyperFramesError, match="index.html"):
        HyperFramesRunner().render(RenderRequest(project_dir=tmp_path))


def test_render_rejects_missing_project(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(HyperFramesError, match="does not exist"):
        HyperFramesRunner().render(RenderRequest(project_dir=missing))
