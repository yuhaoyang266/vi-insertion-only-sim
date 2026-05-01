from __future__ import annotations

import hashlib
import json
from numbers import Integral
from pathlib import Path
from typing import Any

import numpy as np

from vi_full.cross_paper_bridge import CONTRACT_SHA
from vi_full.three_dof_profiles import DEFAULT_UNCERTAINTY_PROFILES


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_EPISODE_RECORD_KEYS = (
    "observations",
    "actions",
    "rewards",
    "episode_id",
    "profile",
    "seed",
    "success",
    "termination_reason",
    "source_policy",
    "paper_a_commit",
    "contract_sha",
)

MODERN_BASELINE_DECISION = {
    "chosen": "iql_offline",
    "compatible_fallbacks": ["cql_offline", "diffusion_policy_lerobot", "act_state_based"],
    "rationale": (
        "IQL/CQL can consume the existing Paper-A 14D observation and 5D action offline "
        "dataset contract without introducing vision, hardware, or action-space scope."
    ),
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def build_synthetic_offline_dataset(*, num_steps: int = 8) -> list[dict[str, Any]]:
    if num_steps <= 0:
        raise ValueError("num_steps must be positive.")
    observations = np.zeros((num_steps, 14), dtype=np.float32)
    actions = np.zeros((num_steps, 5), dtype=np.float32)
    rewards = np.zeros((num_steps,), dtype=np.float32)
    observations[:, 0] = np.linspace(0.003, 0.0, num_steps, dtype=np.float32)
    observations[:, 2] = np.linspace(0.006, 0.0, num_steps, dtype=np.float32)
    actions[:, 2] = -0.25
    actions[:, 3] = 0.5
    actions[:, 4] = 0.6
    rewards[-1] = 1.0
    return [
        {
            "observations": observations,
            "actions": actions,
            "rewards": rewards,
            "episode_id": "synthetic_schema_smoke_0000",
            "profile": "nominal",
            "seed": 0,
            "success": True,
            "termination_reason": "synthetic_success",
            "source_policy": "synthetic_schema_smoke",
            "paper_a_commit": "synthetic_schema_smoke",
            "contract_sha": CONTRACT_SHA,
        }
    ]


def load_offline_dataset_json(dataset_path: Path) -> Any:
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"offline dataset does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def compute_dataset_sha256(dataset_path: Path) -> str:
    return hashlib.sha256(Path(dataset_path).read_bytes()).hexdigest()


def _dataset_source_label(dataset_path: Path) -> str:
    path = Path(dataset_path)
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return f"external_json_dataset:{path.name}"


def _as_array(dataset: dict[str, Any], name: str, shape_tail: tuple[int, ...]) -> np.ndarray:
    if name not in dataset:
        raise ValueError(f"dataset is missing {name}")
    array = np.asarray(dataset[name], dtype=np.float32)
    if array.ndim != 1 + len(shape_tail) or tuple(array.shape[1:]) != shape_tail:
        raise ValueError(f"{name} must have shape [N, {', '.join(map(str, shape_tail))}]")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def _episode_records(dataset: Any) -> list[dict[str, Any]]:
    if isinstance(dataset, dict) and "episodes" in dataset:
        records = dataset["episodes"]
    elif isinstance(dataset, dict):
        records = [dataset]
    else:
        records = dataset
    if not isinstance(records, (list, tuple)) or not records:
        raise ValueError("dataset must contain at least one episode record")
    return [dict(record) for record in records]


def _validate_episode_record(record: dict[str, Any]) -> dict[str, Any]:
    missing_keys = [key for key in REQUIRED_EPISODE_RECORD_KEYS if key not in record]
    if missing_keys:
        raise ValueError(f"episode record is missing required keys: {missing_keys}")
    observations = _as_array(record, "observations", (14,))
    actions = _as_array(record, "actions", (5,))
    rewards = _as_array(record, "rewards", ())
    if len(observations) != len(actions) or len(observations) != len(rewards):
        raise ValueError("observations, actions, and rewards must have matching first dimension")
    if not str(record["episode_id"]):
        raise ValueError("episode_id must not be empty")
    profile = str(record["profile"])
    if profile not in DEFAULT_UNCERTAINTY_PROFILES:
        raise ValueError(f"profile must be one of {list(DEFAULT_UNCERTAINTY_PROFILES)}")
    seed = record["seed"]
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    success = record["success"]
    if not isinstance(success, bool):
        raise ValueError("success must be a boolean")
    termination_reason = str(record["termination_reason"])
    if not termination_reason:
        raise ValueError("termination_reason must not be empty")
    if not str(record["source_policy"]):
        raise ValueError("source_policy must not be empty")
    paper_a_commit = str(record["paper_a_commit"])
    if not paper_a_commit:
        raise ValueError("paper_a_commit must not be empty")
    contract_sha = str(record["contract_sha"])
    if contract_sha != CONTRACT_SHA:
        raise ValueError(f"contract_sha must match current contract SHA {CONTRACT_SHA}")
    return {
        "observation_shape": list(observations.shape),
        "action_shape": list(actions.shape),
        "reward_shape": list(rewards.shape),
        "sample_count": int(len(observations)),
        "profile": profile,
        "seed": int(seed),
        "success": success,
        "termination_reason": termination_reason,
        "source_policy": str(record["source_policy"]),
        "paper_a_commit": paper_a_commit,
        "contract_sha": contract_sha,
    }


def validate_offline_dataset_schema(dataset: Any) -> dict[str, Any]:
    episode_summaries = [_validate_episode_record(record) for record in _episode_records(dataset)]
    sample_count = int(sum(summary["sample_count"] for summary in episode_summaries))
    profiles = [summary["profile"] for summary in episode_summaries]
    contract_shas = sorted({summary["contract_sha"] for summary in episode_summaries})
    return {
        "episode_count": len(episode_summaries),
        "profile_count": len(set(profiles)),
        "sample_count": sample_count,
        "required_episode_keys": list(REQUIRED_EPISODE_RECORD_KEYS),
        "observation_shape": episode_summaries[0]["observation_shape"],
        "action_shape": episode_summaries[0]["action_shape"],
        "reward_shape": episode_summaries[0]["reward_shape"],
        "profiles": sorted(set(profiles)),
        "contract_sha": contract_shas[0] if len(contract_shas) == 1 else "mixed",
    }


def run_modern_baseline_smoke(
    *,
    num_steps: int = 8,
    dataset_path: Path | None = None,
) -> dict[str, Any]:
    if dataset_path is None:
        dataset = build_synthetic_offline_dataset(num_steps=num_steps)
        status = "scaffold_only"
        dataset_source = "synthetic_schema_smoke"
        dataset_sha256 = None
        dataset_size_bytes = None
        blocked_on = [
            "real Paper-A offline demonstration artifact path",
            "IQL/CQL training dependency and hyperparameter file",
            "comparison protocol against existing five-suite benchmark rows",
        ]
    else:
        resolved_dataset_path = Path(dataset_path)
        dataset = load_offline_dataset_json(resolved_dataset_path)
        status = "dataset_schema_verified"
        dataset_source = _dataset_source_label(resolved_dataset_path)
        dataset_sha256 = compute_dataset_sha256(resolved_dataset_path)
        dataset_size_bytes = int(resolved_dataset_path.stat().st_size)
        blocked_on = [
            "IQL/CQL training dependency and hyperparameter file",
            "comparison protocol against existing five-suite benchmark rows",
        ]
    dataset_summary = validate_offline_dataset_schema(dataset)
    return {
        "artifact_type": "modern_baseline_smoke",
        "schema_version": 1,
        "algorithm": MODERN_BASELINE_DECISION["chosen"],
        "status": status,
        "decision": dict(MODERN_BASELINE_DECISION),
        "dataset_source": dataset_source,
        "dataset_sha256": dataset_sha256,
        "dataset_size_bytes": dataset_size_bytes,
        "dataset_summary": dataset_summary,
        "blocked_on": blocked_on,
    }


def render_modern_baseline_smoke_markdown(report: dict[str, Any]) -> str:
    summary = report["dataset_summary"]
    dataset_sha256 = "null" if report["dataset_sha256"] is None else report["dataset_sha256"]
    dataset_size_bytes = (
        "null" if report["dataset_size_bytes"] is None else report["dataset_size_bytes"]
    )
    lines = [
        "# Modern Baseline Smoke",
        "",
        f"- algorithm: {report['algorithm']}",
        f"- status: {report['status']}",
        f"- dataset_source: {report['dataset_source']}",
        f"- dataset_sha256: {dataset_sha256}",
        f"- dataset_size_bytes: {dataset_size_bytes}",
        f"- observation_shape: {summary['observation_shape']}",
        f"- action_shape: {summary['action_shape']}",
        f"- sample_count: {summary['sample_count']}",
        "",
        "## Blocked On",
        "",
    ]
    lines.extend(f"- {item}" for item in report["blocked_on"])
    lines.append("")
    return "\n".join(lines)


def write_modern_baseline_smoke_artifacts(
    output_path: Path,
    report: dict[str, Any],
) -> dict[str, Path]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_path
    markdown_path = output_path.with_suffix(".md")
    json_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")
    markdown_path.write_text(render_modern_baseline_smoke_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
