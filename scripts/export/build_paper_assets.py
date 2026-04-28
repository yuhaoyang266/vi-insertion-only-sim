from __future__ import annotations

import argparse
import filecmp
import json
from pathlib import Path
import subprocess
import sys
import tempfile


DEFAULT_MANIFEST = Path("artifacts/main_benchmark/main_benchmark_manifest.json")
DEFAULT_CONFIRM_REPORT = Path(
    "outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json"
)
DEFAULT_EVIDENCE_OUTPUT_DIR = Path("outputs/evidence_matrix")
EVIDENCE_OUTPUT_FILENAMES = (
    "three_dof_evidence_matrix.json",
    "three_dof_evidence_matrix.csv",
    "three_dof_evidence_matrix.md",
    "three_dof_contact_gate_matrix.png",
    "three_dof_contact_gate_matrix.pdf",
    "three_dof_sprint2_main_table.json",
    "three_dof_sprint2_main_table.csv",
    "three_dof_sprint2_main_table.md",
)
EVIDENCE_FIGURE_FILENAMES = frozenset(
    {
        "three_dof_contact_gate_matrix.png",
        "three_dof_contact_gate_matrix.pdf",
    }
)
TEXT_EVIDENCE_SUFFIXES = frozenset({".csv", ".md"})
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PDF_SIGNATURE = b"%PDF-"


def _cli_path(path: Path) -> str:
    return Path(path).as_posix()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or check the canonical paper-facing table, Figure 2, and evidence matrix."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--confirm-report", type=Path, default=DEFAULT_CONFIRM_REPORT)
    parser.add_argument("--evidence-output-dir", type=Path, default=DEFAULT_EVIDENCE_OUTPUT_DIR)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run check mode for table/Figure 2 exporters and regenerate evidence matrix in place.",
    )
    return parser.parse_args(argv)


def build_evidence_command(args: argparse.Namespace, *, output_dir: Path | None = None) -> list[str]:
    manifest = _cli_path(args.manifest)
    return [
        sys.executable,
        "scripts/experiments/export_3dof_evidence_matrix.py",
        "--confirm-report",
        _cli_path(args.confirm_report),
        "--manifest",
        manifest,
        "--output-dir",
        _cli_path(args.evidence_output_dir if output_dir is None else output_dir),
    ]


def build_commands(args: argparse.Namespace) -> list[list[str]]:
    manifest = _cli_path(args.manifest)
    table_command = [
        sys.executable,
        "scripts/export/export_paper_only_sim_benchmark_table.py",
        "--manifest",
        manifest,
    ]
    figure_command = [
        sys.executable,
        "scripts/export/export_paper_only_sim_figure2.py",
        "--manifest",
        manifest,
    ]
    if args.check:
        table_command.append("--check")
        figure_command.append("--check")
        return [table_command, figure_command]
    return [table_command, figure_command, build_evidence_command(args)]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_repo_path(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else _repo_root() / path


def run_evidence_check(args: argparse.Namespace) -> None:
    stale: list[str] = []
    expected_dir = _resolve_repo_path(args.evidence_output_dir)
    with tempfile.TemporaryDirectory() as tmp_dir:
        generated_dir = Path(tmp_dir)
        subprocess.run(
            build_evidence_command(args, output_dir=generated_dir),
            cwd=_repo_root(),
            check=True,
        )
        for filename in EVIDENCE_OUTPUT_FILENAMES:
            expected_path = expected_dir / filename
            generated_path = generated_dir / filename
            if not expected_path.exists():
                stale.append(f"Missing checked-in output: {expected_path}")
            elif not _same_evidence_output(expected_path, generated_path):
                stale.append(f"Output differs: {expected_path}")
    if stale:
        raise SystemExit("Evidence matrix outputs are stale:\n" + "\n".join(stale))


def _same_evidence_output(expected_path: Path, generated_path: Path) -> bool:
    if expected_path.name == "three_dof_sprint2_main_table.json":
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        generated = json.loads(generated_path.read_text(encoding="utf-8"))
        expected["source_artifacts"]["evidence_matrix"] = "<evidence_matrix>"
        generated["source_artifacts"]["evidence_matrix"] = "<evidence_matrix>"
        return expected == generated
    if expected_path.name == "three_dof_sprint2_main_table.md":
        expected = expected_path.read_text(encoding="utf-8").splitlines()
        generated = generated_path.read_text(encoding="utf-8").splitlines()
        return _normalize_sprint2_markdown(expected) == _normalize_sprint2_markdown(generated)
    if expected_path.name in EVIDENCE_FIGURE_FILENAMES:
        return _same_evidence_figure(expected_path, generated_path)
    if expected_path.suffix == ".json":
        return _same_json(expected_path, generated_path)
    if expected_path.suffix in TEXT_EVIDENCE_SUFFIXES:
        return _same_text_lines(expected_path, generated_path)
    return filecmp.cmp(expected_path, generated_path, shallow=False)


def _same_json(expected_path: Path, generated_path: Path) -> bool:
    try:
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        generated = json.loads(generated_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return expected == generated


def _same_text_lines(expected_path: Path, generated_path: Path) -> bool:
    try:
        expected = expected_path.read_text(encoding="utf-8").splitlines()
        generated = generated_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    return expected == generated


def _same_evidence_figure(expected_path: Path, generated_path: Path) -> bool:
    if expected_path.suffix == ".png":
        expected_dimensions = _png_dimensions(expected_path)
        return expected_dimensions is not None and expected_dimensions == _png_dimensions(
            generated_path
        )
    if expected_path.suffix == ".pdf":
        return _is_pdf(expected_path) and _is_pdf(generated_path)
    return False


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        header = path.read_bytes()[:24]
    except OSError:
        return None
    if (
        len(header) < 24
        or not header.startswith(PNG_SIGNATURE)
        or header[12:16] != b"IHDR"
    ):
        return None
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    if width <= 0 or height <= 0:
        return None
    return width, height


def _is_pdf(path: Path) -> bool:
    try:
        content = path.read_bytes()
    except OSError:
        return False
    return content.startswith(PDF_SIGNATURE) and content.rstrip().endswith(b"%%EOF")


def _normalize_sprint2_markdown(lines: list[str]) -> list[str]:
    return [
        "Evidence-matrix source: `<evidence_matrix>`"
        if line.startswith("Evidence-matrix source: `")
        else line
        for line in lines
    ]


def main(args: argparse.Namespace | None = None) -> None:
    parsed_args = parse_args() if args is None else args
    for command in build_commands(parsed_args):
        subprocess.run(command, cwd=_repo_root(), check=True)
    if parsed_args.check:
        run_evidence_check(parsed_args)


if __name__ == "__main__":
    main()
