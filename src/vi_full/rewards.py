from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class RewardConfig:
    potential_tip_weight: float = 20.0
    potential_xy_weight: float = 30.0
    potential_base_weight: float = 10.0
    potential_depth_weight: float = 25.0
    soft_contact_force_limit: float = 20.0
    contact_force_weight: float = 0.01
    action_l2_weight: float = 0.01
    time_penalty: float = 0.02
    success_bonus: float = 15.0
    unused_step_bonus: float = 0.25
    jam_penalty: float = 5.0
    stall_progress_threshold: float = 1e-4
    stall_tip_distance_threshold: float = 0.02
    stall_penalty_weight: float = 0.2
    state_tip_weight: float = 0.5
    state_xy_weight: float = 1.0
    state_base_weight: float = 0.25
    state_depth_weight: float = 0.5
    guided_contact_force_threshold: float = 5.0
    guided_contact_xy_threshold: float = 0.01
    guided_contact_bonus: float = 1.0
    aligned_insertion_xy_threshold: float = 0.005
    aligned_insertion_contact_threshold: float = 5.0
    insertion_progress_bonus_weight: float = 2.0
    aligned_hover_xy_threshold: float = 0.003
    aligned_hover_z_threshold: float = 0.02
    aligned_hover_contact_threshold: float = 2.0
    aligned_hover_penalty_weight: float = 0.25
    aligned_drift_entry_xy_threshold: float = 0.003
    aligned_drift_tolerance: float = 5e-4
    aligned_drift_penalty_weight: float = 4.0


@dataclass(frozen=True, slots=True)
class RewardMetrics:
    tip_distance: float
    xy_distance: float
    z_distance: float
    base_distance: float
    insertion_depth: float
    contact_force_norm: float
    is_success: bool
    is_jammed: bool


@dataclass(frozen=True, slots=True)
class RewardBreakdown:
    progress_reward: float
    excess_force_penalty: float
    action_penalty: float
    time_penalty: float
    stall_penalty: float
    state_cost_penalty: float
    contact_bonus: float
    insertion_bonus: float
    hover_penalty: float
    drift_penalty: float
    success_bonus: float
    jam_penalty: float
    total_reward: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


class PPOInsertionReward:
    def __init__(self, config: RewardConfig | None = None) -> None:
        self.config = config or RewardConfig()

    def compute(
        self,
        *,
        previous_metrics: RewardMetrics,
        current_metrics: RewardMetrics,
        action_norm: float,
        remaining_steps: int,
        target_insertion_depth: float,
    ) -> RewardBreakdown:
        previous_potential = self._potential(previous_metrics, target_insertion_depth)
        current_potential = self._potential(current_metrics, target_insertion_depth)
        progress_reward = previous_potential - current_potential

        excess_force = max(
            0.0, current_metrics.contact_force_norm - self.config.soft_contact_force_limit
        )
        excess_force_penalty = -self.config.contact_force_weight * excess_force
        action_penalty = -self.config.action_l2_weight * float(action_norm**2)
        time_penalty = -self.config.time_penalty
        stall_penalty = 0.0
        if (
            abs(progress_reward) < self.config.stall_progress_threshold
            and current_metrics.tip_distance > self.config.stall_tip_distance_threshold
            and not current_metrics.is_success
        ):
            stall_penalty = -self.config.stall_penalty_weight
        contact_bonus = 0.0
        if (
            previous_metrics.contact_force_norm < self.config.guided_contact_force_threshold
            and current_metrics.contact_force_norm >= self.config.guided_contact_force_threshold
            and current_metrics.xy_distance <= self.config.guided_contact_xy_threshold
            and not current_metrics.is_jammed
            and not current_metrics.is_success
        ):
            alignment_ratio = 1.0 - (
                current_metrics.xy_distance / max(self.config.guided_contact_xy_threshold, 1e-6)
            )
            contact_bonus = self.config.guided_contact_bonus * max(alignment_ratio, 0.0)
        insertion_bonus = 0.0
        insertion_progress_delta = max(
            current_metrics.insertion_depth - previous_metrics.insertion_depth,
            0.0,
        )
        if (
            insertion_progress_delta > 0.0
            and current_metrics.xy_distance <= self.config.aligned_insertion_xy_threshold
            and current_metrics.contact_force_norm >= self.config.aligned_insertion_contact_threshold
            and not current_metrics.is_jammed
        ):
            insertion_bonus = self.config.insertion_progress_bonus_weight * (
                insertion_progress_delta / max(target_insertion_depth, 1e-6)
            )
        hover_penalty = 0.0
        if (
            current_metrics.xy_distance <= self.config.aligned_hover_xy_threshold
            and current_metrics.z_distance <= self.config.aligned_hover_z_threshold
            and current_metrics.contact_force_norm < self.config.aligned_hover_contact_threshold
            and insertion_progress_delta <= 1e-6
            and not current_metrics.is_success
        ):
            hover_penalty = -self.config.aligned_hover_penalty_weight
        drift_penalty = 0.0
        xy_drift = current_metrics.xy_distance - previous_metrics.xy_distance
        if (
            previous_metrics.xy_distance <= self.config.aligned_drift_entry_xy_threshold
            and xy_drift > self.config.aligned_drift_tolerance
            and not current_metrics.is_success
        ):
            drift_penalty = -self.config.aligned_drift_penalty_weight * xy_drift
        success_bonus = 0.0
        if current_metrics.is_success:
            success_bonus = self.config.success_bonus + self.config.unused_step_bonus * max(
                remaining_steps, 0
            )
        jam_penalty = -self.config.jam_penalty if current_metrics.is_jammed else 0.0
        state_cost_penalty = -(
            self.config.state_tip_weight * current_metrics.tip_distance
            + self.config.state_xy_weight * current_metrics.xy_distance
            + self.config.state_base_weight * current_metrics.base_distance
            + self.config.state_depth_weight
            * max(target_insertion_depth - current_metrics.insertion_depth, 0.0)
        )

        total_reward = (
            progress_reward
            + excess_force_penalty
            + action_penalty
            + time_penalty
            + stall_penalty
            + state_cost_penalty
            + contact_bonus
            + insertion_bonus
            + hover_penalty
            + drift_penalty
            + success_bonus
            + jam_penalty
        )
        return RewardBreakdown(
            progress_reward=progress_reward,
            excess_force_penalty=excess_force_penalty,
            action_penalty=action_penalty,
            time_penalty=time_penalty,
            stall_penalty=stall_penalty,
            state_cost_penalty=state_cost_penalty,
            contact_bonus=contact_bonus,
            insertion_bonus=insertion_bonus,
            hover_penalty=hover_penalty,
            drift_penalty=drift_penalty,
            success_bonus=success_bonus,
            jam_penalty=jam_penalty,
            total_reward=total_reward,
        )

    def _potential(self, metrics: RewardMetrics, target_insertion_depth: float) -> float:
        depth_remaining = max(target_insertion_depth - metrics.insertion_depth, 0.0)
        return (
            self.config.potential_tip_weight * metrics.tip_distance
            + self.config.potential_xy_weight * metrics.xy_distance
            + self.config.potential_base_weight * metrics.base_distance
            + self.config.potential_depth_weight * depth_remaining
        )
