import importlib.util
from pathlib import Path
import sys


def _load_runner_module():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "experiments"
        / "export_sprint4_clearance_shift.py"
    )
    spec = importlib.util.spec_from_file_location(
        "export_sprint4_clearance_shift_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_runner_uses_default_sprint4_contract_and_writes_artifacts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    calls: dict[str, object] = {}

    def _fake_run_sweep(*, train_seeds, episodes_per_seed, max_episode_steps):
        calls["train_seeds"] = list(train_seeds)
        calls["episodes_per_seed"] = int(episodes_per_seed)
        calls["max_episode_steps"] = int(max_episode_steps)
        return {"export_name": "sprint4_clearance_shift", "suite_rows": []}

    def _fake_export(report, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "sprint4_clearance_shift.json"
        csv_path = output_dir / "sprint4_clearance_shift.csv"
        markdown_path = output_dir / "sprint4_clearance_shift.md"
        pdf_path = output_dir / "sprint4_clearance_shift_summary.pdf"
        png_path = output_dir / "sprint4_clearance_shift_summary.png"
        json_path.write_text("{}", encoding="utf-8")
        csv_path.write_text("suite_name\n", encoding="utf-8")
        markdown_path.write_text("# Sprint 4 Clearance Shift\n", encoding="utf-8")
        pdf_path.write_text("pdf", encoding="utf-8")
        png_path.write_text("png", encoding="utf-8")
        calls["report"] = dict(report)
        calls["output_dir"] = output_dir
        return {
            "json_path": json_path,
            "csv_path": csv_path,
            "markdown_path": markdown_path,
            "pdf_path": pdf_path,
            "png_path": png_path,
        }

    monkeypatch.setattr(module, "run_sprint4_clearance_shift_sweep", _fake_run_sweep)
    monkeypatch.setattr(
        module, "export_sprint4_clearance_shift_artifacts", _fake_export
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_sprint4_clearance_shift.py",
            "--output-dir",
            str(tmp_path / "sprint4_clearance_shift"),
        ],
    )

    module.main()

    assert calls["train_seeds"] == [0, 1, 2, 3, 4]
    assert calls["episodes_per_seed"] == 100
    assert calls["max_episode_steps"] == 64
    assert calls["report"]["export_name"] == "sprint4_clearance_shift"
    assert (tmp_path / "sprint4_clearance_shift" / "sprint4_clearance_shift.json").exists()
    assert (tmp_path / "sprint4_clearance_shift" / "sprint4_clearance_shift_summary.pdf").exists()
    assert (tmp_path / "sprint4_clearance_shift" / "sprint4_clearance_shift_summary.png").exists()
