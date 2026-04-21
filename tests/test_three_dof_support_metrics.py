import numpy as np
import pytest

from vi_full.three_dof_benchmark import collect_3dof_policy_rollout_samples
from vi_full.three_dof_support_metrics import (
    ThreeDoFSupportMetricConfig,
    compute_3dof_support_coverage_index,
    project_3dof_support_signature,
)


class _ConstantPolicy:
    def __init__(self, action: np.ndarray) -> None:
        self._action = np.asarray(action, dtype=np.float32)

    def act(self, observation: np.ndarray) -> np.ndarray:
        del observation
        return self._action.copy()


class _SampleEpisodeEnv:
    def __init__(self, episode_observations: list[list[np.ndarray]]) -> None:
        self._episode_observations = episode_observations
        self._episode_index = -1
        self._step_index = 0
        self.observation_space = type("_ObsSpace", (), {"shape": (14,)})()
        self.action_space = type("_ActSpace", (), {"shape": (5,)})()

    def reset(self, seed: int = 0):
        del seed
        self._episode_index += 1
        self._step_index = 0
        return self._episode_observations[self._episode_index][0].copy(), {}

    def step(self, action: np.ndarray):
        del action
        episode = self._episode_observations[self._episode_index]
        self._step_index += 1
        terminated = self._step_index >= len(episode)
        next_observation = (
            np.zeros(14, dtype=np.float32)
            if terminated
            else episode[self._step_index].copy()
        )
        return next_observation, 0.0, terminated, False, {}


def _make_observation(
    *,
    xy_norm: float,
    z: float,
    force_norm: float,
) -> np.ndarray:
    observation = np.zeros(14, dtype=np.float32)
    observation[0] = float(xy_norm)
    observation[2] = float(z)
    observation[6] = float(force_norm)
    return observation


def _make_action(
    *,
    xy_norm: float,
    dz: float,
    k_xy: float,
    k_z: float,
) -> np.ndarray:
    action = np.zeros(5, dtype=np.float32)
    action[0] = float(xy_norm)
    action[2] = float(dz)
    action[3] = float(k_xy)
    action[4] = float(k_z)
    return action


def test_project_3dof_support_signature_uses_projected_state_action_fields() -> None:
    observations = np.asarray(
        [_make_observation(xy_norm=0.005, z=-0.002, force_norm=0.5)],
        dtype=np.float32,
    )
    actions = np.asarray(
        [_make_action(xy_norm=0.5, dz=-0.2, k_xy=0.6, k_z=0.8)],
        dtype=np.float32,
    )

    signature = project_3dof_support_signature(observations, actions)

    assert signature.shape == (1, 7)
    assert signature[0].tolist() == [
        np.float32(0.005),
        np.float32(-0.002),
        np.float32(0.5),
        np.float32(0.5),
        np.float32(-0.2),
        np.float32(0.6),
        np.float32(0.8),
    ]


def test_compute_3dof_support_coverage_index_reports_sample_and_cell_overlap() -> None:
    config = ThreeDoFSupportMetricConfig(
        obs_xy_norm_bin_m=1.0,
        obs_z_bin_m=1.0,
        force_norm_bin_n=1.0,
        action_xy_norm_bin=1.0,
        action_dz_bin=1.0,
        action_k_xy_bin=1.0,
        action_k_z_bin=1.0,
    )
    demo_observations = np.asarray(
        [
            _make_observation(xy_norm=0.2, z=0.2, force_norm=0.2),
            _make_observation(xy_norm=1.2, z=1.2, force_norm=1.2),
        ],
        dtype=np.float32,
    )
    demo_actions = np.asarray(
        [
            _make_action(xy_norm=0.2, dz=0.2, k_xy=0.2, k_z=0.2),
            _make_action(xy_norm=1.2, dz=1.2, k_xy=1.2, k_z=1.2),
        ],
        dtype=np.float32,
    )
    rollout_observations = np.asarray(
        [
            _make_observation(xy_norm=0.1, z=0.1, force_norm=0.1),
            _make_observation(xy_norm=0.4, z=0.2, force_norm=0.3),
            _make_observation(xy_norm=2.2, z=2.2, force_norm=2.2),
        ],
        dtype=np.float32,
    )
    rollout_actions = np.asarray(
        [
            _make_action(xy_norm=0.1, dz=0.1, k_xy=0.1, k_z=0.1),
            _make_action(xy_norm=0.4, dz=0.2, k_xy=0.3, k_z=0.2),
            _make_action(xy_norm=2.2, dz=2.2, k_xy=2.2, k_z=2.2),
        ],
        dtype=np.float32,
    )

    summary = compute_3dof_support_coverage_index(
        demo_observations=demo_observations,
        demo_actions=demo_actions,
        rollout_observations=rollout_observations,
        rollout_actions=rollout_actions,
        config=config,
    )

    assert summary["support_coverage_index"] == 2.0 / 3.0
    assert summary["covered_rollout_sample_count"] == 2
    assert summary["rollout_sample_count"] == 3
    assert summary["demo_unique_cell_count"] == 2
    assert summary["rollout_unique_cell_count"] == 2
    assert summary["shared_unique_cell_count"] == 1
    assert summary["support_cell_coverage"] == 0.5


def test_compute_3dof_support_coverage_index_rejects_mismatched_row_counts() -> None:
    with np.testing.assert_raises_regex(
        ValueError,
        "observations and actions must have the same row count",
    ):
        compute_3dof_support_coverage_index(
            demo_observations=np.zeros((2, 14), dtype=np.float32),
            demo_actions=np.zeros((1, 5), dtype=np.float32),
            rollout_observations=np.zeros((0, 14), dtype=np.float32),
            rollout_actions=np.zeros((0, 5), dtype=np.float32),
        )


def test_collect_3dof_policy_rollout_samples_records_all_episode_rows() -> None:
    env = _SampleEpisodeEnv(
        [
            [
                _make_observation(xy_norm=0.1, z=-0.1, force_norm=0.0),
                _make_observation(xy_norm=0.2, z=-0.2, force_norm=0.1),
            ],
            [
                _make_observation(xy_norm=0.3, z=-0.3, force_norm=0.2),
            ],
        ]
    )
    policy = _ConstantPolicy(_make_action(xy_norm=0.4, dz=-0.2, k_xy=0.5, k_z=0.6))

    observations, actions = collect_3dof_policy_rollout_samples(
        env,
        policy,
        episodes=2,
        seed=0,
    )

    assert observations.shape == (3, 14)
    assert actions.shape == (3, 5)
    assert observations[:, 0].tolist() == pytest.approx([0.1, 0.2, 0.3])
    assert actions[:, 3].tolist() == pytest.approx([0.5, 0.5, 0.5])
