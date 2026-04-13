from __future__ import annotations

from collections.abc import Mapping

import numpy as np


def evaluate_policy(
    env,
    policy,
    episodes: int = 5,
    seed: int = 0,
) -> dict[str, float | int | str]:
    episode_returns: list[float] = []
    final_distances: list[float] = []
    successes: list[float] = []
    episode_lengths: list[int] = []
    peak_contact_forces: list[float] = []
    jam_flags: list[float] = []

    for episode_index in range(episodes):
        observation, info = env.reset(seed=seed + episode_index)
        del info
        terminated = False
        truncated = False
        total_return = 0.0
        step_count = 0
        final_info: Mapping[str, object] = {}
        episode_peak_contact_force = 0.0
        jammed = False

        while not (terminated or truncated):
            action = policy.act(observation)
            observation, reward, terminated, truncated, final_info = env.step(action)
            total_return += float(reward)
            step_count += 1
            episode_peak_contact_force = max(
                episode_peak_contact_force, float(final_info["peak_contact_force"])
            )
            jammed = jammed or bool(final_info["is_jammed"])

        episode_returns.append(total_return)
        episode_lengths.append(step_count)
        final_distances.append(float(final_info["distance_to_target"]))
        successes.append(float(bool(final_info["is_success"])))
        peak_contact_forces.append(episode_peak_contact_force)
        jam_flags.append(float(jammed))

    return {
        "policy_name": getattr(policy, "name", policy.__class__.__name__),
        "episodes": episodes,
        "success_rate": float(np.mean(successes)),
        "mean_episode_return": float(np.mean(episode_returns)),
        "mean_final_distance": float(np.mean(final_distances)),
        "mean_episode_length": float(np.mean(episode_lengths)),
        "mean_peak_contact_force": float(np.mean(peak_contact_forces)),
        "jam_rate": float(np.mean(jam_flags)),
    }
