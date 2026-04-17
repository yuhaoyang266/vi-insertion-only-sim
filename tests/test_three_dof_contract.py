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


def test_force_threshold_termination_reason_is_exposed(monkeypatch) -> None:
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

    assert terminated is True
    assert truncated is False
    assert info["is_jammed"] is True
    assert info["termination_reason"] == "force_threshold"
    assert info["force_over_threshold_steps"] == 1
    assert info["meets_documented_force_jam"] is False


def test_blocked_contact_termination_reason_is_separate(monkeypatch) -> None:
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


def test_meets_documented_force_jam_turns_true_after_consecutive_force_violations(
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
    for _ in range(env.config.jam_persistence_steps):
        _, _, _, _, info = env.step(np.zeros(env.action_space.shape, dtype=np.float32))

    assert info["is_jammed"] is True
    assert info["termination_reason"] == "force_threshold"
    assert info["force_over_threshold_steps"] == env.config.jam_persistence_steps
    assert info["meets_documented_force_jam"] is True
