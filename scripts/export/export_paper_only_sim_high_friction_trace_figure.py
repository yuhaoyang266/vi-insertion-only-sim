from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vi_full.three_dof_benchmark import (  # noqa: E402
    CONTACT_THRESHOLD_N,
    build_3dof_dapg_baseline_registry,
    trace_3dof_policy_rollout,
    trace_3dof_predictor_rollout,
)
from vi_full.three_dof_env import ThreeDoFInsertionEnv  # noqa: E402
from vi_full.three_dof_policies import (  # noqa: E402
    ThreeDoFFixedImpedancePolicy,
    ThreeDoFVariableImpedancePolicy,
)
from vi_full.three_dof_profiles import build_3dof_profile_config  # noqa: E402
from vi_full.three_dof_training import (  # noqa: E402
    build_3dof_mainline_train_config,
    train_3dof_ppo_agent,
)
from vi_full.training import VecNormalizePredictor  # noqa: E402


SUITE_SPECS = {
    "learned_fixed": {
        "display_name": "Learned fixed",
        "color": "#C0504D",
        "kind": "learned",
        "source_suite_name": "fixed_impedance_rl_stable_r32_p32",
    },
    "learned_variable": {
        "display_name": "Learned variable",
        "color": "#4F81BD",
        "kind": "learned",
        "source_suite_name": "repaired_mainline_bc_to_ppo",
    },
    "handcrafted_fixed": {
        "display_name": "Handcrafted fixed",
        "color": "#DD8452",
        "kind": "handcrafted",
        "policy_factory": ThreeDoFFixedImpedancePolicy,
    },
    "handcrafted_variable": {
        "display_name": "Handcrafted variable",
        "color": "#55A868",
        "kind": "handcrafted",
        "policy_factory": ThreeDoFVariableImpedancePolicy,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the high-friction direct mechanics trace figure for the only-sim paper."
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--trace-episodes-per-seed", type=int, default=50)
    parser.add_argument("--timesteps", type=int, default=128)
    parser.add_argument("--max-episode-steps", type=int, default=64)
    parser.add_argument(
        "--train-profile",
        type=str,
        default="nominal",
        help="Training profile for the learned suites.",
    )
    parser.add_argument(
        "--eval-profile",
        type=str,
        default="high_friction",
        help="Evaluation profile used for the direct mechanics traces.",
    )
    parser.add_argument(
        "--trace-output",
        type=Path,
        default=Path("outputs/latest_three_dof_high_friction_direct_mechanics_trace.json"),
        help="Path for the raw trace JSON export.",
    )
    parser.add_argument(
        "--figure-output-dir",
        type=Path,
        default=Path("outputs/paper_only_sim_figures"),
        help="Directory for the exported figure files.",
    )
    parser.add_argument(
        "--figure-stem",
        type=str,
        default="fig3_high_friction_impedance_mechanism",
        help="Canonical output filename stem.",
    )
    parser.add_argument(
        "--interpolation-points",
        type=int,
        default=120,
        help="Number of normalized contact-phase points used for aggregation.",
    )
    return parser.parse_args()


def _suite_train_config(
    source_suite_name: str,
    *,
    seed: int,
    total_timesteps: int,
    max_episode_steps: int,
    train_profile: str,
    eval_profile: str,
) -> Any:
    registry = build_3dof_dapg_baseline_registry()
    suite_kwargs = dict(registry[source_suite_name])
    suite_timesteps = int(suite_kwargs.pop("total_timesteps", total_timesteps))
    bc_rollout_episodes = int(suite_kwargs.pop("bc_rollout_episodes", 8))
    bc_pretrain_steps = int(suite_kwargs.pop("bc_pretrain_steps", 32))
    bc_batch_size = int(suite_kwargs.pop("bc_batch_size", 64))
    base_env_overrides = dict(suite_kwargs.pop("base_env_overrides", {}) or {})
    train_reset_config = suite_kwargs.pop("train_reset_config", None)
    bc_reset_config = suite_kwargs.pop("bc_reset_config", None)
    dapg_enabled = bool(suite_kwargs.pop("dapg_enabled", False))
    dapg_mini_updates_per_chunk = int(suite_kwargs.pop("dapg_mini_updates_per_chunk", 1))
    dapg_demo_batch_size = int(suite_kwargs.pop("dapg_demo_batch_size", 64))
    if suite_kwargs:
        unresolved = ", ".join(sorted(suite_kwargs.keys()))
        raise ValueError(
            f"Unhandled suite kwargs for {source_suite_name}: {unresolved}"
        )

    config = build_3dof_mainline_train_config(
        seed=seed,
        total_timesteps=suite_timesteps,
        max_episode_steps=max_episode_steps,
        train_uncertainty_profile=train_profile,
        eval_uncertainty_profile=eval_profile,
        n_envs=1,
        n_steps=min(64, max(suite_timesteps, 16)),
        batch_size=min(64, max(suite_timesteps, 16)),
        n_epochs=1,
        learning_rate=1e-4,
        gamma=0.95,
        verbose=0,
        bc_rollout_episodes=bc_rollout_episodes,
        bc_pretrain_steps=bc_pretrain_steps,
        bc_batch_size=bc_batch_size,
        bc_demo_policy_name="variable_impedance",
    )
    return replace(
        config,
        base_env_overrides=base_env_overrides,
        train_reset_config=(
            train_reset_config if train_reset_config is not None else config.train_reset_config
        ),
        bc_reset_config=bc_reset_config if bc_reset_config is not None else config.bc_reset_config,
        dapg_enabled=dapg_enabled,
        dapg_mini_updates_per_chunk=dapg_mini_updates_per_chunk,
        dapg_demo_batch_size=dapg_demo_batch_size,
    )


def _build_trace_run_record(
    *,
    train_seed: int | None,
    trace_episode_index: int,
    rollout_seed: int,
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    final_step = trace[-1]
    return {
        "train_seed": train_seed,
        "trace_episode_index": trace_episode_index,
        "rollout_seed": rollout_seed,
        "num_steps": len(trace),
        "is_success": bool(final_step["is_success"]),
        "is_jammed": bool(final_step["is_jammed"]),
        "trace": trace,
    }


def _collect_learned_suite_traces(
    suite_key: str,
    *,
    seeds: list[int],
    trace_episodes_per_seed: int,
    total_timesteps: int,
    max_episode_steps: int,
    train_profile: str,
    eval_profile: str,
) -> dict[str, Any]:
    suite_spec = SUITE_SPECS[suite_key]
    source_suite_name = str(suite_spec["source_suite_name"])
    trace_runs: list[dict[str, Any]] = []
    for seed in seeds:
        train_config = _suite_train_config(
            source_suite_name,
            seed=seed,
            total_timesteps=total_timesteps,
            max_episode_steps=max_episode_steps,
            train_profile=train_profile,
            eval_profile=eval_profile,
        )
        artifacts = train_3dof_ppo_agent(train_config)
        predictor = VecNormalizePredictor(
            model=artifacts.model,
            vec_normalize=artifacts.vec_normalize,
        )
        try:
            for trace_episode_index in range(trace_episodes_per_seed):
                rollout_seed = seed + 10_000 + trace_episode_index
                env = artifacts.make_eval_env(uncertainty_profile=eval_profile)
                try:
                    trace = trace_3dof_predictor_rollout(
                        env,
                        predictor,
                        seed=rollout_seed,
                    )
                finally:
                    env.close()
                trace_runs.append(
                    _build_trace_run_record(
                        train_seed=seed,
                        trace_episode_index=trace_episode_index,
                        rollout_seed=rollout_seed,
                        trace=trace,
                    )
                )
        finally:
            artifacts.vec_normalize.close()
    return {
        "suite_name": suite_key,
        "display_name": suite_spec["display_name"],
        "kind": suite_spec["kind"],
        "source_suite_name": source_suite_name,
        "train_profile": train_profile,
        "eval_profile": eval_profile,
        "trace_runs": trace_runs,
    }


def _collect_handcrafted_suite_traces(
    suite_key: str,
    *,
    seeds: list[int],
    trace_episodes_per_seed: int,
    max_episode_steps: int,
    eval_profile: str,
) -> dict[str, Any]:
    suite_spec = SUITE_SPECS[suite_key]
    policy = suite_spec["policy_factory"]()
    config = build_3dof_profile_config(
        eval_profile,
        max_episode_steps=max_episode_steps,
    )
    trace_runs: list[dict[str, Any]] = []
    env = ThreeDoFInsertionEnv(config)
    try:
        for seed in seeds:
            for trace_episode_index in range(trace_episodes_per_seed):
                rollout_seed = seed + 10_000 + trace_episode_index
                trace = trace_3dof_policy_rollout(
                    env,
                    policy,
                    seed=rollout_seed,
                )
                trace_runs.append(
                    _build_trace_run_record(
                        train_seed=None,
                        trace_episode_index=trace_episode_index,
                        rollout_seed=rollout_seed,
                        trace=trace,
                    )
                )
    finally:
        env.close()
    return {
        "suite_name": suite_key,
        "display_name": suite_spec["display_name"],
        "kind": suite_spec["kind"],
        "policy_name": policy.name,
        "train_profile": None,
        "eval_profile": eval_profile,
        "trace_runs": trace_runs,
    }


def _contact_segment(trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
    onset_index = 0
    for idx, step in enumerate(trace):
        if float(step["contact_force_norm"]) > CONTACT_THRESHOLD_N:
            onset_index = idx
            break
    segment = trace[onset_index:]
    return segment if segment else trace


def _interp_trace_channel(trace: list[dict[str, Any]], key: str, num_points: int, scale: float = 1.0) -> np.ndarray:
    segment = _contact_segment(trace)
    values = np.asarray([float(step[key]) * scale for step in segment], dtype=np.float64)
    if values.size == 0:
        return np.zeros(num_points, dtype=np.float64)
    if values.size == 1:
        return np.full(num_points, float(values[0]), dtype=np.float64)
    source_x = np.linspace(0.0, 1.0, num=values.size, dtype=np.float64)
    target_x = np.linspace(0.0, 1.0, num=num_points, dtype=np.float64)
    return np.interp(target_x, source_x, values)


def _stack_trace_channel(
    trace_runs: list[dict[str, Any]],
    key: str,
    num_points: int,
    *,
    scale: float = 1.0,
) -> np.ndarray:
    return np.stack(
        [
            _interp_trace_channel(run["trace"], key, num_points, scale=scale)
            for run in trace_runs
        ],
        axis=0,
    )


def _mean_std_payload(values: np.ndarray) -> dict[str, list[float]]:
    return {
        "mean": np.mean(values, axis=0).tolist(),
        "std": np.std(values, axis=0).tolist(),
    }


def _aggregate_suite_traces(
    trace_runs: list[dict[str, Any]],
    num_points: int,
    *,
    successful_only: bool,
) -> dict[str, Any] | None:
    runs_for_curves = [
        run for run in trace_runs if (not successful_only or bool(run["is_success"]))
    ]
    if not runs_for_curves:
        return None

    insertion_depth = _stack_trace_channel(
        runs_for_curves,
        "insertion_depth",
        num_points,
        scale=1000.0,
    )
    contact_force = _stack_trace_channel(runs_for_curves, "contact_force_norm", num_points)
    wall_force = _stack_trace_channel(
        runs_for_curves,
        "wall_contact_force_norm",
        num_points,
    )
    bottom_force = _stack_trace_channel(
        runs_for_curves,
        "bottom_contact_force_norm",
        num_points,
    )
    approx_normal_force = _stack_trace_channel(
        runs_for_curves,
        "approx_normal_force_norm",
        num_points,
    )
    approx_tangential_force = _stack_trace_channel(
        runs_for_curves,
        "approx_tangential_force_norm",
        num_points,
    )
    decoded_k_xy = _stack_trace_channel(runs_for_curves, "decoded_k_xy", num_points)
    decoded_k_z = _stack_trace_channel(runs_for_curves, "decoded_k_z", num_points)
    cumulative_contact_work = _stack_trace_channel(
        runs_for_curves,
        "cumulative_contact_work",
        num_points,
    )
    cumulative_contact_impulse = _stack_trace_channel(
        runs_for_curves,
        "cumulative_contact_impulse",
        num_points,
    )
    normalized_contact_step = np.linspace(0.0, 1.0, num=num_points, dtype=np.float64)
    success_flags = np.asarray([bool(run["is_success"]) for run in trace_runs], dtype=np.float64)
    jam_flags = np.asarray([bool(run["is_jammed"]) for run in trace_runs], dtype=np.float64)
    return {
        "curve_basis": "successful_only" if successful_only else "all_traces",
        "normalized_contact_step": normalized_contact_step.tolist(),
        "trace_count_total": int(len(trace_runs)),
        "trace_count_successful": int(sum(bool(run["is_success"]) for run in trace_runs)),
        "trace_count_failed": int(sum(not bool(run["is_success"]) for run in trace_runs)),
        "trace_count_used_for_curves": int(len(runs_for_curves)),
        "success_rate_over_traces": float(np.mean(success_flags)) if trace_runs else 0.0,
        "jam_rate_over_traces": float(np.mean(jam_flags)) if trace_runs else 0.0,
        "insertion_depth_mm": _mean_std_payload(insertion_depth),
        "contact_force_norm": _mean_std_payload(contact_force),
        "wall_contact_force_norm": _mean_std_payload(wall_force),
        "bottom_contact_force_norm": _mean_std_payload(bottom_force),
        "approx_normal_force_norm": _mean_std_payload(approx_normal_force),
        "approx_tangential_force_norm": _mean_std_payload(approx_tangential_force),
        "decoded_k_xy": _mean_std_payload(decoded_k_xy),
        "decoded_k_z": _mean_std_payload(decoded_k_z),
        "cumulative_contact_work": _mean_std_payload(cumulative_contact_work),
        "cumulative_contact_impulse": _mean_std_payload(cumulative_contact_impulse),
    }


def _render_trace_panel(ax, x: np.ndarray, y_mean: np.ndarray, y_std: np.ndarray, *, color: str, label: str, linestyle: str = "-", alpha_fill: float = 0.16) -> None:
    ax.plot(x, y_mean, color=color, linewidth=2.2, linestyle=linestyle, label=label)
    ax.fill_between(
        x,
        y_mean - y_std,
        y_mean + y_std,
        color=color,
        alpha=alpha_fill,
        linewidth=0.0,
    )


def _aggregation_counts_text(
    trace_payload: dict[str, Any],
    aggregation_key: str,
) -> str:
    lines = [f"aggregation: {aggregation_key.replace('_', ' ')}"]
    for suite_key, suite_payload in trace_payload["suite_summaries"].items():
        aggregation = suite_payload["aggregations"].get(aggregation_key)
        if aggregation is None:
            lines.append(
                f"{SUITE_SPECS[suite_key]['display_name']}: 0/"
                f"{len(suite_payload['trace_runs'])} used"
            )
            continue
        lines.append(
            f"{suite_payload['display_name']}: "
            f"{aggregation['trace_count_used_for_curves']}/"
            f"{aggregation['trace_count_total']} used | "
            f"success {aggregation['success_rate_over_traces']:.2f}"
        )
    return "\n".join(lines)


def _render_direct_mechanics_figure(
    trace_payload: dict[str, Any],
    output_dir: Path,
    stem: str,
    *,
    aggregation_key: str,
    title_suffix: str,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    suite_summaries = trace_payload["suite_summaries"]
    reference_aggregation = None
    for suite_payload in suite_summaries.values():
        reference_aggregation = suite_payload["aggregations"].get(aggregation_key)
        if reference_aggregation is not None:
            break
    if reference_aggregation is None:
        raise ValueError(f"No aggregation data available for {aggregation_key}")
    x = np.asarray(reference_aggregation["normalized_contact_step"], dtype=np.float64)

    fig, axes = plt.subplots(2, 2, figsize=(12.4, 8.0), constrained_layout=True, sharex=True)
    axes = axes.reshape(2, 2)

    for suite_key, suite_payload in suite_summaries.items():
        aggregation = suite_payload["aggregations"].get(aggregation_key)
        if aggregation is None:
            continue
        color = str(SUITE_SPECS[suite_key]["color"])
        display_name = str(suite_payload["display_name"])

        _render_trace_panel(
            axes[0, 0],
            x,
            np.asarray(aggregation["insertion_depth_mm"]["mean"], dtype=np.float64),
            np.asarray(aggregation["insertion_depth_mm"]["std"], dtype=np.float64),
            color=color,
            label=display_name,
            alpha_fill=0.12,
        )

        _render_trace_panel(
            axes[0, 1],
            x,
            np.asarray(aggregation["contact_force_norm"]["mean"], dtype=np.float64),
            np.asarray(aggregation["contact_force_norm"]["std"], dtype=np.float64),
            color=color,
            label=f"{display_name} total",
            linestyle="-",
            alpha_fill=0.08,
        )
        axes[0, 1].plot(
            x,
            np.asarray(aggregation["wall_contact_force_norm"]["mean"], dtype=np.float64),
            color=color,
            linestyle="--",
            linewidth=1.8,
            alpha=0.95,
        )
        axes[0, 1].plot(
            x,
            np.asarray(aggregation["bottom_contact_force_norm"]["mean"], dtype=np.float64),
            color=color,
            linestyle=":",
            linewidth=1.8,
            alpha=0.95,
        )

        _render_trace_panel(
            axes[1, 0],
            x,
            np.asarray(aggregation["decoded_k_xy"]["mean"], dtype=np.float64),
            np.asarray(aggregation["decoded_k_xy"]["std"], dtype=np.float64),
            color=color,
            label=f"{display_name} $K_{{xy}}$",
            linestyle="-",
            alpha_fill=0.08,
        )
        _render_trace_panel(
            axes[1, 0],
            x,
            np.asarray(aggregation["decoded_k_z"]["mean"], dtype=np.float64),
            np.asarray(aggregation["decoded_k_z"]["std"], dtype=np.float64),
            color=color,
            label=f"{display_name} $K_z$",
            linestyle="--",
            alpha_fill=0.05,
        )

        _render_trace_panel(
            axes[1, 1],
            x,
            np.asarray(aggregation["cumulative_contact_work"]["mean"], dtype=np.float64),
            np.asarray(aggregation["cumulative_contact_work"]["std"], dtype=np.float64),
            color=color,
            label=display_name,
            alpha_fill=0.12,
        )

    axes[0, 0].set_title("Insertion depth / progress", fontsize=11.5, fontweight="bold", pad=9)
    axes[0, 0].set_ylabel("depth after contact onset (mm)")
    axes[0, 1].set_title("Total and decomposed force", fontsize=11.5, fontweight="bold", pad=9)
    axes[0, 1].set_ylabel("force (N)")
    axes[1, 0].set_title("Decoded stiffness schedule", fontsize=11.5, fontweight="bold", pad=9)
    axes[1, 0].set_ylabel("stiffness")
    axes[1, 1].set_title("Cumulative contact work", fontsize=11.5, fontweight="bold", pad=9)
    axes[1, 1].set_ylabel("work (J, dissipative sign)")

    for ax in axes.flat:
        ax.set_xlim(0.0, 1.0)
        ax.set_xlabel("normalized contact step")
        ax.grid(color="#DDDDDD", linewidth=0.8)
        ax.set_axisbelow(True)

    suite_handles = [
        Line2D(
            [0],
            [0],
            color=str(spec["color"]),
            linewidth=2.2,
            label=str(spec["display_name"]),
        )
        for spec in SUITE_SPECS.values()
    ]
    force_style_handles = [
        Line2D([0], [0], color="#555555", linewidth=2.0, linestyle="-", label="total"),
        Line2D([0], [0], color="#555555", linewidth=2.0, linestyle="--", label="wall"),
        Line2D([0], [0], color="#555555", linewidth=2.0, linestyle=":", label="bottom"),
    ]
    stiffness_style_handles = [
        Line2D([0], [0], color="#555555", linewidth=2.0, linestyle="-", label="$K_{xy}$"),
        Line2D([0], [0], color="#555555", linewidth=2.0, linestyle="--", label="$K_z$"),
    ]
    axes[0, 0].legend(handles=suite_handles, loc="upper left", frameon=False, fontsize=8.5)
    axes[0, 1].legend(handles=force_style_handles, loc="upper left", frameon=False, fontsize=8.5)
    axes[1, 0].legend(handles=stiffness_style_handles, loc="upper right", frameon=False, fontsize=8.5)
    axes[1, 1].text(
        0.98,
        0.95,
        _aggregation_counts_text(trace_payload, aggregation_key),
        ha="right",
        va="top",
        fontsize=8.3,
        transform=axes[1, 1].transAxes,
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#CCCCCC"},
    )

    fig.suptitle(
        f"High-friction direct mechanics traces ({title_suffix})",
        fontsize=13,
        fontweight="bold",
    )

    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def main() -> None:
    args = parse_args()
    suite_summaries: dict[str, Any] = {}
    for suite_key, suite_spec in SUITE_SPECS.items():
        if suite_spec["kind"] == "learned":
            suite_payload = _collect_learned_suite_traces(
                suite_key,
                seeds=args.seeds,
                trace_episodes_per_seed=args.trace_episodes_per_seed,
                total_timesteps=args.timesteps,
                max_episode_steps=args.max_episode_steps,
                train_profile=args.train_profile,
                eval_profile=args.eval_profile,
            )
        else:
            suite_payload = _collect_handcrafted_suite_traces(
                suite_key,
                seeds=args.seeds,
                trace_episodes_per_seed=args.trace_episodes_per_seed,
                max_episode_steps=args.max_episode_steps,
                eval_profile=args.eval_profile,
            )
        suite_payload["aggregations"] = {
            "all_traces": _aggregate_suite_traces(
                suite_payload["trace_runs"],
                num_points=args.interpolation_points,
                successful_only=False,
            ),
            "successful_only": _aggregate_suite_traces(
                suite_payload["trace_runs"],
                num_points=args.interpolation_points,
                successful_only=True,
            ),
        }
        suite_summaries[suite_key] = suite_payload

    trace_payload = {
        "config": {
            "suite_names": list(suite_summaries.keys()),
            "display_names": {
                suite_name: payload["display_name"] for suite_name, payload in suite_summaries.items()
            },
            "seeds": args.seeds,
            "trace_episodes_per_seed": args.trace_episodes_per_seed,
            "timesteps": args.timesteps,
            "max_episode_steps": args.max_episode_steps,
            "train_profile": args.train_profile,
            "eval_profile": args.eval_profile,
            "contact_threshold_n": CONTACT_THRESHOLD_N,
            "interpolation_points": args.interpolation_points,
            "primary_aggregation": "all_traces",
            "secondary_aggregation": "successful_only",
        },
        "suite_summaries": suite_summaries,
    }

    args.trace_output.parent.mkdir(parents=True, exist_ok=True)
    args.trace_output.write_text(json.dumps(trace_payload, indent=2), encoding="utf-8")

    pdf_path, png_path = _render_direct_mechanics_figure(
        trace_payload,
        output_dir=args.figure_output_dir,
        stem=args.figure_stem,
        aggregation_key="all_traces",
        title_suffix="all traces",
    )
    secondary_paths: tuple[Path, Path] | None = None
    if any(
        suite_payload["aggregations"]["successful_only"] is not None
        for suite_payload in suite_summaries.values()
    ):
        secondary_paths = _render_direct_mechanics_figure(
            trace_payload,
            output_dir=args.figure_output_dir,
            stem=f"{args.figure_stem}_success_only",
            aggregation_key="successful_only",
            title_suffix="successful-only secondary view",
        )
    print(args.trace_output)
    print(pdf_path)
    print(png_path)
    if secondary_paths is not None:
        print(secondary_paths[0])
        print(secondary_paths[1])


if __name__ == "__main__":
    main()
