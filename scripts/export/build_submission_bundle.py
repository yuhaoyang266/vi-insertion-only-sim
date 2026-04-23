from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.submission_bundle import build_submission_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an anonymized submission bundle from the current repository.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tmp/submission_bundle/journal_double_blind"),
    )
    parser.add_argument(
        "--venue",
        default="journal-double-blind",
        help="Label recorded in the bundle manifest.",
    )
    parser.add_argument(
        "--paper-pdf",
        type=Path,
        default=None,
        help="Optional anonymous manuscript PDF to include alongside the bundle. Must live outside --output-dir.",
    )
    parser.add_argument(
        "--skip-archives",
        action="store_true",
        help="Skip zip archive generation and keep only the unpacked directories.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifacts = build_submission_bundle(
        source_root=REPO_ROOT,
        output_dir=args.output_dir,
        venue=args.venue,
        paper_pdf=args.paper_pdf,
        create_archives=not args.skip_archives,
    )
    print("submission_bundle")
    print("anonymous_snapshot_dir", artifacts["anonymous_snapshot_dir"])
    print("editor_materials_dir", artifacts["editor_materials_dir"])
    print("manifest_path", artifacts["manifest_path"])
    print("summary_path", artifacts["summary_path"])
    print("paper_pdf_path", artifacts["paper_pdf_path"])
    print("anonymous_snapshot_zip", artifacts["anonymous_snapshot_zip"])
    print("editor_materials_zip", artifacts["editor_materials_zip"])


if __name__ == "__main__":
    main()
