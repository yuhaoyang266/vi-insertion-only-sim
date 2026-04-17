from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime
import hashlib
from pathlib import Path
from typing import Any

from vi_full.training import VecNormalizePredictor
from vi_full.three_dof_benchmark import (
    DEFAULT_UNCERTAINTY_PROFILES,
    THREE_DOF_NUMERIC_METRICS,
    build_3dof_dapg_baseline_registry,
    evaluate_3dof_predictor,
    run_3dof_handcrafted_uncertainty_suite,
    summarize_3dof_seed_runs,
)
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_policies import (
    build_3dof_teacher_metadata,
    build_3dof_handcrafted_policy_registry,
)
from vi_full.three_dof_training import (
    build_3dof_mainline_train_config,
    serialize_3dof_train_config,
    train_3dof_ppo_agent,
)

UNCERTAINTY_BENCHMARK_ARTIFACT_SCHEMA_VERSION = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the paper-facing 3DoF uncertainty benchmark."
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument(
        "--max-episode-steps",
        type=int,
        default=DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    )
    parser.add_argument("--include-learned", action="store_true")
    parser.add_argument("--include-paper-learned-block", action="store_true")
    parser.add_argument("--include-dapg-mechanism-block", action="store_true")
    parser.add_argument("--include-teacher-ablation-block", action="store_true")
    parser.add_argument("--timesteps", type=int, default=128)
    parser.add_argument("--train-profile", type=str, default="nominal")
    parser.add_argument("--eval-profile", type=str, default="nominal")
    parser.add_argument("--bc-rollout-episodes", type=int, default=32)
    parser.add_argument("--bc-pretrain-steps", type=int, default=32)
    parser.add_argument("--bc-batch-size", type=int, default=64)
    parser.add_argument("--bc-demo-policy-name", type=str, default="variable_impedance")
    parser.add_argument("--approach-bc-rollout-episodes", type=int, default=0)
    parser.add_argument("--approach-bc-pretrain-steps", type=int, default=0)
    parser.add_argument("--contact-bc-rollout-episodes", type=int, default=0)
    parser.add_argument("--contact-bc-pretrain-steps", type=int, default=0)
    parser.add_argument("--contact-bc-freeze-pose-head", action="store_true")
    parser.add_argument("--contact-bc-after-finetune", action="store_true")
    parser.add_argument("--contact-finetune-timesteps", type=int, default=0)
    parser.add_argument("--contact-finetune-anchor-rollout-episodes", type=int, default=0)
    parser.add_argument("--contact-finetune-anchor-bc-steps", type=int, default=0)
    parser.add_argument("--contact-finetune-anchor-interval-timesteps", type=int, default=0)
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=list(DEFAULT_UNCERTAINTY_PROFILES),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional explicit output path for the benchmark JSON report.",
    )
    return parser.parse_args()


def _build_suite_run_kwargs(
    args: argparse.Namespace,
    *,
    suite_name: str,
    total_timesteps: int,
) -> dict[str, Any]:
    return {
        "suite_name": suite_name,
        "seeds": list(args.seeds),
        "total_timesteps": int(total_timesteps),
        "episodes_per_seed": int(args.episodes),
        "max_episode_steps": int(args.max_episode_steps),
        "train_uncertainty_profile": str(args.train_profile),
        "eval_uncertainty_profile": str(args.eval_profile),
        "uncertainty_profiles": list(args.profiles),
        "bc_rollout_episodes": int(args.bc_rollout_episodes),
        "bc_pretrain_steps": int(args.bc_pretrain_steps),
        "bc_batch_size": int(args.bc_batch_size),
        "bc_demo_policy_name": str(args.bc_demo_policy_name),
        "approach_bc_rollout_episodes": int(args.approach_bc_rollout_episodes),
        "approach_bc_pretrain_steps": int(args.approach_bc_pretrain_steps),
        "contact_bc_rollout_episodes": int(args.contact_bc_rollout_episodes),
        "contact_bc_pretrain_steps": int(args.contact_bc_pretrain_steps),
        "contact_bc_freeze_pose_head": bool(args.contact_bc_freeze_pose_head),
        "contact_bc_after_finetune": bool(args.contact_bc_after_finetune),
        "contact_finetune_timesteps": int(args.contact_finetune_timesteps),
        "contact_finetune_anchor_rollout_episodes": int(
            args.contact_finetune_anchor_rollout_episodes
        ),
        "contact_finetune_anchor_bc_steps": int(args.contact_finetune_anchor_bc_steps),
        "contact_finetune_anchor_interval_timesteps": int(
            args.contact_finetune_anchor_interval_timesteps
        ),
    }


def _build_run_signature(suite_run_kwargs: dict[str, Any]) -> str:
    signature_payload = json.dumps(
        {
            "artifact_schema_version": UNCERTAINTY_BENCHMARK_ARTIFACT_SCHEMA_VERSION,
            "suite_run_kwargs": _json_safe(suite_run_kwargs),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(signature_payload.encode("utf-8")).hexdigest()


def _suite_result_matches_signature(
    existing_suite_result: dict[str, Any],
    suite_run_kwargs: dict[str, Any],
) -> bool:
    return existing_suite_result.get("run_signature") == _build_run_signature(
        suite_run_kwargs
    )


def _build_teacher_metadata(suite_run_kwargs: dict[str, Any]) -> dict[str, Any]:
    return build_3dof_teacher_metadata(
        policy_name=str(suite_run_kwargs.get("bc_demo_policy_name", "variable_impedance")),
        teacher_spec=suite_run_kwargs.get("bc_demo_teacher_spec"),
    )


def _build_train_config(seed: int, suite_run_kwargs: dict[str, Any]) -> Any:
    total_timesteps = int(suite_run_kwargs["total_timesteps"])
    train_config = build_3dof_mainline_train_config(
        seed=seed,
        total_timesteps=total_timesteps,
        max_episode_steps=int(suite_run_kwargs["max_episode_steps"]),
        train_uncertainty_profile=str(suite_run_kwargs["train_uncertainty_profile"]),
        eval_uncertainty_profile=str(suite_run_kwargs["eval_uncertainty_profile"]),
        n_envs=1,
        n_steps=min(64, max(total_timesteps, 16)),
        batch_size=min(64, max(total_timesteps, 16)),
        n_epochs=1,
        learning_rate=1e-4,
        gamma=0.95,
        verbose=0,
        bc_rollout_episodes=int(suite_run_kwargs["bc_rollout_episodes"]),
        bc_pretrain_steps=int(suite_run_kwargs["bc_pretrain_steps"]),
        bc_batch_size=int(suite_run_kwargs["bc_batch_size"]),
        bc_demo_policy_name=str(suite_run_kwargs["bc_demo_policy_name"]),
        bc_demo_teacher_spec=suite_run_kwargs.get("bc_demo_teacher_spec"),
    )
    replace_kwargs: dict[str, Any] = {
        key: value
        for key, value in suite_run_kwargs.items()
        if key
        not in {
            "suite_name",
            "seeds",
            "total_timesteps",
            "episodes_per_seed",
            "max_episode_steps",
            "train_uncertainty_profile",
            "eval_uncertainty_profile",
            "uncertainty_profiles",
            "bc_rollout_episodes",
            "bc_pretrain_steps",
            "bc_batch_size",
            "bc_demo_policy_name",
            "bc_demo_teacher_spec",
        }
    }
    if "base_env_overrides" in replace_kwargs:
        replace_kwargs["base_env_overrides"] = dict(replace_kwargs["base_env_overrides"])
    return replace(train_config, **replace_kwargs)


def _build_five_profile_mean(eval_results: dict[str, Any]) -> dict[str, float]:
    summary: dict[str, float] = {}
    for metric_name in THREE_DOF_NUMERIC_METRICS:
        values = [
            float(payload["aggregate"][f"{metric_name}_mean"])
            for payload in eval_results.values()
        ]
        summary[f"{metric_name}_mean_over_profiles"] = float(sum(values) / len(values))
        mean_value = summary[f"{metric_name}_mean_over_profiles"]
        variance = sum((value - mean_value) ** 2 for value in values) / len(values)
        summary[f"{metric_name}_std_over_profiles"] = float(variance**0.5)
    return summary


def _run_3dof_suite_across_profiles(
    suite_run_kwargs: dict[str, Any],
) -> dict[str, Any]:
    run_signature = _build_run_signature(suite_run_kwargs)
    teacher_metadata = _build_teacher_metadata(suite_run_kwargs)
    eval_results: dict[str, dict[str, Any]] = {
        profile_name: {"per_seed": []}
        for profile_name in suite_run_kwargs["uncertainty_profiles"]
    }
    train_configs: list[dict[str, Any]] = []
    training_summaries: list[dict[str, Any]] = []

    for seed in suite_run_kwargs["seeds"]:
        train_config = _build_train_config(int(seed), suite_run_kwargs)
        artifacts = train_3dof_ppo_agent(train_config)
        predictor = VecNormalizePredictor(
            model=artifacts.model,
            vec_normalize=artifacts.vec_normalize,
        )
        train_configs.append(serialize_3dof_train_config(train_config))
        training_summary = {"seed": int(seed), **dict(artifacts.training_summary)}
        training_summaries.append(training_summary)

        try:
            for profile_index, profile_name in enumerate(
                suite_run_kwargs["uncertainty_profiles"]
            ):
                eval_seed = int(seed) + 10_000 + profile_index * 1_000
                env = artifacts.make_eval_env(
                    seed=eval_seed,
                    uncertainty_profile=profile_name,
                )
                try:
                    summary = evaluate_3dof_predictor(
                        env,
                        predictor,
                        episodes=int(suite_run_kwargs["episodes_per_seed"]),
                        seed=eval_seed,
                        uncertainty_profile=profile_name,
                    )
                finally:
                    env.close()
                summary["seed"] = int(seed)
                summary["training_summary"] = dict(artifacts.training_summary)
                eval_results[profile_name]["per_seed"].append(summary)
        finally:
            artifacts.vec_normalize.close()

    for profile_name, payload in eval_results.items():
        payload["aggregate"] = summarize_3dof_seed_runs(payload["per_seed"])
        payload["aggregate"]["suite_name"] = suite_run_kwargs["suite_name"]
        payload["aggregate"]["train_uncertainty_profile"] = suite_run_kwargs[
            "train_uncertainty_profile"
        ]
        payload["aggregate"]["eval_uncertainty_profile"] = profile_name
        payload["aggregate"].update(teacher_metadata)

    return {
        "run_signature": run_signature,
        **teacher_metadata,
        "suite_run_kwargs": {
            key: value
            for key, value in suite_run_kwargs.items()
            if key not in {"seeds", "episodes_per_seed", "uncertainty_profiles"}
        },
        "train_configs": train_configs,
        "training_summaries": training_summaries,
        "eval_results": eval_results,
        "five_profile_mean": _build_five_profile_mean(eval_results),
    }


def _default_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("outputs") / f"three_dof_benchmark_{timestamp}.json"


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _write_report(output_path: Path, report: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_output_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temp_output_path.write_text(
        json.dumps(_json_safe(report), indent=2),
        encoding="utf-8",
    )
    temp_output_path.replace(output_path)


def _load_existing_report(output_path: Path) -> dict[str, Any] | None:
    if not output_path.exists():
        return None
    return json.loads(output_path.read_text(encoding="utf-8"))


def _build_report_config(
    args: argparse.Namespace,
    *,
    suite_name_order: list[str],
) -> dict[str, Any]:
    return {
        "seeds": list(args.seeds),
        "episodes_per_seed": int(args.episodes),
        "max_episode_steps": int(args.max_episode_steps),
        "timesteps": int(args.timesteps),
        "uncertainty_profiles": list(args.profiles),
        "train_uncertainty_profile": str(args.train_profile),
        "base_bc_rollout_episodes": int(args.bc_rollout_episodes),
        "base_bc_pretrain_steps": int(args.bc_pretrain_steps),
        "base_bc_batch_size": int(args.bc_batch_size),
        "suite_names": suite_name_order,
        "handcrafted_policy_names": list(build_3dof_handcrafted_policy_registry().keys()),
        "artifact_schema_version": UNCERTAINTY_BENCHMARK_ARTIFACT_SCHEMA_VERSION,
        "benchmark_contract": asdict(DEFAULT_3DOF_BENCHMARK_CONTRACT),
    }


def main() -> None:
    args = parse_args()
    output_path = args.output if args.output is not None else _default_output_path()
    existing_report = _load_existing_report(output_path)
    handcrafted_results = run_3dof_handcrafted_uncertainty_suite(
        seeds=args.seeds,
        episodes_per_seed=args.episodes,
        max_episode_steps=args.max_episode_steps,
        uncertainty_profiles=args.profiles,
    )

    learned_results: dict[str, Any] = (
        dict(existing_report.get("learned_results", {})) if existing_report is not None else {}
    )
    suite_name_order: list[str] = (
        list(existing_report.get("config", {}).get("suite_names", []))
        if existing_report is not None
        else []
    )
    if args.include_learned:
        suite_name_parts = ["learned", "ppo", "3dof"]
        if args.bc_pretrain_steps > 0:
            suite_name_parts.append("bc")
        if args.approach_bc_pretrain_steps > 0:
            suite_name_parts.append("approach")
        if args.contact_bc_pretrain_steps > 0:
            suite_name_parts.append("contactbc")
        if args.contact_finetune_timesteps > 0:
            suite_name_parts.append("contact")
        if args.contact_finetune_anchor_bc_steps > 0:
            suite_name_parts.append("anchor")
        suite_name = "_".join(suite_name_parts)
        suite_run_kwargs = _build_suite_run_kwargs(
            args,
            suite_name=suite_name,
            total_timesteps=args.timesteps,
        )
        if suite_name not in suite_name_order:
            suite_name_order.append(suite_name)
        existing_suite_result = learned_results.get(suite_name)
        if existing_suite_result is None:
            print(f"running_suite {suite_name}", flush=True)
            learned_results[suite_name] = _run_3dof_suite_across_profiles(
                suite_run_kwargs
            )
            _write_report(
                output_path,
                {
                    "config": _build_report_config(args, suite_name_order=suite_name_order),
                    "handcrafted_results": handcrafted_results,
                    "learned_results": learned_results,
                },
            )
        elif _suite_result_matches_signature(existing_suite_result, suite_run_kwargs):
            print(f"skipping_suite {suite_name}", flush=True)
        else:
            print(f"rerunning_suite {suite_name}", flush=True)
            learned_results[suite_name] = _run_3dof_suite_across_profiles(
                suite_run_kwargs
            )
            _write_report(
                output_path,
                {
                    "config": _build_report_config(args, suite_name_order=suite_name_order),
                    "handcrafted_results": handcrafted_results,
                    "learned_results": learned_results,
                },
            )

    registry = build_3dof_dapg_baseline_registry()
    selected_registry_names: list[str] = []
    if args.include_paper_learned_block:
        selected_registry_names.extend(
            [
                "ppo_no_bc",
                "bc_only_stable_r32_p32",
                "fixed_impedance_rl_stable_r32_p32",
                "repaired_mainline_bc_to_ppo",
                "dapg_lite_repaired_mainline",
            ]
        )
    if args.include_dapg_mechanism_block:
        selected_registry_names.extend(
            [
                "dapg_lite_contact_old__reset_coverage_collapse",
                "dapg_lite_contact_old__reset_repaired",
                "dapg_lite_contact_new__reset_coverage_collapse",
                "dapg_lite_contact_new__reset_repaired",
            ]
        )
    if args.include_teacher_ablation_block:
        selected_registry_names.extend(
            [
                "teacher_variable_variable__repaired_mainline",
                "teacher_variable_fixed__repaired_mainline",
                "teacher_pose_variable__repaired_mainline",
                "teacher_pose_fixed__repaired_mainline",
            ]
        )

    for suite_name in dict.fromkeys(selected_registry_names):
        suite_kwargs = dict(registry[suite_name])
        total_timesteps = int(suite_kwargs.pop("total_timesteps", args.timesteps))
        suite_run_kwargs = _build_suite_run_kwargs(
            args,
            suite_name=suite_name,
            total_timesteps=total_timesteps,
        )
        suite_run_kwargs.update(suite_kwargs)
        if suite_name not in suite_name_order:
            suite_name_order.append(suite_name)
        existing_suite_result = learned_results.get(suite_name)
        if existing_suite_result is not None and _suite_result_matches_signature(
            existing_suite_result,
            suite_run_kwargs,
        ):
            print(f"skipping_suite {suite_name}", flush=True)
            continue
        action_label = (
            "rerunning_suite" if existing_suite_result is not None else "running_suite"
        )
        print(f"{action_label} {suite_name}", flush=True)
        learned_results[suite_name] = _run_3dof_suite_across_profiles(suite_run_kwargs)
        _write_report(
            output_path,
            {
                "config": _build_report_config(args, suite_name_order=suite_name_order),
                "handcrafted_results": handcrafted_results,
                "learned_results": learned_results,
            },
        )

    report = {
        "config": _build_report_config(args, suite_name_order=suite_name_order),
        "handcrafted_results": handcrafted_results,
        "learned_results": learned_results,
    }

    _write_report(output_path, report)

    print("benchmark_report", output_path)
    for suite_name in suite_name_order:
        five_profile_mean = learned_results[suite_name]["five_profile_mean"]
        print(
            suite_name,
            {
                "success_rate_mean_over_profiles": five_profile_mean[
                    "success_rate_mean_over_profiles"
                ],
                "jam_rate_mean_over_profiles": five_profile_mean[
                    "jam_rate_mean_over_profiles"
                ],
            },
        )


if __name__ == "__main__":
    main()
