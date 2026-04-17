from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ThreeDoFBenchmarkContract:
    max_episode_steps: int = 64
    jam_force_threshold_n: float = 8.0
    jam_persistence_steps: int = 3


DEFAULT_3DOF_BENCHMARK_CONTRACT = ThreeDoFBenchmarkContract()
