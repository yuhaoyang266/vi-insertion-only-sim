from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ThreeDoFResetStage:
    start_xy_noise_m: float = 0.0
    start_depth_fraction_range: tuple[float, float] = (0.0, 0.0)
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class ThreeDoFResetConfig:
    curriculum_stages: tuple[ThreeDoFResetStage, ...] = ()


@dataclass(frozen=True, slots=True)
class ThreeDoFInsertionConfig:
    action_dim: int = 5
    observation_dim: int = 14
    max_episode_steps: int = 80

    dt: float = 0.02
    step_scale_xy_m: float = 0.0012
    step_scale_z_m: float = 0.0010

    initial_height_m: float = 0.012
    initial_lateral_offset_m: float = 0.0035
    target_insertion_depth_m: float = 0.006

    success_lateral_tolerance_m: float = 0.0008
    success_axial_tolerance_m: float = 0.0010
    jam_force_threshold_n: float = 8.0
    jam_persistence_steps: int = 3

    workspace_xy_limit_m: float = 0.015
    workspace_z_min_m: float = -0.008
    workspace_z_max_m: float = 0.018

    min_k_xy: float = 20.0
    max_k_xy: float = 110.0
    min_k_z: float = 35.0
    max_k_z: float = 140.0

    hole_xy_offset_range_m: float = 0.0010
    wall_friction_range: tuple[float, float] = (0.12, 0.32)
    clearance_range_m: tuple[float, float] = (0.0007, 0.0011)
    force_noise_std_range: tuple[float, float] = (0.02, 0.12)
    pose_target_bias_xy_m: float = 0.0
    orientation_perturbation_deg: float = 0.0

    contact_xy_scale: float = 4200.0
    contact_z_scale: float = 3400.0
    in_hole_drag_scale: float = 120.0
    contact_transition_band_m: float = 0.001
    contact_transition_stiffness_aware_force_scaling: bool = False
    contact_transition_stiffness_aware_force_scaling_xy: bool = True
    contact_transition_stiffness_aware_force_scaling_z: bool = False
    contact_transition_stiffness_aware_force_scaling_z_axial: bool = True
    contact_transition_stiffness_aware_force_scaling_z_coupling: bool = False
    contact_transition_direct_axial_ramp_power: float = 0.0
    free_motion_damping: float = 0.22
    contact_lateral_relaxation: float = 0.18
    aligned_xy_threshold_m: float = 0.0015
    near_contact_height_m: float = 0.0025
    contact_reward_force_threshold_n: float = 0.05
    progress_reward_scale: float = 40.0
    force_penalty_scale: float = 0.06
    stability_penalty_scale: float = 0.12
    time_penalty: float = 0.02
    contact_bonus: float = 0.04
    enable_approach_alignment_projection: bool = False
    approach_alignment_trigger_height_m: float = 0.006
    approach_alignment_trigger_xy_threshold_m: float = 0.0015
    approach_alignment_max_xy_error_increase_m: float = 0.0
    enable_phase_conditioned_action_bias: bool = False
    phase_action_bias_trigger_height_m: float = 0.006
    phase_action_bias_trigger_xy_threshold_m: float = 0.0015
    phase_action_bias_dz_action: float = -0.2
    phase_action_bias_k_xy_action: float = 0.2
    phase_action_bias_k_z_action: float = 0.3
    phase_action_bias_mix: float = 0.35
    phase_action_bias_max_xy_error_increase_m: float = 0.0
    enable_contact_intent_projection: bool = False
    contact_intent_trigger_height_m: float = 0.0025
    contact_intent_trigger_xy_threshold_m: float = 0.0015
    contact_intent_min_z_action: float = -0.25
    contact_intent_min_k_xy_action: float = 0.2
    contact_intent_min_k_z_action: float = 0.4
    contact_intent_max_xy_error_increase_m: float = float("inf")
    approach_bonus_scale: float = 30.0
    insertion_bonus_scale: float = 20.0
    hover_penalty: float = 0.05
    reset_config: ThreeDoFResetConfig = field(default_factory=ThreeDoFResetConfig)

    def transition_stiffness_force_scaling_components(self) -> tuple[bool, bool, bool]:
        shared = self.contact_transition_stiffness_aware_force_scaling
        z_shared = bool(shared or self.contact_transition_stiffness_aware_force_scaling_z)
        return (
            bool(shared or self.contact_transition_stiffness_aware_force_scaling_xy),
            bool(z_shared or self.contact_transition_stiffness_aware_force_scaling_z_axial),
            bool(
                z_shared
                or self.contact_transition_stiffness_aware_force_scaling_z_coupling
            ),
        )

    def transition_stiffness_force_scaling_axes(self) -> tuple[bool, bool]:
        scale_xy, scale_z_axial, scale_z_coupling = (
            self.transition_stiffness_force_scaling_components()
        )
        return scale_xy, bool(scale_z_axial or scale_z_coupling)
