from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Sequence

from vi_full.three_dof_benchmark import DEFAULT_UNCERTAINTY_PROFILES
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_policies import ThreeDoFTeacherSpec, resolve_3dof_teacher_spec
from vi_full.three_dof_training import (
    FIXED_IMPEDANCE_K_XY,
    FIXED_IMPEDANCE_K_Z,
    build_3dof_fixed_impedance_env_overrides,
    build_3dof_fixed_impedance_env_overrides_for,
)


@dataclass(frozen=True, slots=True)
class TeacherCouplingCondition:
    name: str
    teacher_prior: str
    student_impedance_space: str
    teacher_preset_name: str
    teacher_spec: ThreeDoFTeacherSpec
    seeds: tuple[int, ...]
    total_timesteps: int
    bc_rollout_episodes: int = 32
    bc_pretrain_steps: int = 32
    bc_batch_size: int = 64
    train_uncertainty_profile: str = "nominal"
    eval_uncertainty_profile: str = "nominal"
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps
    motion_rule: str | None = None
    impedance_rule: str | None = None
    fixed_stiffness_xy: float | None = None
    fixed_stiffness_z: float | None = None

    def to_suite_run_kwargs(
        self,
        *,
        episodes: int,
        profiles: Sequence[str] = DEFAULT_UNCERTAINTY_PROFILES,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "suite_name": self.name,
            "seeds": list(self.seeds),
            "total_timesteps": int(self.total_timesteps),
            "episodes_per_seed": int(episodes),
            "max_episode_steps": int(self.max_episode_steps),
            "train_uncertainty_profile": self.train_uncertainty_profile,
            "eval_uncertainty_profile": self.eval_uncertainty_profile,
            "uncertainty_profiles": list(profiles),
            "bc_rollout_episodes": int(self.bc_rollout_episodes),
            "bc_pretrain_steps": int(self.bc_pretrain_steps),
            "bc_batch_size": int(self.bc_batch_size),
            "bc_demo_policy_name": self.teacher_preset_name,
            "bc_demo_teacher_spec": self.teacher_spec,
        }
        if self.motion_rule is not None:
            kwargs["motion_rule"] = self.motion_rule
        if self.impedance_rule is not None:
            kwargs["impedance_rule"] = self.impedance_rule
        if self.fixed_stiffness_xy is not None:
            kwargs["fixed_stiffness_xy"] = float(self.fixed_stiffness_xy)
        if self.fixed_stiffness_z is not None:
            kwargs["fixed_stiffness_z"] = float(self.fixed_stiffness_z)
        if self.student_impedance_space == "fixed_impedance":
            if self.fixed_stiffness_xy is None or self.fixed_stiffness_z is None:
                kwargs["base_env_overrides"] = build_3dof_fixed_impedance_env_overrides()
            else:
                kwargs["base_env_overrides"] = build_3dof_fixed_impedance_env_overrides_for(
                    k_xy=float(self.fixed_stiffness_xy),
                    k_z=float(self.fixed_stiffness_z),
                )
        return kwargs


def build_teacher_coupling_grid(
    seeds: Sequence[int] = (0, 1, 2),
    total_timesteps: int = 128,
) -> list[TeacherCouplingCondition]:
    vi_teacher = resolve_3dof_teacher_spec(policy_name="teacher_variable_variable")
    fi_teacher = resolve_3dof_teacher_spec(policy_name="teacher_pose_fixed")
    seed_tuple = tuple(int(seed) for seed in seeds)
    return [
        TeacherCouplingCondition(
            name="vi_teacher_vi_student",
            teacher_prior="variable_impedance",
            student_impedance_space="variable_impedance",
            teacher_preset_name="teacher_variable_variable",
            teacher_spec=vi_teacher,
            seeds=seed_tuple,
            total_timesteps=int(total_timesteps),
        ),
        TeacherCouplingCondition(
            name="vi_teacher_fi_student",
            teacher_prior="variable_impedance",
            student_impedance_space="fixed_impedance",
            teacher_preset_name="teacher_variable_variable",
            teacher_spec=vi_teacher,
            seeds=seed_tuple,
            total_timesteps=int(total_timesteps),
        ),
        TeacherCouplingCondition(
            name="fi_teacher_fi_student",
            teacher_prior="fixed_impedance",
            student_impedance_space="fixed_impedance",
            teacher_preset_name="teacher_pose_fixed",
            teacher_spec=fi_teacher,
            seeds=seed_tuple,
            total_timesteps=int(total_timesteps),
        ),
        TeacherCouplingCondition(
            name="fi_teacher_vi_student",
            teacher_prior="fixed_impedance",
            student_impedance_space="variable_impedance",
            teacher_preset_name="teacher_pose_fixed",
            teacher_spec=fi_teacher,
            seeds=seed_tuple,
            total_timesteps=int(total_timesteps),
        ),
    ]


def _motion_condition(
    *,
    name: str,
    teacher_prior: str,
    student_impedance_space: str,
    teacher_preset_name: str,
    seeds: tuple[int, ...],
    total_timesteps: int,
    fixed_stiffness_xy: float | None = None,
    fixed_stiffness_z: float | None = None,
) -> TeacherCouplingCondition:
    spec = resolve_3dof_teacher_spec(policy_name=teacher_preset_name)
    return TeacherCouplingCondition(
        name=name,
        teacher_prior=teacher_prior,
        student_impedance_space=student_impedance_space,
        teacher_preset_name=teacher_preset_name,
        teacher_spec=spec,
        seeds=seeds,
        total_timesteps=int(total_timesteps),
        motion_rule=spec.motion_rule,
        impedance_rule=spec.impedance_rule,
        fixed_stiffness_xy=fixed_stiffness_xy,
        fixed_stiffness_z=fixed_stiffness_z,
    )


def build_motion_matched_grid(
    seeds: Sequence[int] = (0, 1, 2),
    total_timesteps: int = 128,
) -> list[TeacherCouplingCondition]:
    seed_tuple = tuple(int(seed) for seed in seeds)
    return [
        _motion_condition(
            name="vi_full",
            teacher_prior="variable_impedance",
            student_impedance_space="variable_impedance",
            teacher_preset_name="teacher_variable_variable",
            seeds=seed_tuple,
            total_timesteps=total_timesteps,
        ),
        _motion_condition(
            name="fi_full",
            teacher_prior="fixed_impedance",
            student_impedance_space="fixed_impedance",
            teacher_preset_name="teacher_pose_fixed",
            seeds=seed_tuple,
            total_timesteps=total_timesteps,
            fixed_stiffness_xy=FIXED_IMPEDANCE_K_XY,
            fixed_stiffness_z=FIXED_IMPEDANCE_K_Z,
        ),
        _motion_condition(
            name="vi_motion_fi_k",
            teacher_prior="motion_matched",
            student_impedance_space="fixed_impedance",
            teacher_preset_name="teacher_variable_fixed",
            seeds=seed_tuple,
            total_timesteps=total_timesteps,
            fixed_stiffness_xy=FIXED_IMPEDANCE_K_XY,
            fixed_stiffness_z=FIXED_IMPEDANCE_K_Z,
        ),
        _motion_condition(
            name="fi_motion_vi_k",
            teacher_prior="motion_matched",
            student_impedance_space="variable_impedance",
            teacher_preset_name="teacher_pose_variable",
            seeds=seed_tuple,
            total_timesteps=total_timesteps,
        ),
        _motion_condition(
            name="tuned_fi_k",
            teacher_prior="fixed_impedance",
            student_impedance_space="fixed_impedance",
            teacher_preset_name="teacher_pose_fixed",
            seeds=seed_tuple,
            total_timesteps=total_timesteps,
            fixed_stiffness_xy=0.6,
            fixed_stiffness_z=0.6,
        ),
    ]


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _metric(source: dict[str, Any], name: str, default: float = 0.0) -> float:
    return float(source.get(name, default))


def summarize_teacher_coupling_results(report: dict[str, Any]) -> dict[str, Any]:
    conditions: list[dict[str, Any]] = []
    for condition_name, payload in report.get("learned_results", {}).items():
        five_profile_mean = dict(payload.get("five_profile_mean", {}))
        support_metrics = dict(payload.get("support_metrics", {}))
        conditions.append(
            {
                "condition_name": condition_name,
                "teacher_prior": payload.get("teacher_prior"),
                "student_impedance_space": payload.get("student_impedance_space"),
                "teacher_motion_rule": payload.get("teacher_motion_rule"),
                "teacher_impedance_rule": payload.get("teacher_impedance_rule"),
                "success_rate": _metric(five_profile_mean, "success_rate_mean_over_profiles"),
                "jam_rate": _metric(five_profile_mean, "jam_rate_mean_over_profiles"),
                "mean_final_distance_mm": 1000.0
                * _metric(five_profile_mean, "mean_final_distance_mean_over_profiles"),
                "mean_peak_contact_force_n": _metric(
                    five_profile_mean,
                    "mean_peak_contact_force_mean_over_profiles",
                ),
                "mean_contact_steps": _metric(
                    five_profile_mean,
                    "mean_contact_steps_mean_over_profiles",
                ),
                "support_coverage_index": _metric(
                    support_metrics,
                    "support_coverage_index_mean_over_profiles",
                ),
                "support_cell_coverage": _metric(
                    support_metrics,
                    "support_cell_coverage_mean_over_profiles",
                ),
            }
        )
    return {
        "condition_count": len(conditions),
        "conditions": conditions,
        "gate": "Gate A: retain VI superiority language only if FI-teacher and motion-matched controls support it.",
    }


def teacher_coupling_report_payload(
    *,
    learned_results: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    report = {
        "artifact_schema_version": 1,
        "ablation_name": config.get("ablation_name", "teacher_coupling_crossed_ablation"),
        "config": config,
        "learned_results": learned_results,
    }
    report["summary"] = summarize_teacher_coupling_results(report)
    return _json_safe(report)
