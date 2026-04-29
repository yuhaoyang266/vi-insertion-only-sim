from __future__ import annotations

from vi_full.three_dof_benchmark import DEFAULT_UNCERTAINTY_PROFILES
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_motion_matched_main_protocol import (
    build_motion_matched_main_grid,
)


def test_motion_matched_main_grid_uses_main_benchmark_contract() -> None:
    grid = build_motion_matched_main_grid()

    assert [condition.name for condition in grid] == [
        "vi_full",
        "vi_motion_fi_k",
        "fi_motion_vi_k",
        "fi_full",
    ]
    assert {condition.seeds for condition in grid} == {tuple(range(5))}
    assert {condition.episodes_per_seed for condition in grid} == {100}
    assert {condition.profiles for condition in grid} == {DEFAULT_UNCERTAINTY_PROFILES}
    assert {condition.total_timesteps for condition in grid} == {128}
    assert {
        condition.max_episode_steps for condition in grid
    } == {DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps}

    suite_kwargs = {
        condition.name: condition.to_suite_run_kwargs()
        for condition in grid
    }
    assert suite_kwargs["vi_full"]["episodes_per_seed"] == 100
    assert suite_kwargs["vi_full"]["uncertainty_profiles"] == list(DEFAULT_UNCERTAINTY_PROFILES)
    assert suite_kwargs["vi_full"]["max_episode_steps"] == (
        DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps
    )
    assert suite_kwargs["fi_full"]["base_env_overrides"]["min_k_xy"] == (
        suite_kwargs["fi_full"]["fixed_stiffness_xy"]
    )
    assert "tuned_fi_k" not in suite_kwargs
