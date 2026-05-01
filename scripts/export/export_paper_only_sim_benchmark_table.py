from __future__ import annotations

import argparse
import difflib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
import sys
import tempfile


DEFAULT_MANIFEST = Path("artifacts/main_benchmark/main_benchmark_manifest.json")


@dataclass(frozen=True)
class ExportInputs:
    benchmark_input: Path
    statistics_report_input: Path | None
    provenance_label: str
    generating_command: str
    git_commit: str | None


def _load_paper_tables_module():
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    module_path = src_root / "vi_full" / "paper_tables.py"
    spec = importlib.util.spec_from_file_location("paper_tables_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load paper table module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_artifact_registry_module():
    repo_root = _repo_root()
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    module_path = src_root / "vi_full" / "artifact_registry.py"
    spec = importlib.util.spec_from_file_location("artifact_registry_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load artifact registry module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export the paper-facing 3DoF benchmark table.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Canonical benchmark manifest. Defaults to the stage4 main benchmark; schema2 is appendix diagnostic only.",
    )
    parser.add_argument(
        "--benchmark-input",
        type=Path,
        default=None,
        help="Optional override benchmark JSON. Overrides are not labeled canonical; schema2 is appendix diagnostic only.",
    )
    parser.add_argument(
        "--fixed-impedance-input",
        type=Path,
        default=None,
        help="Optional stable fixed-impedance supplement JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/main_benchmark"),
        help="Directory for the exported table files.",
    )
    parser.add_argument(
        "--statistics-report-input",
        type=Path,
        default=None,
        help="Optional override statistics report JSON. Defaults to the manifest canonical statistics report.",
    )
    parser.add_argument(
        "--stem",
        type=str,
        default="table_3dof_paper_benchmark_stage4_20260429",
        help="Canonical output filename stem.",
    )
    parser.add_argument(
        "--latex-output",
        type=Path,
        default=Path("paper/generated/main_benchmark_table.tex"),
        help="Path for the generated LaTeX tabular include.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Generate in a temporary directory and fail if checked-in outputs would change.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def _load_manifest(path: Path) -> dict:
    manifest_path = path if path.is_absolute() else _repo_root() / path
    registry = _load_artifact_registry_module()
    return registry.load_manifest(manifest_path, repo_root=_repo_root())


def resolve_export_inputs(args: argparse.Namespace) -> ExportInputs:
    if args.benchmark_input is not None:
        benchmark_input = args.benchmark_input
        statistics_report_input = args.statistics_report_input
        provenance_label = "override_benchmark_input"
        generating_command = "python scripts/export/export_paper_only_sim_benchmark_table.py --benchmark-input <override>"
        git_commit = None
    else:
        manifest = _load_manifest(args.manifest)
        canonical_benchmark = manifest["artifacts"]["canonical_main_benchmark"]
        canonical_statistics = manifest["artifacts"]["canonical_statistics_report"]
        benchmark_input = Path(canonical_benchmark["path"])
        statistics_report_input = (
            Path(canonical_statistics["path"])
            if args.statistics_report_input is None
            else args.statistics_report_input
        )
        provenance_label = "canonical_main_benchmark"
        generating_command = (
            "python scripts/export/export_paper_only_sim_benchmark_table.py "
            "--manifest artifacts/main_benchmark/main_benchmark_manifest.json"
        )
        git_commit = canonical_benchmark["git_commit"]
    return ExportInputs(
        benchmark_input=benchmark_input,
        statistics_report_input=statistics_report_input,
        provenance_label=provenance_label,
        generating_command=generating_command,
        git_commit=git_commit,
    )


def _diff_text_files(expected_path: Path, generated_path: Path) -> list[str]:
    if not expected_path.exists():
        return [f"Missing checked-in output: {expected_path}"]
    expected = expected_path.read_text(encoding="utf-8").splitlines(keepends=True)
    generated = generated_path.read_text(encoding="utf-8").splitlines(keepends=True)
    if expected == generated:
        return []
    return list(
        difflib.unified_diff(
            expected,
            generated,
            fromfile=str(expected_path),
            tofile=str(generated_path),
            n=3,
        )
    )


def _diff_outputs(expected_dir: Path, generated_dir: Path, stem: str) -> str:
    messages: list[str] = []
    for suffix in (".json", ".md", ".csv"):
        expected_path = expected_dir / f"{stem}{suffix}"
        generated_path = generated_dir / f"{stem}{suffix}"
        messages.extend(_diff_text_files(expected_path, generated_path))
    return "".join(messages)


def run_check(args: argparse.Namespace) -> None:
    module = _load_paper_tables_module()
    inputs = resolve_export_inputs(args)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_latex_path = Path(tmp_dir) / args.latex_output.name
        module.export_3dof_paper_table(
            benchmark_report_path=inputs.benchmark_input,
            fixed_impedance_report_path=args.fixed_impedance_input,
            statistics_report_path=inputs.statistics_report_input,
            output_dir=Path(tmp_dir),
            stem=args.stem,
            source_role=inputs.provenance_label,
            generating_command=inputs.generating_command,
            git_commit=inputs.git_commit,
            latex_output_path=tmp_latex_path,
        )
        diff = _diff_outputs(args.output_dir, Path(tmp_dir), args.stem)
        diff += "".join(_diff_text_files(args.latex_output, tmp_latex_path))
    if diff:
        raise SystemExit("Benchmark table outputs are stale:\n" + diff)


def main() -> None:
    args = parse_args()
    if args.check:
        run_check(args)
        return
    module = _load_paper_tables_module()
    inputs = resolve_export_inputs(args)
    json_path, markdown_path = module.export_3dof_paper_table(
        benchmark_report_path=inputs.benchmark_input,
        fixed_impedance_report_path=args.fixed_impedance_input,
        statistics_report_path=inputs.statistics_report_input,
        output_dir=args.output_dir,
        stem=args.stem,
        source_role=inputs.provenance_label,
        generating_command=inputs.generating_command,
        git_commit=inputs.git_commit,
        latex_output_path=args.latex_output,
    )
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()
