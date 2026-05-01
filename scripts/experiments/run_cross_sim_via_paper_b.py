from __future__ import annotations

import argparse
from datetime import datetime
import subprocess
from pathlib import Path
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.cross_paper_bridge import (
    CONTRACT_RELATIVE_PATH,
    CONTRACT_SHA,
    PAPER_A_POLICY_SUITE_NAMES,
    assert_contract_sha_current,
    build_policy_stub,
    compute_contract_sha,
    map_paper_a_action_to_paper_b,
    project_paper_b_observation_to_paper_a,
)
from vi_full.cross_sim_ranking import build_cross_sim_ranking, write_cross_sim_ranking_artifacts
from vi_full.three_dof_profiles import DEFAULT_UNCERTAINTY_PROFILES


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Paper-A to Paper-B cross-sim bridge smoke."
    )
    parser.add_argument("--paper-b-repo-path", type=Path, required=True)
    parser.add_argument("--paper-b-commit", type=str, default=None)
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=list(DEFAULT_UNCERTAINTY_PROFILES),
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0])
    parser.add_argument("--episodes-per-seed", type=int, default=5)
    parser.add_argument(
        "--suites",
        type=str,
        nargs="+",
        default=list(PAPER_A_POLICY_SUITE_NAMES),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write a contract-level smoke artifact without running Paper-B physics.",
    )
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def _default_output_path() -> Path:
    date_stamp = datetime.now().strftime("%Y%m%d")
    return Path("outputs") / "cross_sim" / f"three_dof_cross_sim_ranking_paper_b_{date_stamp}.json"


def _git_commit(repo_path: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip()


def _validate_paper_b_contract(paper_b_repo_path: Path) -> str:
    contract_path = paper_b_repo_path / CONTRACT_RELATIVE_PATH
    if not contract_path.exists():
        raise FileNotFoundError(f"Paper-B contract not found: {contract_path}")
    paper_b_contract_sha = compute_contract_sha(contract_path)
    if paper_b_contract_sha != CONTRACT_SHA:
        raise RuntimeError(
            "Paper-B contract SHA mismatch: "
            f"expected {CONTRACT_SHA}, got {paper_b_contract_sha}"
        )
    return paper_b_contract_sha


def _translation_smoke() -> dict[str, Any]:
    mapped_action = map_paper_a_action_to_paper_b(np.zeros(5, dtype=np.float64))
    projected = project_paper_b_observation_to_paper_a(
        {
            "ee_pos": np.zeros(3, dtype=np.float64),
            "ee_twist": np.zeros(6, dtype=np.float64),
            "wrench": np.zeros(6, dtype=np.float64),
            "contact_count": 0,
            "contact_state": "free_space",
        },
        hole_origin_world=np.zeros(3, dtype=np.float64),
        previous_schema_p_action=mapped_action.schema_p_action,
    )
    return {
        "schema_p_action": mapped_action.schema_p_action.tolist(),
        "env_action_keys": sorted(mapped_action.env_action.keys()),
        "observation_shape": list(projected.observation.shape),
        "out_of_paper_a_scope": projected.out_of_paper_a_scope,
    }


def _dry_run_records(
    *,
    suites: list[str],
    profiles: list[str],
    seeds: list[int],
    episodes_per_seed: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for suite_name in suites:
        build_policy_stub(suite_name)
        for profile in profiles:
            for seed in seeds:
                records.append(
                    {
                        "suite_name": suite_name,
                        "profile": profile,
                        "seed": int(seed),
                        "episode_count": int(episodes_per_seed),
                        "status": "not_available",
                        "reason": "Paper-A policy artifact loader is not implemented.",
                    }
                )
    return records


def _metadata(args: argparse.Namespace, paper_b_contract_sha: str, paper_b_commit: str) -> dict[str, Any]:
    return {
        "contract_sha": CONTRACT_SHA,
        "paper_b_contract_sha": paper_b_contract_sha,
        "paper_a_commit": _git_commit(REPO_ROOT),
        "paper_b_commit": paper_b_commit,
        "paper_b_repo_path": args.paper_b_repo_path,
        "dry_run": bool(args.dry_run),
        "profiles": list(args.profiles),
        "seeds": [int(seed) for seed in args.seeds],
        "episodes_per_seed": int(args.episodes_per_seed),
        "suites": list(args.suites),
        "translation_smoke": _translation_smoke(),
    }


def main() -> None:
    args = _parse_args()
    assert_contract_sha_current()
    paper_b_repo_path = args.paper_b_repo_path.resolve()
    if not paper_b_repo_path.exists():
        raise FileNotFoundError(f"Paper-B repo path does not exist: {paper_b_repo_path}")
    paper_b_contract_sha = _validate_paper_b_contract(paper_b_repo_path)
    paper_b_commit = args.paper_b_commit or _git_commit(paper_b_repo_path)
    if not args.dry_run:
        raise RuntimeError(
            "Paper-B physics execution is not implemented yet; use --dry-run for contract smoke."
        )
    records = _dry_run_records(
        suites=list(args.suites),
        profiles=list(args.profiles),
        seeds=[int(seed) for seed in args.seeds],
        episodes_per_seed=int(args.episodes_per_seed),
    )
    output_path = args.output if args.output is not None else _default_output_path()
    ranking = build_cross_sim_ranking(
        records,
        metadata=_metadata(args, paper_b_contract_sha, paper_b_commit),
    )
    paths = write_cross_sim_ranking_artifacts(output_path, ranking)
    print(f"cross_sim_ranking_json {paths['json']}", flush=True)
    print(f"cross_sim_ranking_csv {paths['csv']}", flush=True)
    print(f"cross_sim_ranking_md {paths['markdown']}", flush=True)


if __name__ == "__main__":
    main()
