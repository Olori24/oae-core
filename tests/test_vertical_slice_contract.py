from oae.core.vertical_slice_contract import VerticalSliceContract


def test_vertical_slice_contract_accepts_generated_shape(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "web/lib").mkdir(parents=True)
    (tmp_path / "src/main.py").write_text("from fastapi import FastAPI\n", encoding="utf-8")
    (tmp_path / "web/lib/api.ts").write_text("export const health = () => fetch('/health')\n", encoding="utf-8")

    result = VerticalSliceContract().validate(tmp_path)

    assert result["passed"] is True
    assert all(result["checks"].values())


def test_vertical_slice_contract_reports_missing_frontend_api(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/main.py").write_text("app = None\n", encoding="utf-8")

    result = VerticalSliceContract().validate(tmp_path)

    assert result["passed"] is False
    assert result["checks"]["frontend_api_module"] is False
