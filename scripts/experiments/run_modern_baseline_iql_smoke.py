from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.modern_baseline_smoke import (
    run_modern_baseline_smoke,
    write_modern_baseline_smoke_artifacts,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the modern IQL/CQL baseline smoke scaffold."
    )
    parser.add_argument("--num-steps", type=int, default=8)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def _default_output_path() -> Path:
    date_stamp = datetime.now().strftime("%Y%m%d")
    return Path("outputs") / "revision" / f"modern_baseline_iql_smoke_{date_stamp}.json"


def main() -> None:
    args = _parse_args()
    report = run_modern_baseline_smoke(num_steps=int(args.num_steps))
    output_path = args.output if args.output is not None else _default_output_path()
    paths = write_modern_baseline_smoke_artifacts(output_path, report)
    print(f"modern_baseline_smoke_json {paths['json']}", flush=True)
    print(f"modern_baseline_smoke_md {paths['markdown']}", flush=True)


if __name__ == "__main__":
    main()
