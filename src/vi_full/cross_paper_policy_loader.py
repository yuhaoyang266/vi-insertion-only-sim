from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np

from vi_full.cross_paper_bridge import (
    PAPER_A_ACTION_HIGH,
    PAPER_A_ACTION_LOW,
    PAPER_A_POLICY_SUITE_NAMES,
)


POLICY_ARTIFACT_SCHEMA_VERSION = 1
EXPECTED_OBSERVATION_SHAPE = (14,)
EXPECTED_ACTION_SHAPE = (5,)


class PolicyArtifactUnavailable(RuntimeError):
    """Raised when a requested Paper-A policy artifact is intentionally unavailable."""


@dataclass(frozen=True, slots=True)
class PaperAPolicyArtifactContract:
    suite_name: str
    artifact_path: Path
    observation_shape: tuple[int, ...]
    action_shape: tuple[int, ...]
    normalization_state: Any


@dataclass(frozen=True, slots=True)
class LoadedPaperAPolicy:
    contract: PaperAPolicyArtifactContract
    constant_action: np.ndarray
    status: str = "loaded"

    def act(self, observation: Any) -> np.ndarray:
        observation_vector = _as_vector(
            observation,
            name="observation",
            expected_shape=self.contract.observation_shape,
        )
        del observation_vector
        return np.clip(
            self.constant_action,
            PAPER_A_ACTION_LOW,
            PAPER_A_ACTION_HIGH,
        ).astype(np.float32)


def _as_shape(value: Any, *, name: str) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError(f"{name} must be a non-empty shape list.")
    shape = tuple(int(item) for item in value)
    if any(item <= 0 for item in shape):
        raise ValueError(f"{name} entries must be positive integers.")
    return shape


def _as_vector(value: Any, *, name: str, expected_shape: tuple[int, ...]) -> np.ndarray:
    vector = np.asarray(value, dtype=np.float32)
    if vector.shape != expected_shape:
        raise ValueError(f"{name} must have shape {expected_shape}, got {vector.shape}.")
    if not np.isfinite(vector).all():
        raise ValueError(f"{name} must contain only finite values.")
    return vector


def build_policy_artifact_contract(
    *,
    suite_name: str,
    artifact_path: Path,
    normalization_state: Any,
    observation_shape: tuple[int, ...] = EXPECTED_OBSERVATION_SHAPE,
    action_shape: tuple[int, ...] = EXPECTED_ACTION_SHAPE,
) -> PaperAPolicyArtifactContract:
    if suite_name not in PAPER_A_POLICY_SUITE_NAMES:
        raise ValueError(f"Unknown Paper-A policy suite: {suite_name}")
    if observation_shape != EXPECTED_OBSERVATION_SHAPE:
        raise ValueError(
            f"observation_shape must be {EXPECTED_OBSERVATION_SHAPE}, got {observation_shape}."
        )
    if action_shape != EXPECTED_ACTION_SHAPE:
        raise ValueError(f"action_shape must be {EXPECTED_ACTION_SHAPE}, got {action_shape}.")
    return PaperAPolicyArtifactContract(
        suite_name=suite_name,
        artifact_path=Path(artifact_path),
        observation_shape=observation_shape,
        action_shape=action_shape,
        normalization_state=normalization_state,
    )


def load_paper_a_policy_artifact(
    *,
    suite_name: str,
    artifact_path: Path | str | None,
) -> LoadedPaperAPolicy:
    if artifact_path is None or str(artifact_path) == "not_available":
        raise PolicyArtifactUnavailable(
            f"Paper-A policy artifact for suite {suite_name!r} is not available."
        )
    path = Path(artifact_path)
    if not path.exists():
        raise PolicyArtifactUnavailable(f"Paper-A policy artifact does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Policy artifact must be a JSON object.")
    if int(payload.get("schema_version", -1)) != POLICY_ARTIFACT_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {POLICY_ARTIFACT_SCHEMA_VERSION} for policy artifacts."
        )
    artifact_suite_name = str(payload.get("suite_name", ""))
    if artifact_suite_name != suite_name:
        raise ValueError(
            f"Policy artifact suite_name must be {suite_name!r}, got {artifact_suite_name!r}."
        )
    if "normalization_state" not in payload:
        raise ValueError("Policy artifact must record normalization_state.")
    contract = build_policy_artifact_contract(
        suite_name=suite_name,
        artifact_path=path,
        observation_shape=_as_shape(payload.get("observation_shape"), name="observation_shape"),
        action_shape=_as_shape(payload.get("action_shape"), name="action_shape"),
        normalization_state=payload["normalization_state"],
    )
    constant_action = _as_vector(
        payload.get("constant_action", np.zeros(EXPECTED_ACTION_SHAPE, dtype=np.float32)),
        name="constant_action",
        expected_shape=contract.action_shape,
    )
    return LoadedPaperAPolicy(contract=contract, constant_action=constant_action)
