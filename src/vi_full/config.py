from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActionSpec:
    names: tuple[str, ...] = ("dx", "dy", "dz", "k_xy", "k_z")

    @property
    def action_dim(self) -> int:
        return len(self.names)


@dataclass(frozen=True, slots=True)
class SystemConfig:
    robot_name: str = "franka_panda"
    algorithm_name: str = "ppo"
    random_seed: int = 42
    action_spec: ActionSpec = ActionSpec()

