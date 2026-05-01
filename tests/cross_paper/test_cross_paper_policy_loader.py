from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from vi_full.cross_paper_policy_loader import (
    EXPECTED_ACTION_SHAPE,
    EXPECTED_OBSERVATION_SHAPE,
    PolicyArtifactUnavailable,
    load_paper_a_policy_artifact,
)


def _write_stub_policy(path: Path, **overrides) -> None:
    payload = {
        "schema_version": 1,
        "suite_name": "repaired_mainline_bc_to_ppo",
        "observation_shape": list(EXPECTED_OBSERVATION_SHAPE),
        "action_shape": list(EXPECTED_ACTION_SHAPE),
        "normalization_state": {"type": "identity"},
        "constant_action": [0.0, 0.0, -0.25, 0.5, 0.75],
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_policy_loader_reports_unavailable_artifacts(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing_policy.json"

    with pytest.raises(PolicyArtifactUnavailable, match="does not exist"):
        load_paper_a_policy_artifact(
            suite_name="repaired_mainline_bc_to_ppo",
            artifact_path=missing_path,
        )

    with pytest.raises(PolicyArtifactUnavailable, match="not available"):
        load_paper_a_policy_artifact(
            suite_name="repaired_mainline_bc_to_ppo",
            artifact_path="not_available",
        )


def test_policy_loader_rejects_invalid_stub_contract(tmp_path: Path) -> None:
    policy_path = tmp_path / "bad_policy.json"
    _write_stub_policy(policy_path, observation_shape=[13])

    with pytest.raises(ValueError, match="observation_shape"):
        load_paper_a_policy_artifact(
            suite_name="repaired_mainline_bc_to_ppo",
            artifact_path=policy_path,
        )


def test_policy_loader_loads_valid_stub_and_validates_observation(tmp_path: Path) -> None:
    policy_path = tmp_path / "stub_policy.json"
    _write_stub_policy(policy_path)

    loaded_policy = load_paper_a_policy_artifact(
        suite_name="repaired_mainline_bc_to_ppo",
        artifact_path=policy_path,
    )

    assert loaded_policy.status == "loaded"
    assert loaded_policy.contract.suite_name == "repaired_mainline_bc_to_ppo"
    assert loaded_policy.contract.artifact_path == policy_path
    assert loaded_policy.contract.normalization_state == {"type": "identity"}
    np.testing.assert_allclose(
        loaded_policy.act(np.zeros(EXPECTED_OBSERVATION_SHAPE, dtype=np.float32)),
        [0.0, 0.0, -0.25, 0.5, 0.75],
    )
    with pytest.raises(ValueError, match="observation"):
        loaded_policy.act(np.zeros((1, 14), dtype=np.float32))
