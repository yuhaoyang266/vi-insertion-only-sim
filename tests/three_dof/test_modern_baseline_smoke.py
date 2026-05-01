from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from vi_full.cross_paper_bridge import CONTRACT_SHA
from vi_full.modern_baseline_smoke import (
    MODERN_BASELINE_DECISION,
    build_synthetic_offline_dataset,
    load_offline_dataset_json,
    run_modern_baseline_smoke,
    validate_offline_dataset_schema,
    write_modern_baseline_smoke_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_modern_baseline_decision_prefers_iql_offline() -> None:
    assert MODERN_BASELINE_DECISION["chosen"] == "iql_offline"
    assert "cql_offline" in MODERN_BASELINE_DECISION["compatible_fallbacks"]


def test_offline_dataset_schema_requires_14d_observations_and_5d_actions() -> None:
    dataset = build_synthetic_offline_dataset(num_steps=4)

    summary = validate_offline_dataset_schema(dataset)

    assert summary["observation_shape"] == [4, 14]
    assert summary["action_shape"] == [4, 5]
    assert summary["profile_count"] == 1

    bad_dataset = [dict(dataset[0])]
    bad_dataset[0]["actions"] = np.zeros((4, 4), dtype=np.float32)
    with pytest.raises(ValueError, match="actions"):
        validate_offline_dataset_schema(bad_dataset)


def test_offline_dataset_schema_requires_contract_episode_metadata() -> None:
    dataset = build_synthetic_offline_dataset(num_steps=4)
    bad_dataset = [dict(dataset[0])]
    bad_dataset[0].pop("termination_reason")

    with pytest.raises(ValueError, match="termination_reason"):
        validate_offline_dataset_schema(bad_dataset)


def test_offline_dataset_schema_requires_current_contract_and_profile() -> None:
    dataset = build_synthetic_offline_dataset(num_steps=4)

    bad_profile = [dict(dataset[0])]
    bad_profile[0]["profile"] = "invalid_profile"
    with pytest.raises(ValueError, match="profile"):
        validate_offline_dataset_schema(bad_profile)

    bad_contract = [dict(dataset[0])]
    bad_contract[0]["contract_sha"] = "old"
    with pytest.raises(ValueError, match="contract_sha"):
        validate_offline_dataset_schema(bad_contract)


def test_offline_dataset_schema_requires_typed_nonempty_episode_metadata() -> None:
    dataset = build_synthetic_offline_dataset(num_steps=4)

    bad_seed = [dict(dataset[0])]
    bad_seed[0]["seed"] = 0.5
    with pytest.raises(ValueError, match="seed"):
        validate_offline_dataset_schema(bad_seed)

    bad_success = [dict(dataset[0])]
    bad_success[0]["success"] = "false"
    with pytest.raises(ValueError, match="success"):
        validate_offline_dataset_schema(bad_success)

    bad_reason = [dict(dataset[0])]
    bad_reason[0]["termination_reason"] = ""
    with pytest.raises(ValueError, match="termination_reason"):
        validate_offline_dataset_schema(bad_reason)

    bad_commit = [dict(dataset[0])]
    bad_commit[0]["paper_a_commit"] = ""
    with pytest.raises(ValueError, match="paper_a_commit"):
        validate_offline_dataset_schema(bad_commit)


def test_modern_baseline_smoke_reports_scaffold_status() -> None:
    report = run_modern_baseline_smoke(num_steps=4)

    assert report["artifact_type"] == "modern_baseline_smoke"
    assert report["algorithm"] == "iql_offline"
    assert report["status"] == "scaffold_only"
    assert report["dataset_source"] == "synthetic_schema_smoke"
    assert report["dataset_summary"]["observation_shape"] == [4, 14]
    assert "episode_id" in report["dataset_summary"]["required_episode_keys"]


def test_modern_baseline_smoke_can_ingest_json_dataset(tmp_path: Path) -> None:
    dataset = build_synthetic_offline_dataset(num_steps=4)
    json_dataset = [
        {
            key: value.tolist() if hasattr(value, "tolist") else value
            for key, value in dataset[0].items()
        }
    ]
    dataset_path = tmp_path / "offline_dataset.json"
    dataset_path.write_text(json.dumps(json_dataset), encoding="utf-8")

    loaded = load_offline_dataset_json(dataset_path)
    report = run_modern_baseline_smoke(dataset_path=dataset_path)

    assert loaded[0]["episode_id"] == "synthetic_schema_smoke_0000"
    assert report["status"] == "dataset_schema_verified"
    assert report["dataset_source"] == "external_json_dataset:offline_dataset.json"
    assert str(tmp_path) not in report["dataset_source"]
    assert report["dataset_summary"]["sample_count"] == 4
    assert "real Paper-A offline demonstration artifact path" not in report["blocked_on"]


def test_modern_baseline_smoke_writes_artifacts(tmp_path: Path) -> None:
    report = run_modern_baseline_smoke(num_steps=4)

    paths = write_modern_baseline_smoke_artifacts(tmp_path / "modern_baseline.json", report)

    assert set(paths) == {"json", "markdown"}
    assert json.loads(paths["json"].read_text(encoding="utf-8"))["algorithm"] == "iql_offline"
    assert "iql_offline" in paths["markdown"].read_text(encoding="utf-8")


def test_committed_modern_baseline_artifact_uses_current_contract_sha() -> None:
    artifact_path = REPO_ROOT / "outputs" / "revision" / "modern_baseline_iql_smoke_20260501.json"

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert payload["status"] == "scaffold_only"
    assert payload["dataset_summary"]["contract_sha"] == CONTRACT_SHA
