from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_contact_parameter_sensitivity import (
    DEFAULT_LEVEL_NAMES,
    DEFAULT_PARAMETER_NAMES,
    run_contact_parameter_sensitivity,
    write_contact_parameter_sensitivity_artifacts,
)
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_profiles import DEFAULT_UNCERTAINTY_PROFILES


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a 3DoF contact-parameter sensitivity sweep."
    )
    parser.add_argument("--profiles", type=str, nargs="+", default=list(DEFAULT_UNCERTAINTY_PROFILES))
    parser.add_argument("--seeds", type=int, nargs="+", default=[0])
    parser.add_argument("--episodes-per-seed", type=int, default=1)
    parser.add_argument(
        "--policies",
        type=str,
        nargs="+",
        default=["fixed_impedance", "variable_impedance"],
    )
    parser.add_argument("--parameters", type=str, nargs="+", default=list(DEFAULT_PARAMETER_NAMES))
    parser.add_argument("--levels", type=str, nargs="+", default=list(DEFAULT_LEVEL_NAMES))
    parser.add_argument(
        "--max-episode-steps",
        type=int,
        default=DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    )
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def _default_output_path() -> Path:
    date_stamp = datetime.now().strftime("%Y%m%d")
    return Path("outputs") / "revision" / f"contact_parameter_sensitivity_{date_stamp}.json"


def main() -> None:
    args = _parse_args()
    report = run_contact_parameter_sensitivity(
        profiles=list(args.profiles),
        seeds=[int(seed) for seed in args.seeds],
        episodes_per_seed=int(args.episodes_per_seed),
        policy_names=list(args.policies),
        parameter_names=list(args.parameters),
        level_names=list(args.levels),
        max_episode_steps=int(args.max_episode_steps),
    )
    output_path = args.output if args.output is not None else _default_output_path()
    paths = write_contact_parameter_sensitivity_artifacts(output_path, report)
    print(f"contact_parameter_sensitivity_json {paths['json']}", flush=True)
    print(f"contact_parameter_sensitivity_csv {paths['csv']}", flush=True)
    print(f"contact_parameter_sensitivity_md {paths['markdown']}", flush=True)


if __name__ == "__main__":
    main()
