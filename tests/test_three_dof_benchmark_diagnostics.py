import numpy as np

from vi_full.three_dof_benchmark import (
    THREE_DOF_NUMERIC_METRICS,
    evaluate_3dof_policy,
    summarize_3dof_seed_runs,
    trace_3dof_policy_rollout,
)


class _NoOpPolicy:
    name = "noop"

    def act(self, observation: np.ndarray) -> np.ndarray:
        del observation
        return np.zeros(5, dtype=np.float32)


class _ScriptedEpisodeEnv:
    def __init__(self, episodes: list[list[dict[str, object]]]) -> None:
        self._episodes = episodes
        self._episode_index = -1
        self._step_index = 0
        self.target_position = np.zeros(3, dtype=np.float64)
        self.config = type(
            "_Config",
            (),
            {
                "contact_intent_trigger_height_m": 0.001,
                "approach_alignment_trigger_height_m": 0.01,
                "approach_alignment_trigger_xy_threshold_m": 0.01,
                "contact_intent_trigger_xy_threshold_m": 0.01,
                "near_contact_height_m": 0.002,
            },
        )()

    def reset(self, seed: int = 0):
        del seed
        self._episode_index += 1
        self._step_index = 0
        return np.zeros(14, dtype=np.float32), {}

    def step(self, action: np.ndarray):
        del action
        episode = self._episodes[self._episode_index]
        step = episode[self._step_index]
        self._step_index += 1
        return (
            np.zeros(14, dtype=np.float32),
            float(step["reward"]),
            bool(step["terminated"]),
            bool(step["truncated"]),
            dict(step["info"]),
        )

    def _insertion_depth(self) -> float:
        return 0.0


def _base_info(
    *,
    is_success: bool,
    is_jammed: bool,
    termination_reason: str,
    termination_details: dict[str, bool],
    contact_force_norm: float = 0.1,
) -> dict[str, object]:
    return {
        "distance_to_target": 0.001,
        "contact_force_norm": contact_force_norm,
        "force_std": 0.0,
        "peak_contact_force": max(contact_force_norm, 0.0),
        "is_success": is_success,
        "is_jammed": is_jammed,
        "termination_reason": termination_reason,
        "termination_details": termination_details,
        "decoded_k_xy": 0.5,
        "decoded_k_z": 0.5,
        "wall_contact_force_norm": 0.0,
        "bottom_contact_force_norm": 0.0,
        "approx_normal_force_norm": 0.0,
        "approx_tangential_force_norm": 0.0,
        "contact_work_increment": 0.0,
        "cumulative_contact_work": 0.0,
        "contact_impulse_increment": 0.0,
        "cumulative_contact_impulse": 0.0,
        "contact_phase_label": "jammed" if is_jammed else "approach",
        "action_modifiers": {
            "phase_action_bias_applied": False,
            "approach_alignment_projection_applied": False,
            "contact_intent_projection_applied": False,
        },
    }


def _summary_with_defaults(**overrides: float | int | str) -> dict[str, float | int | str]:
    summary: dict[str, float | int | str] = {
        "policy_name": "ppo",
        "uncertainty_profile": "nominal",
        "seed": 0,
    }
    for metric_name in THREE_DOF_NUMERIC_METRICS:
        summary[metric_name] = 0.0
    summary.update(overrides)
    return summary


def test_evaluate_3dof_policy_reports_termination_diagnostic_rates() -> None:
    env = _ScriptedEpisodeEnv(
        [
            [
                {
                    "reward": 1.0,
                    "terminated": True,
                    "truncated": False,
                    "info": _base_info(
                        is_success=False,
                        is_jammed=True,
                        termination_reason="force_threshold",
                        termination_details={
                            "success": False,
                            "force_threshold_exceeded": True,
                            "blocked_contact_failure": False,
                            "meets_documented_force_jam": True,
                            "jammed": True,
                        },
                    ),
                }
            ],
            [
                {
                    "reward": 1.0,
                    "terminated": True,
                    "truncated": False,
                    "info": _base_info(
                        is_success=False,
                        is_jammed=True,
                        termination_reason="blocked_contact",
                        termination_details={
                            "success": False,
                            "force_threshold_exceeded": False,
                            "blocked_contact_failure": True,
                            "meets_documented_force_jam": False,
                            "jammed": True,
                        },
                    ),
                }
            ],
            [
                {
                    "reward": 1.0,
                    "terminated": True,
                    "truncated": False,
                    "info": _base_info(
                        is_success=False,
                        is_jammed=True,
                        termination_reason="force_threshold",
                        termination_details={
                            "success": False,
                            "force_threshold_exceeded": True,
                            "blocked_contact_failure": True,
                            "meets_documented_force_jam": True,
                            "jammed": True,
                        },
                    ),
                }
            ],
            [
                {
                    "reward": 1.0,
                    "terminated": True,
                    "truncated": False,
                    "info": _base_info(
                        is_success=True,
                        is_jammed=False,
                        termination_reason="success",
                        termination_details={
                            "success": True,
                            "force_threshold_exceeded": False,
                            "blocked_contact_failure": False,
                            "meets_documented_force_jam": False,
                            "jammed": False,
                        },
                        contact_force_norm=0.0,
                    ),
                }
            ],
        ]
    )

    summary = evaluate_3dof_policy(
        env,
        _NoOpPolicy(),
        episodes=4,
        seed=0,
        uncertainty_profile="nominal",
    )

    assert summary["jam_rate"] == 0.75
    assert summary["force_threshold_termination_rate"] == 0.5
    assert summary["blocked_contact_termination_rate"] == 0.5
    assert summary["force_threshold_only_termination_rate"] == 0.25
    assert summary["blocked_contact_only_termination_rate"] == 0.25
    assert summary["force_and_blocked_termination_rate"] == 0.25
    assert summary["documented_force_jam_rate"] == 0.5


def test_trace_3dof_policy_rollout_includes_termination_diagnostics() -> None:
    env = _ScriptedEpisodeEnv(
        [
            [
                {
                    "reward": 0.0,
                    "terminated": True,
                    "truncated": False,
                    "info": _base_info(
                        is_success=False,
                        is_jammed=True,
                        termination_reason="force_threshold",
                        termination_details={
                            "success": False,
                            "force_threshold_exceeded": True,
                            "blocked_contact_failure": True,
                            "meets_documented_force_jam": True,
                            "jammed": True,
                        },
                    ),
                }
            ]
        ]
    )

    trace = trace_3dof_policy_rollout(env, _NoOpPolicy(), seed=0)

    assert trace[0]["termination_reason"] == "force_threshold"
    assert trace[0]["force_threshold_exceeded"] is True
    assert trace[0]["blocked_contact_failure"] is True
    assert trace[0]["meets_documented_force_jam"] is True


def test_summarize_3dof_seed_runs_aggregates_termination_diagnostic_rates() -> None:
    aggregate = summarize_3dof_seed_runs(
        [
            _summary_with_defaults(
                force_threshold_termination_rate=0.5,
                blocked_contact_termination_rate=0.25,
                force_threshold_only_termination_rate=0.25,
                blocked_contact_only_termination_rate=0.0,
                force_and_blocked_termination_rate=0.25,
                documented_force_jam_rate=0.25,
            ),
            _summary_with_defaults(
                seed=1,
                force_threshold_termination_rate=0.0,
                blocked_contact_termination_rate=0.75,
                force_threshold_only_termination_rate=0.0,
                blocked_contact_only_termination_rate=0.5,
                force_and_blocked_termination_rate=0.25,
                documented_force_jam_rate=0.0,
            ),
        ]
    )

    assert aggregate["force_threshold_termination_rate_mean"] == 0.25
    assert aggregate["blocked_contact_termination_rate_mean"] == 0.5
    assert aggregate["force_threshold_only_termination_rate_mean"] == 0.125
    assert aggregate["blocked_contact_only_termination_rate_mean"] == 0.25
    assert aggregate["force_and_blocked_termination_rate_mean"] == 0.25
    assert aggregate["documented_force_jam_rate_mean"] == 0.125
