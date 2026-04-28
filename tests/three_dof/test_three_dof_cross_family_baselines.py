import numpy as np
import pytest


def test_cross_family_pilot_registry_exposes_expected_methods() -> None:
    from vi_full.three_dof_cross_family_baselines import (
        build_3dof_cross_family_pilot_registry,
    )

    registry = build_3dof_cross_family_pilot_registry()

    assert registry["experiment_name"] == "three_dof_cross_family_pilot"
    assert registry["budget_points"] == [50_000, 100_000, 200_000]
    assert registry["default_profiles"] == ["nominal"]
    assert [
        (method["method_name"], method["algorithm"])
        for method in registry["methods"]
    ] == [
        ("ppo_no_bc", "ppo"),
        ("sac_no_bc", "sac"),
        ("td3_no_bc", "td3"),
    ]

    ppo_method = registry["methods"][0]
    assert ppo_method["train_overrides"]["n_envs"] == 4
    assert ppo_method["train_overrides"]["n_steps"] == 256
    assert ppo_method["train_overrides"]["n_epochs"] == 4

    sac_method = registry["methods"][1]
    assert sac_method["train_overrides"]["n_envs"] == 1
    assert sac_method["train_overrides"]["learning_starts"] == 1024
    assert sac_method["train_overrides"]["buffer_size"] == 200_000
    assert sac_method["train_overrides"]["train_freq"] == 1

    td3_method = registry["methods"][2]
    assert td3_method["train_overrides"]["n_envs"] == 1
    assert td3_method["train_overrides"]["learning_starts"] == 1024
    assert td3_method["train_overrides"]["buffer_size"] == 200_000
    assert td3_method["train_overrides"]["action_noise_std"] == 0.1


def test_cross_family_train_config_uses_public_train_reset_factory() -> None:
    from vi_full.three_dof_cross_family_baselines import (
        build_3dof_cross_family_train_config,
    )
    from vi_full.three_dof_training import build_3dof_default_train_reset_config

    config = build_3dof_cross_family_train_config(
        method_name="ppo_no_bc",
        seed=0,
        total_timesteps=64,
        max_episode_steps=64,
    )

    assert config.train_reset_config == build_3dof_default_train_reset_config()


def test_cross_family_train_config_rejects_action_noise_for_non_td3() -> None:
    from vi_full.three_dof_cross_family_baselines import (
        build_3dof_cross_family_train_config,
    )

    with pytest.raises(
        ValueError,
        match="action_noise_std is only supported for td3 baselines",
    ):
        build_3dof_cross_family_train_config(
            method_name="sac_no_bc",
            seed=0,
            total_timesteps=64,
            max_episode_steps=64,
            train_overrides={"action_noise_std": 0.1},
        )


def test_train_3dof_family_baseline_selects_td3_and_action_noise(monkeypatch) -> None:
    import vi_full.three_dof_cross_family_baselines as module

    init_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    class _FakeNoise:
        def __init__(self, mean, sigma) -> None:
            self.mean = mean
            self.sigma = sigma

    class _FakeActionSpace:
        shape = (5,)

    class _FakeVecNormalize:
        def __init__(self) -> None:
            self.action_space = _FakeActionSpace()
            self.training = True
            self.norm_reward = True

        def close(self) -> None:
            return None

    class _FakeTD3:
        def __init__(self, *args, **kwargs) -> None:
            init_calls.append((args, kwargs))

        def learn(self, total_timesteps: int) -> None:
            self.total_timesteps = total_timesteps

    fake_vec_env = _FakeVecNormalize()
    monkeypatch.setattr(
        module,
        "create_3dof_baseline_training_vec_env",
        lambda config: fake_vec_env,
    )
    monkeypatch.setattr(module, "TD3", _FakeTD3)
    monkeypatch.setattr(module, "NormalActionNoise", _FakeNoise)

    config = module.build_3dof_cross_family_train_config(
        method_name="td3_no_bc",
        seed=7,
        total_timesteps=64,
        max_episode_steps=64,
    )

    artifacts = module.train_3dof_family_baseline(config)

    assert init_calls
    args, kwargs = init_calls[0]
    assert args[:2] == ("MlpPolicy", fake_vec_env)
    assert kwargs["device"] == "cpu"
    assert kwargs["seed"] == 7
    assert kwargs["train_freq"] == 1
    assert kwargs["gradient_steps"] == 1
    assert kwargs["learning_starts"] == 1024
    assert isinstance(kwargs["action_noise"], _FakeNoise)
    np.testing.assert_allclose(kwargs["action_noise"].mean, np.zeros(5, dtype=np.float32))
    np.testing.assert_allclose(kwargs["action_noise"].sigma, np.full(5, 0.1, dtype=np.float32))
    assert artifacts.training_summary["algorithm"] == "td3"
    assert artifacts.training_summary["method_name"] == "td3_no_bc"
    assert artifacts.training_summary["total_timesteps"] == 64
    assert fake_vec_env.training is False
    assert fake_vec_env.norm_reward is False
