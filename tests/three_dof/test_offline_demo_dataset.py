from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from vi_full.cross_paper_bridge import CONTRACT_SHA
from vi_full.modern_baseline_smoke import validate_offline_dataset_schema
from vi_full.offline_demo_dataset import (
    OFFLINE_DEMO_DATASET_ARTIFACT_TYPE,
    NearestNeighborOfflinePolicy,
    build_offline_demo_dataset,
    compute_dataset_payload_sha256,
    flatten_offline_dataset_arrays,
    write_offline_demo_dataset_artifact,
)


def test_offline_demo_dataset_exports_contract_shaped_episodes() -> None:
    dataset = build_offline_demo_dataset(
        profiles=["nominal"],
        seeds=[0],
        episodes_per_seed=1,
        source_policy="variable_impedance",
        paper_a_commit="test_commit",
        generation_command="python export_3dof_offline_demo_dataset.py",
    )

    assert dataset["artifact_type"] == OFFLINE_DEMO_DATASET_ARTIFACT_TYPE
    assert dataset["metadata"]["contract_sha"] == CONTRACT_SHA
    assert dataset["metadata"]["dataset_payload_sha256"] == compute_dataset_payload_sha256(dataset)
    assert dataset["metadata"]["generation_command"].startswith("python")
    assert len(dataset["episodes"]) == 1

    summary = validate_offline_dataset_schema(dataset)
    observations, actions = flatten_offline_dataset_arrays(dataset)
    policy = NearestNeighborOfflinePolicy(observations=observations, actions=actions)

    assert summary["episode_count"] == 1
    assert summary["observation_shape"][1] == 14
    assert summary["action_shape"][1] == 5
    assert policy.act(np.zeros(14, dtype=np.float32)).shape == (5,)


def test_offline_demo_dataset_writes_json_artifact(tmp_path: Path) -> None:
    dataset = build_offline_demo_dataset(
        profiles=["nominal"],
        seeds=[0],
        episodes_per_seed=1,
        paper_a_commit="test_commit",
    )

    paths = write_offline_demo_dataset_artifact(tmp_path / "offline_dataset.json", dataset)
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))

    assert set(paths) == {"json"}
    assert payload["artifact_type"] == OFFLINE_DEMO_DATASET_ARTIFACT_TYPE
    assert payload["metadata"]["dataset_payload_sha256"] == dataset["metadata"][
        "dataset_payload_sha256"
    ]


def test_committed_offline_demo_dataset_artifact_is_canonical() -> None:
    artifact_path = (
        Path(__file__).resolve().parents[2]
        / "artifacts"
        / "main_benchmark"
        / "three_dof_offline_demo_dataset_20260501.json"
    )

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert payload["artifact_type"] == OFFLINE_DEMO_DATASET_ARTIFACT_TYPE
    assert payload["metadata"]["profiles"] == [
        "nominal",
        "tight_clearance",
        "high_friction",
        "offset_bias",
        "noisy_force",
    ]
    assert payload["metadata"]["seeds"] == [0, 1, 2]
    assert payload["metadata"]["episodes_per_seed"] == 2
    assert payload["metadata"]["dataset_payload_sha256"] == compute_dataset_payload_sha256(payload)
    assert validate_offline_dataset_schema(payload)["episode_count"] == 30
