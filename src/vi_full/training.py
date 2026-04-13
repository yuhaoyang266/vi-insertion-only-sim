from __future__ import annotations

import gc
from dataclasses import dataclass, field
from copy import deepcopy

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from vi_full.env import CurriculumStage, PandaVariableImpedanceEnv, ResetConfig
from vi_full.policies import (
    JamAwareVariableImpedanceDemoPolicy,
    PoseOnlyPolicy,
    VariableImpedanceHeuristicPolicy,
)


def _default_near_contact_reset_config() -> ResetConfig:
    return ResetConfig(
        target_xy_noise_m=0.0005,
        curriculum_stages=(
            CurriculumStage(
                start_xy_noise_m=0.0002,
                start_depth_fraction_range=(0.82, 0.86),
                weight=1.0,
            ),
        ),
    )


def _default_bc_reset_config() -> ResetConfig:
    return ResetConfig(
        target_xy_noise_m=0.0008,
        curriculum_stages=(
            CurriculumStage(
                start_xy_noise_m=0.0008,
                start_depth_fraction_range=(0.0, 0.2),
                weight=0.2,
            ),
            CurriculumStage(
                start_xy_noise_m=0.0005,
                start_depth_fraction_range=(0.35, 0.75),
                weight=0.35,
            ),
            CurriculumStage(
                start_xy_noise_m=0.0002,
                start_depth_fraction_range=(0.82, 0.86),
                weight=0.45,
            ),
        ),
    )


@dataclass(frozen=True, slots=True)
class PPOTrainConfig:
    total_timesteps: int = 2048
    n_envs: int = 4
    n_steps: int = 128
    batch_size: int = 128
    n_epochs: int = 4
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    ent_coef: float = 0.0
    vf_coef: float = 0.5
    clip_range: float = 0.2
    seed: int = 0
    max_episode_steps: int = 32
    norm_obs: bool = True
    norm_reward: bool = True
    verbose: int = 0
    bc_rollout_episodes: int = 0
    bc_pretrain_steps: int = 0
    bc_batch_size: int = 128
    bc_learning_rate: float = 1e-3
    bc_demo_policy_name: str = "heuristic"
    contact_finetune_timesteps: int = 0
    hard_reset_finetune_timesteps: int = 0
    bc_reset_config: ResetConfig = field(default_factory=_default_bc_reset_config)
    contact_finetune_reset_config: ResetConfig = field(
        default_factory=_default_near_contact_reset_config
    )
    train_reset_config: ResetConfig = field(
        default_factory=lambda: ResetConfig(
            target_xy_noise_m=0.001,
            curriculum_stages=(
                CurriculumStage(
                    start_xy_noise_m=0.0008,
                    start_depth_fraction_range=(0.0, 0.2),
                    weight=0.35,
                ),
                CurriculumStage(
                    start_xy_noise_m=0.0005,
                    start_depth_fraction_range=(0.35, 0.75),
                    weight=0.4,
                ),
                CurriculumStage(
                    start_xy_noise_m=0.0002,
                    start_depth_fraction_range=(0.82, 0.86),
                    weight=0.25,
                ),
            ),
        )
    )


@dataclass(slots=True)
class PPOArtifacts:
    model: PPO | None
    vec_normalize: VecNormalize | None
    train_config: PPOTrainConfig

    def make_eval_env(self, seed: int | None = None) -> PandaVariableImpedanceEnv:
        env = PandaVariableImpedanceEnv(max_episode_steps=self.train_config.max_episode_steps)
        if seed is not None:
            env.reset(seed=seed)
        return env

    def close(self) -> None:
        if self.vec_normalize is not None:
            self.vec_normalize.close()
        if self.model is not None:
            if hasattr(self.model, "env"):
                self.model.env = None
        self.vec_normalize = None
        self.model = None
        gc.collect()


class VecNormalizePredictor:
    def __init__(self, *, model: PPO, vec_normalize: VecNormalize) -> None:
        self.model = model
        self.vec_normalize = vec_normalize
        self.name = getattr(model, "__class__", type(model)).__name__

    def predict(
        self, observation: np.ndarray, deterministic: bool = True
    ) -> tuple[np.ndarray, object]:
        batched = np.asarray(observation, dtype=np.float32)[None, :]
        normalized = self.vec_normalize.normalize_obs(batched).astype(np.float32)
        action, state = self.model.predict(normalized[0], deterministic=deterministic)
        return np.asarray(action, dtype=np.float32), state


def create_training_vec_env(config: PPOTrainConfig) -> VecNormalize:
    return _create_vec_env_with_reset_config(config, reset_config=config.train_reset_config)


def _create_vec_env_with_reset_config(
    config: PPOTrainConfig,
    *,
    reset_config: ResetConfig,
) -> VecNormalize:
    def _make_env(rank: int):
        def _factory():
            env = PandaVariableImpedanceEnv(
                max_episode_steps=config.max_episode_steps,
                reset_config=reset_config,
            )
            env.reset(seed=config.seed + rank)
            return env

        return _factory

    vec_env = DummyVecEnv([_make_env(rank) for rank in range(config.n_envs)])
    return VecNormalize(
        vec_env,
        norm_obs=config.norm_obs,
        norm_reward=config.norm_reward,
        clip_obs=10.0,
        gamma=config.gamma,
    )


def _transfer_vecnormalize_stats(source: VecNormalize, target: VecNormalize) -> None:
    if source.norm_obs and target.norm_obs:
        target.obs_rms = deepcopy(source.obs_rms)
    if source.norm_reward and target.norm_reward:
        target.ret_rms = deepcopy(source.ret_rms)
    target.returns = np.zeros_like(target.returns)


def _continue_training_with_reset_config(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: PPOTrainConfig,
    reset_config: ResetConfig,
    total_timesteps: int,
) -> VecNormalize:
    if total_timesteps <= 0:
        return vec_env

    next_vec_env = _create_vec_env_with_reset_config(config, reset_config=reset_config)
    _transfer_vecnormalize_stats(vec_env, next_vec_env)
    model.set_env(next_vec_env)
    model.learn(total_timesteps=total_timesteps, reset_num_timesteps=False)
    vec_env.close()
    return next_vec_env


def collect_heuristic_demonstrations(
    config: PPOTrainConfig,
    episodes: int,
) -> tuple[np.ndarray, np.ndarray]:
    policy = _build_bc_demo_policy(config.bc_demo_policy_name)
    env = PandaVariableImpedanceEnv(
        max_episode_steps=config.max_episode_steps,
        reset_config=config.bc_reset_config,
    )
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    try:
        for episode_index in range(episodes):
            observation, _ = env.reset(seed=config.seed + 50_000 + episode_index)
            terminated = False
            truncated = False
            while not (terminated or truncated):
                action = policy.act(observation)
                observations.append(np.asarray(observation, dtype=np.float32).copy())
                actions.append(np.asarray(action, dtype=np.float32).copy())
                observation, _, terminated, truncated, _ = env.step(action)
    finally:
        env.close()

    if not observations:
        obs_dim = env.observation_space.shape[0]
        act_dim = env.action_space.shape[0]
        return (
            np.zeros((0, obs_dim), dtype=np.float32),
            np.zeros((0, act_dim), dtype=np.float32),
        )
    return np.stack(observations).astype(np.float32), np.stack(actions).astype(np.float32)


def _build_bc_demo_policy(policy_name: str):
    if policy_name == "heuristic":
        return VariableImpedanceHeuristicPolicy()
    if policy_name == "jam_aware":
        return JamAwareVariableImpedanceDemoPolicy()
    if policy_name == "pose_only":
        return PoseOnlyPolicy()
    raise ValueError(f"Unknown bc_demo_policy_name: {policy_name}")


def _behavior_clone_warm_start(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: PPOTrainConfig,
) -> None:
    if config.bc_pretrain_steps <= 0 or config.bc_rollout_episodes <= 0:
        return

    observations, actions = collect_heuristic_demonstrations(
        config,
        episodes=config.bc_rollout_episodes,
    )
    if observations.shape[0] == 0:
        return

    if config.norm_obs:
        vec_env.obs_rms.update(observations)
        observations = vec_env.normalize_obs(observations)

    policy = model.policy
    policy.set_training_mode(True)
    optimizer = torch.optim.Adam(policy.parameters(), lr=config.bc_learning_rate)
    obs_tensor = torch.as_tensor(observations, device=policy.device, dtype=torch.float32)
    action_tensor = torch.as_tensor(actions, device=policy.device, dtype=torch.float32)

    for _ in range(config.bc_pretrain_steps):
        permutation = torch.randperm(obs_tensor.shape[0], device=policy.device)
        for start in range(0, obs_tensor.shape[0], config.bc_batch_size):
            batch_indices = permutation[start : start + config.bc_batch_size]
            batch_obs = obs_tensor[batch_indices]
            batch_actions = action_tensor[batch_indices]
            distribution = policy.get_distribution(batch_obs)
            loss = -distribution.log_prob(batch_actions).mean()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()


def train_ppo_agent(config: PPOTrainConfig) -> PPOArtifacts:
    vec_env = create_training_vec_env(config)
    model = PPO(
        "MlpPolicy",
        vec_env,
        n_steps=config.n_steps,
        batch_size=config.batch_size,
        n_epochs=config.n_epochs,
        learning_rate=config.learning_rate,
        gamma=config.gamma,
        gae_lambda=config.gae_lambda,
        ent_coef=config.ent_coef,
        vf_coef=config.vf_coef,
        clip_range=config.clip_range,
        seed=config.seed,
        verbose=config.verbose,
    )
    _behavior_clone_warm_start(model=model, vec_env=vec_env, config=config)
    model.learn(total_timesteps=config.total_timesteps)
    vec_env = _continue_training_with_reset_config(
        model=model,
        vec_env=vec_env,
        config=config,
        reset_config=config.contact_finetune_reset_config,
        total_timesteps=config.contact_finetune_timesteps,
    )
    vec_env = _continue_training_with_reset_config(
        model=model,
        vec_env=vec_env,
        config=config,
        reset_config=ResetConfig(),
        total_timesteps=config.hard_reset_finetune_timesteps,
    )
    vec_env.training = False
    vec_env.norm_reward = False
    return PPOArtifacts(model=model, vec_normalize=vec_env, train_config=config)
