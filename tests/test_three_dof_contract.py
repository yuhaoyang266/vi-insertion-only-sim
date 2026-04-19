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
