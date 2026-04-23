import json
import os
from pathlib import Path
import subprocess
import sys


def test_cli_exports_sprint3_kickoff_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = (
        repo_root
        / "scripts"
        / "experiments"
        / "export_sprint3_teacher_mini_ablation_kickoff.py"
    )
    output_dir = tmp_path / "sprint3_teacher_mini_ablation"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "sprint3_teacher_mini_ablation_kickoff" in completed.stdout
    json_path = output_dir / "sprint3_teacher_mini_ablation_kickoff.json"
    csv_path = output_dir / "sprint3_teacher_mini_ablation_kickoff.csv"
    markdown_path = output_dir / "sprint3_teacher_mini_ablation_kickoff.md"
    pdf_path = output_dir / "sprint3_teacher_mini_ablation_kickoff_matrix.pdf"
    png_path = output_dir / "sprint3_teacher_mini_ablation_kickoff_matrix.png"
    assert json_path.exists()
    assert csv_path.exists()
    assert markdown_path.exists()
    assert pdf_path.exists()
    assert png_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["target_question"]["primary_axis"] == "teacher_support_quality"
    assert payload["condition_count"] == 4
    assert "teacher_support_quality" in csv_path.read_text(encoding="utf-8")
    assert "not a leaderboard" in markdown_path.read_text(encoding="utf-8")
