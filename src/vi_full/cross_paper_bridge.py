from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

import numpy as np


CONTRACT_RELATIVE_PATH = Path("docs") / "cross_paper_interface_contract.md"
CONTRACT_SHA = "19a155c7a754cacce7aef9bcc9b72007a00667589de43821ae03d6a0271d5d3b"
CONTRACT_VERSION = "2026-05-01"
PAPER_A_ACTION_LOW = np.array([-1.0, -1.0, -1.0, 0.0, 0.0], dtype=np.float64)
PAPER_A_ACTION_HIGH = np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float64)
PAPER_A_POLICY_SUITE_NAMES = (
    "ppo_no_bc",
    "bc_only_stable_r32_p32",
    "fixed_impedance_rl_stable_r32_p32",
    "repaired_mainline_bc_to_ppo",
    "dapg_lite_repaired_mainline",
)

STEP_SCALE_XY_M = 0.0012
STEP_SCALE_Z_M = 0.0010
MIN_K_XY = 20.0
MAX_K_XY = 110.0
MIN_K_Z = 35.0
MAX_K_Z = 140.0
TORQUE_DROP_GUARD_N_M = 0.1


@dataclass(frozen=True, slots=True)
class PaperBActionMapping:
    schema_p_action: np.ndarray
    env_action: dict[str, Any]
    clipped: bool
    dyaw: float = 0.0


@dataclass(frozen=True, slots=True)
class PaperAObservationProjection:
    observation: np.ndarray
    dropped_torque_norm_nm: float
    out_of_paper_a_scope: bool
    contact_count: int
    contact_state: str


@dataclass(frozen=True, slots=True)
class PaperAPolicyStub:
    suite_name: str
    status: str = "not_available"

    def act(self, observation: np.ndarray) -> np.ndarray:
        del observation
        raise RuntimeError(f"Paper-A policy suite {self.suite_name!r} is not available.")


def resolve_contract_path(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    return root / CONTRACT_RELATIVE_PATH


def compute_contract_sha(contract_path: Path | None = None) -> str:
    path = contract_path if contract_path is not None else resolve_contract_path()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_contract_sha_current(contract_path: Path | None = None) -> str:
    actual_sha = compute_contract_sha(contract_path)
    if actual_sha != CONTRACT_SHA:
        raise RuntimeError(
            "Cross-paper interface contract SHA mismatch: "
            f"expected {CONTRACT_SHA}, got {actual_sha}"
        )
    return actual_sha


def _as_vector(values: Any, *, name: str, shape: tuple[int, ...]) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float64)
    if vector.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {vector.shape}.")
    if not np.isfinite(vector).all():
        raise ValueError(f"{name} must contain only finite values.")
    return vector


def _decode_stiffness(value: float, minimum: float, maximum: float) -> float:
    return float(minimum + float(value) * (maximum - minimum))


def map_paper_a_action_to_paper_b(action: Any) -> PaperBActionMapping:
    paper_a_action = _as_vector(action, name="Paper-A action", shape=(5,))
    schema_p_action = np.clip(paper_a_action, PAPER_A_ACTION_LOW, PAPER_A_ACTION_HIGH)
    clipped = bool(not np.allclose(schema_p_action, paper_a_action))
    stiffness_xy = _decode_stiffness(schema_p_action[3], MIN_K_XY, MAX_K_XY)
    stiffness_z = _decode_stiffness(schema_p_action[4], MIN_K_Z, MAX_K_Z)
    env_action = {
        "dx": float(schema_p_action[0] * STEP_SCALE_XY_M),
        "dy": float(schema_p_action[1] * STEP_SCALE_XY_M),
        "dz": float(schema_p_action[2] * STEP_SCALE_Z_M),
        "droll": 0.0,
        "dpitch": 0.0,
        "k_cart_diag": np.array(
            [stiffness_xy, stiffness_xy, stiffness_z, 0.0, 0.0, 0.0],
            dtype=np.float64,
        ),
    }
    return PaperBActionMapping(
        schema_p_action=schema_p_action,
        env_action=env_action,
        clipped=clipped,
    )


def _field(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def _linear_velocity(
    paper_b_observation: Any,
    relative_position: np.ndarray,
    previous_relative_position: np.ndarray | None,
    dt_s: float | None,
) -> np.ndarray:
    ee_twist = _field(paper_b_observation, "ee_twist")
    if ee_twist is not None:
        twist = _as_vector(ee_twist, name="Paper-B ee_twist", shape=(6,))
        return twist[:3]
    if previous_relative_position is None or dt_s is None:
        return np.zeros(3, dtype=np.float64)
    previous = _as_vector(
        previous_relative_position,
        name="previous relative position",
        shape=(3,),
    )
    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive when finite-differencing velocity.")
    return (relative_position - previous) / float(dt_s)


def _force_and_torque(paper_b_observation: Any) -> tuple[np.ndarray, float]:
    wrench = _field(paper_b_observation, "wrench")
    if wrench is None:
        force = _as_vector(
            _field(paper_b_observation, "force", np.zeros(3, dtype=np.float64)),
            name="Paper-B force",
            shape=(3,),
        )
        torque_norm = float(_field(paper_b_observation, "torque_norm_nm", 0.0))
        return force, torque_norm
    wrench_vector = np.asarray(wrench, dtype=np.float64)
    if wrench_vector.shape == (3,):
        if not np.isfinite(wrench_vector).all():
            raise ValueError("Paper-B wrench force must contain only finite values.")
        return wrench_vector, float(_field(paper_b_observation, "torque_norm_nm", 0.0))
    if wrench_vector.shape != (6,):
        raise ValueError(f"Paper-B wrench must have shape (3,) or (6,), got {wrench_vector.shape}.")
    if not np.isfinite(wrench_vector).all():
        raise ValueError("Paper-B wrench must contain only finite values.")
    return wrench_vector[:3], float(np.linalg.norm(wrench_vector[3:]))


def project_paper_b_observation_to_paper_a(
    paper_b_observation: Any,
    *,
    hole_origin_world: Any,
    previous_schema_p_action: Any,
    previous_relative_position: Any | None = None,
    dt_s: float | None = None,
) -> PaperAObservationProjection:
    ee_pos = _as_vector(_field(paper_b_observation, "ee_pos"), name="Paper-B ee_pos", shape=(3,))
    hole_origin = _as_vector(hole_origin_world, name="hole origin", shape=(3,))
    previous_action = _as_vector(
        previous_schema_p_action,
        name="previous Schema-P action",
        shape=(5,),
    )
    relative_position = ee_pos - hole_origin
    previous_relative = (
        None
        if previous_relative_position is None
        else _as_vector(
            previous_relative_position,
            name="previous relative position",
            shape=(3,),
        )
    )
    velocity = _linear_velocity(
        paper_b_observation,
        relative_position,
        previous_relative,
        dt_s,
    )
    force, dropped_torque_norm = _force_and_torque(paper_b_observation)
    observation = np.concatenate(
        [relative_position, velocity, force, previous_action]
    ).astype(np.float32)
    return PaperAObservationProjection(
        observation=observation,
        dropped_torque_norm_nm=dropped_torque_norm,
        out_of_paper_a_scope=dropped_torque_norm > TORQUE_DROP_GUARD_N_M,
        contact_count=int(_field(paper_b_observation, "contact_count", 0)),
        contact_state=str(_field(paper_b_observation, "contact_state", "unknown")),
    )


def build_policy_stub(suite_name: str) -> PaperAPolicyStub:
    if suite_name not in PAPER_A_POLICY_SUITE_NAMES:
        raise ValueError(f"Unknown Paper-A policy suite: {suite_name}")
    return PaperAPolicyStub(suite_name=suite_name)
