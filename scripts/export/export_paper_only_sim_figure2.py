from __future__ import annotations

import argparse
import filecmp
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


def _load_paper_figures_module():
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    module_path = src_root / "vi_full" / "paper_figures.py"
    spec = importlib.util.spec_from_file_location("paper_figures_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load paper figure module from {module_path}")
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
    parser = argparse.ArgumentParser(description="Export only-sim Figure 2 assets.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Canonical benchmark manifest. Defaults to the stage3 main benchmark; schema2 is appendix diagnostic only.",
    )
    parser.add_argument(
        "--benchmark-input",
        type=Path,
        default=None,
        help="Optional override benchmark JSON. Overrides are not labeled canonical; schema2 is appendix diagnostic only.",
    )
    parser.add_argument(
        "--statistics-report-input",
        type=Path,
        default=None,
        help="Optional override statistics report. Defaults to the manifest canonical statistics report.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("figures/main"),
        help="Directory for the exported figure files.",
    )
    parser.add_argument(
        "--stem",
        type=str,
        default="fig2_main_benchmark_evaluation_class_summary",
        help="Canonical output filename stem.",
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
    manifest = _load_manifest(args.manifest)
    canonical_benchmark = manifest["artifacts"]["canonical_main_benchmark"]
    canonical_statistics = manifest["artifacts"]["canonical_statistics_report"]
    if args.benchmark_input is None:
        benchmark_input = Path(canonical_benchmark["path"])
        statistics_report_input = (
            Path(canonical_statistics["path"])
            if args.statistics_report_input is None
            else args.statistics_report_input
        )
        provenance_label = "canonical_main_benchmark"
    else:
        benchmark_input = args.benchmark_input
        statistics_report_input = args.statistics_report_input
        provenance_label = "override_benchmark_input"
    return ExportInputs(
        benchmark_input=benchmark_input,
        statistics_report_input=statistics_report_input,
        provenance_label=provenance_label,
    )


def run_check(args: argparse.Namespace) -> None:
    module = _load_paper_figures_module()
    inputs = resolve_export_inputs(args)
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path, png_path = module.export_figure2_main_benchmark_pressure_class_summary(
            benchmark_report_path=inputs.benchmark_input,
            statistics_report_path=inputs.statistics_report_input,
            output_dir=Path(tmp_dir),
            stem=args.stem,
        )
        generated_paths = {".pdf": pdf_path, ".png": png_path}
        stale: list[str] = []
        for suffix, generated_path in generated_paths.items():
            expected_path = args.output_dir / f"{args.stem}{suffix}"
            if not expected_path.exists():
                stale.append(f"Missing checked-in output: {expected_path}")
            elif not filecmp.cmp(expected_path, generated_path, shallow=False):
                stale.append(f"Output differs: {expected_path}")
    if stale:
        raise SystemExit("Figure 2 outputs are stale:\n" + "\n".join(stale))


def main() -> None:
    args = parse_args()
    if args.check:
        run_check(args)
        return
    module = _load_paper_figures_module()
    inputs = resolve_export_inputs(args)
    pdf_path, png_path = module.export_figure2_main_benchmark_pressure_class_summary(
        benchmark_report_path=inputs.benchmark_input,
        statistics_report_path=inputs.statistics_report_input,
        output_dir=args.output_dir,
        stem=args.stem,
    )
    print(pdf_path)
    print(png_path)


if __name__ == "__main__":
    main()
