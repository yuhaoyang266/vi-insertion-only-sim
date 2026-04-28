import numpy as np

from vi_full.three_dof_config import ThreeDoFInsertionConfig
from vi_full.three_dof_env import ThreeDoFInsertionEnv
from vi_full.three_dof_profiles import build_3dof_profile_config
from vi_full.three_dof_training import build_3dof_mainline_train_config


def test_benchmark_contract_aligns_profile_and_training_defaults() -> None:
    from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT

    profile_config = build_3dof_profile_config("nominal")
    train_config = build_3dof_mainline_train_config(seed=0)

    assert DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps == 64
    assert DEFAULT_3DOF_BENCHMARK_CONTRACT.jam_force_threshold_n == 8.0
    assert DEFAULT_3DOF_BENCHMARK_CONTRACT.jam_persistence_steps == 3
    assert profile_config.max_episode_steps == DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps
    assert train_config.max_episode_steps == DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps
    assert ThreeDoFInsertionConfig().max_episode_steps == 80


def test_terminal_reward_magnitudes_are_configured() -> None:
    env = ThreeDoFInsertionEnv(
        ThreeDoFInsertionConfig(
            success_bonus=2.5,
            jam_penalty=3.5,
        )
    )
    env.reset(seed=0)

    success_breakdown = env._compute_reward_breakdown(
        previous_distance=0.0,
        current_distance=0.0,
        previous_insertion_depth=0.0,
        current_insertion_depth=0.0,
        previous_surface_height=0.0,
        current_surface_height=0.0,
        force_norm=0.0,
        previous_force_std=0.0,
        current_force_std=0.0,
        is_success=True,
        is_jammed=False,
    )
    jam_breakdown = env._compute_reward_breakdown(
        previous_distance=0.0,
        current_distance=0.0,
        previous_insertion_depth=0.0,
        current_insertion_depth=0.0,
        previous_surface_height=0.0,
        current_surface_height=0.0,
        force_norm=0.0,
        previous_force_std=0.0,
        current_force_std=0.0,
        is_success=False,
        is_jammed=True,
    )

    assert success_breakdown["success_bonus"] == 2.5
    assert jam_breakdown["jam_penalty"] == 3.5


def test_hover_penalty_only_applies_when_aligned_agent_is_not_descending() -> None:
    env = ThreeDoFInsertionEnv(
        ThreeDoFInsertionConfig(
            target_insertion_depth_m=0.006,
            aligned_xy_threshold_m=0.0015,
            near_contact_height_m=0.0025,
            approach_bonus_scale=30.0,
            hover_penalty=0.05,
        )
    )
    env.reset(seed=0)
    env.position = env.contact_target_position.copy()
    env.position[2] = 0.001

    descending_breakdown = env._compute_reward_breakdown(
        previous_distance=0.0,
        current_distance=0.0,
        previous_insertion_depth=0.0,
        current_insertion_depth=0.0,
        previous_surface_height=0.002,
        current_surface_height=0.001,
        force_norm=0.0,
        previous_force_std=0.0,
        current_force_std=0.0,
        is_success=False,
        is_jammed=False,
    )
    stationary_breakdown = env._compute_reward_breakdown(
        previous_distance=0.0,
        current_distance=0.0,
        previous_insertion_depth=0.0,
        current_insertion_depth=0.0,
        previous_surface_height=0.001,
        current_surface_height=0.001,
        force_norm=0.0,
        previous_force_std=0.0,
        current_force_std=0.0,
        is_success=False,
        is_jammed=False,
    )

    assert np.isclose(descending_breakdown["approach_bonus"], 0.03)
    assert descending_breakdown["hover_penalty"] == 0.0
    assert stationary_breakdown["hover_penalty"] == env.config.hover_penalty


def test_hard_blocked_rebound_uses_configured_z_clearance() -> None:
    env = ThreeDoFInsertionEnv(
        ThreeDoFInsertionConfig(
            hard_blocked_rebound_m=0.0002,
            hard_blocked_min_z_m=0.00008,
        )
    )
    env.reset(seed=0)
    env.position[2] = 0.0001

    _, _, new_position, _, _ = env._compute_hard_blocked_contact_response(
        proposed_position=np.array([0.002, 0.0, -0.001], dtype=np.float64),
        cartesian_delta=np.array([0.0, 0.0, -0.001], dtype=np.float64),
        candidate_xy_error=np.array([0.002, 0.0], dtype=np.float64),
        lateral_error=0.002,
        overflow=0.001,
        stiffness_xy=100.0,
        stiffness_z=100.0,
    )

    assert np.isclose(new_position[2], 0.00008)


def test_hard_blocked_lateral_jam_load_scale_is_configured() -> None:
    env = ThreeDoFInsertionEnv(
        ThreeDoFInsertionConfig(
            contact_xy_scale=1.0,
            contact_z_scale=1.0,
            hard_blocked_lateral_jam_load_scale=2.0,
        )
    )
    env.reset(seed=0)
    env.uncertainty["wall_friction"] = 0.5

    _, contact_force, _, _, _ = env._compute_hard_blocked_contact_response(
        proposed_position=np.array([0.002, 0.0, -0.001], dtype=np.float64),
        cartesian_delta=np.array([0.0, 0.0, -0.001], dtype=np.float64),
        candidate_xy_error=np.array([0.002, 0.0], dtype=np.float64),
        lateral_error=0.002,
        overflow=0.001,
        stiffness_xy=100.0,
        stiffness_z=100.0,
    )

    assert np.isclose(contact_force[0], -0.2)
    assert np.isclose(contact_force[1], 0.0)


def test_transition_band_records_blocked_contact_suppression() -> None:
    env = ThreeDoFInsertionEnv(ThreeDoFInsertionConfig(contact_transition_band_m=0.001))
    env.reset(seed=0)
    clearance = float(env.uncertainty["clearance_m"])
    overflow = 0.5 * env.config.contact_transition_band_m
    proposed_position = env.contact_target_position.copy()
    proposed_position[:2] += np.array([clearance + overflow, 0.0], dtype=np.float64)
    proposed_position[2] = -0.001

    _, _, blocked_contact, contact_debug, _ = env._apply_contact_dynamics(
        proposed_position=proposed_position,
        cartesian_delta=np.array([0.0, 0.0, -0.001], dtype=np.float64),
        stiffness_xy=100.0,
        stiffness_z=100.0,
    )

    assert blocked_contact is False
    assert contact_debug["within_transition_band"] is True
    assert contact_debug["blocked_contact_suppressed_in_transition_band"] is True


def test_single_force_threshold_violation_is_diagnostic_only(monkeypatch) -> None:
    env = ThreeDoFInsertionEnv(ThreeDoFInsertionConfig())
    env.reset(seed=0)

    def _fake_contact_dynamics(**kwargs):
        del kwargs
        return (
            env.position.copy(),
            np.array([env.config.jam_force_threshold_n + 0.5, 0.0, 0.0], dtype=np.float64),
            False,
            env._empty_contact_debug(),
            np.array([env.config.jam_force_threshold_n + 0.5, 0.0, 0.0], dtype=np.float64),
        )

    monkeypatch.setattr(env, "_apply_contact_dynamics", _fake_contact_dynamics)
    monkeypatch.setattr(env, "_is_success", lambda: False)

    _, _, terminated, truncated, info = env.step(np.zeros(env.action_space.shape, dtype=np.float32))

    assert terminated is False
    assert truncated is False
    assert info["is_jammed"] is False
    assert info["termination_reason"] == "running"
    assert info["force_over_threshold_steps"] == 1
    assert info["meets_documented_force_jam"] is False
    assert info["termination_details"] == {
        "success": False,
        "force_threshold_exceeded": True,
        "blocked_contact_failure": False,
        "meets_documented_force_jam": False,
        "jammed": False,
    }


def test_blocked_contact_failure_is_separate_reason(monkeypatch) -> None:
    env = ThreeDoFInsertionEnv(ThreeDoFInsertionConfig())
    env.reset(seed=0)

    def _fake_contact_dynamics(**kwargs):
        del kwargs
        return (
            env.position.copy(),
            np.array([0.0, 0.0, 0.0], dtype=np.float64),
            True,
            env._empty_contact_debug(),
            np.array([0.0, 0.0, 0.0], dtype=np.float64),
        )

    monkeypatch.setattr(env, "_apply_contact_dynamics", _fake_contact_dynamics)
    monkeypatch.setattr(env, "_is_success", lambda: False)

    info = {}
    terminated = False
    for _ in range(env.config.jam_persistence_steps):
        _, _, terminated, _, info = env.step(
            np.zeros(env.action_space.shape, dtype=np.float32)
        )

    assert terminated is True
    assert info["is_jammed"] is True
    assert info["termination_reason"] == "blocked_contact"
    assert info["blocked_contact_steps"] == env.config.jam_persistence_steps
    assert info["meets_documented_force_jam"] is False
    assert info["termination_details"] == {
        "success": False,
        "force_threshold_exceeded": False,
        "blocked_contact_failure": True,
        "meets_documented_force_jam": False,
        "jammed": True,
    }


def test_blocked_contact_failure_requires_persistence(monkeypatch) -> None:
    env = ThreeDoFInsertionEnv(ThreeDoFInsertionConfig())
    env.reset(seed=0)

    def _fake_contact_dynamics(**kwargs):
        del kwargs
        return (
            env.position.copy(),
            np.array([0.0, 0.0, 0.0], dtype=np.float64),
            True,
            env._empty_contact_debug(),
            np.array([0.0, 0.0, 0.0], dtype=np.float64),
        )

    monkeypatch.setattr(env, "_apply_contact_dynamics", _fake_contact_dynamics)
    monkeypatch.setattr(env, "_is_success", lambda: False)

    for step_index in range(env.config.jam_persistence_steps - 1):
        _, _, terminated, truncated, info = env.step(
            np.zeros(env.action_space.shape, dtype=np.float32)
        )
        assert terminated is False
        assert truncated is False
        assert info["is_jammed"] is False
        assert info["termination_reason"] == "running"
        assert info["blocked_contact_steps"] == step_index + 1
        assert info["meets_documented_force_jam"] is False


def test_force_jam_requires_consecutive_violations(
    monkeypatch,
) -> None:
    env = ThreeDoFInsertionEnv(ThreeDoFInsertionConfig())
    env.reset(seed=0)

    def _fake_contact_dynamics(**kwargs):
        del kwargs
        return (
            env.position.copy(),
            np.array([env.config.jam_force_threshold_n + 0.5, 0.0, 0.0], dtype=np.float64),
            False,
            env._empty_contact_debug(),
            np.array([env.config.jam_force_threshold_n + 0.5, 0.0, 0.0], dtype=np.float64),
        )

    monkeypatch.setattr(env, "_apply_contact_dynamics", _fake_contact_dynamics)
    monkeypatch.setattr(env, "_is_success", lambda: False)

    info = {}
    terminated = False
    for step_index in range(env.config.jam_persistence_steps):
        _, _, terminated, _, info = env.step(
            np.zeros(env.action_space.shape, dtype=np.float32)
        )
        if step_index < env.config.jam_persistence_steps - 1:
            assert terminated is False
            assert info["is_jammed"] is False
            assert info["termination_reason"] == "running"

    assert terminated is True
    assert info["is_jammed"] is True
    assert info["termination_reason"] == "force_threshold"
    assert info["force_over_threshold_steps"] == env.config.jam_persistence_steps
    assert info["meets_documented_force_jam"] is True
    assert info["termination_details"] == {
        "success": False,
        "force_threshold_exceeded": True,
        "blocked_contact_failure": False,
        "meets_documented_force_jam": True,
        "jammed": True,
    }


def test_force_jam_counter_resets_after_below_threshold_step(monkeypatch) -> None:
    env = ThreeDoFInsertionEnv(ThreeDoFInsertionConfig())
    env.reset(seed=0)
    force_sequence = [
        env.config.jam_force_threshold_n + 0.5,
        env.config.jam_force_threshold_n + 0.5,
        env.config.jam_force_threshold_n - 0.5,
        env.config.jam_force_threshold_n + 0.5,
        env.config.jam_force_threshold_n + 0.5,
    ]

    def _fake_contact_dynamics(**kwargs):
        del kwargs
        force_norm = force_sequence.pop(0)
        force_vector = np.array([force_norm, 0.0, 0.0], dtype=np.float64)
        return (
            env.position.copy(),
            force_vector,
            False,
            env._empty_contact_debug(),
            force_vector,
        )

    monkeypatch.setattr(env, "_apply_contact_dynamics", _fake_contact_dynamics)
    monkeypatch.setattr(env, "_is_success", lambda: False)

    observed_force_counts = []
    for _ in range(5):
        _, _, terminated, truncated, info = env.step(
            np.zeros(env.action_space.shape, dtype=np.float32)
        )
        observed_force_counts.append(info["force_over_threshold_steps"])
        assert terminated is False
        assert truncated is False
        assert info["is_jammed"] is False
        assert info["termination_reason"] == "running"
        assert info["meets_documented_force_jam"] is False

    assert observed_force_counts == [1, 2, 0, 1, 2]


def test_force_threshold_keeps_priority_when_blocked_contact_also_fails(
    monkeypatch,
) -> None:
    env = ThreeDoFInsertionEnv(ThreeDoFInsertionConfig())
    env.reset(seed=0)

    def _fake_contact_dynamics(**kwargs):
        del kwargs
        return (
            env.position.copy(),
            np.array([env.config.jam_force_threshold_n + 0.5, 0.0, 0.0], dtype=np.float64),
            True,
            env._empty_contact_debug(),
            np.array([env.config.jam_force_threshold_n + 0.5, 0.0, 0.0], dtype=np.float64),
        )

    monkeypatch.setattr(env, "_apply_contact_dynamics", _fake_contact_dynamics)
    monkeypatch.setattr(env, "_is_success", lambda: False)

    info = {}
    for _ in range(env.config.jam_persistence_steps):
        _, _, _, _, info = env.step(np.zeros(env.action_space.shape, dtype=np.float32))

    assert info["termination_reason"] == "force_threshold"
    assert info["termination_details"] == {
        "success": False,
        "force_threshold_exceeded": True,
        "blocked_contact_failure": True,
        "meets_documented_force_jam": True,
        "jammed": True,
    }
