from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
import mujoco
import numpy as np
from PIL import Image, ImageDraw

from vi_full.env import PandaVariableImpedanceEnv, ResetConfig

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


@dataclass(frozen=True, slots=True)
class DemoClipSpec:
    name: str
    eval_label: str
    eval_seed: int
    expected_outcome: str


def build_default_demo_clip_specs() -> tuple[DemoClipSpec, ...]:
    return (
        DemoClipSpec(
            name="nominal_learned_success_seed10000",
            eval_label="nominal",
            eval_seed=10000,
            expected_outcome="success",
        ),
        DemoClipSpec(
            name="stress_xy_learned_success_seed10001",
            eval_label="stress_xy",
            eval_seed=10001,
            expected_outcome="success",
        ),
        DemoClipSpec(
            name="stress_xy_learned_jam_seed10003",
            eval_label="stress_xy",
            eval_seed=10003,
            expected_outcome="jam",
        ),
    )


def build_demo_reset_configs() -> dict[str, ResetConfig]:
    return {
        "nominal": ResetConfig(),
        "stress_xy": ResetConfig(target_xy_noise_m=0.0030),
    }


def compose_demo_frame(
    scene_rgb: np.ndarray,
    wall_plot_rgb: np.ndarray,
    bottom_plot_rgb: np.ndarray,
) -> np.ndarray:
    if scene_rgb.ndim != 3 or wall_plot_rgb.ndim != 3 or bottom_plot_rgb.ndim != 3:
        raise ValueError("scene_rgb, wall_plot_rgb, and bottom_plot_rgb must be HxWx3 arrays")
    if scene_rgb.shape[2] != 3 or wall_plot_rgb.shape[2] != 3 or bottom_plot_rgb.shape[2] != 3:
        raise ValueError("scene_rgb, wall_plot_rgb, and bottom_plot_rgb must have 3 channels")

    right_height = wall_plot_rgb.shape[0] + bottom_plot_rgb.shape[0]
    right_width = max(wall_plot_rgb.shape[1], bottom_plot_rgb.shape[1])
    height = max(scene_rgb.shape[0], right_height)
    width = scene_rgb.shape[1] + right_width
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[: scene_rgb.shape[0], : scene_rgb.shape[1]] = scene_rgb
    right_x0 = scene_rgb.shape[1]
    canvas[: wall_plot_rgb.shape[0], right_x0 : right_x0 + wall_plot_rgb.shape[1]] = wall_plot_rgb
    bottom_y0 = wall_plot_rgb.shape[0]
    canvas[
        bottom_y0 : bottom_y0 + bottom_plot_rgb.shape[0],
        right_x0 : right_x0 + bottom_plot_rgb.shape[1],
    ] = bottom_plot_rgb
    return canvas


def _build_side_camera(target_position: np.ndarray) -> mujoco.MjvCamera:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = target_position
    camera.distance = 0.14
    camera.azimuth = 90.0
    camera.elevation = -20.0
    return camera


def compute_force_plot_ymax(
    force_history: list[float],
    *,
    floor_n: float = 50.0,
    ceiling_n: float = 700.0,
    headroom: float = 1.1,
) -> float:
    if not force_history:
        return floor_n
    peak_force = max(float(value) for value in force_history)
    return float(min(ceiling_n, max(floor_n, peak_force * headroom)))


def _render_scene_rgb(
    *,
    env: PandaVariableImpedanceEnv,
    renderer: mujoco.Renderer,
    camera: mujoco.MjvCamera,
) -> np.ndarray:
    renderer.update_scene(env.data, camera=camera)
    return np.asarray(renderer.render(), dtype=np.uint8)


def _render_force_plot_rgb(
    *,
    force_history: list[float],
    panel_title: str,
    force_label: str,
    line_color: str,
    height: int,
    width: int,
) -> np.ndarray:
    max_force_n = compute_force_plot_ymax(force_history)
    fig = plt.figure(figsize=(width / 100.0, height / 100.0), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_title(panel_title, fontsize=10)
    ax.set_xlabel("Step")
    ax.set_ylabel("Force (N)")
    ax.set_xlim(0, max(len(force_history) - 1, 1))
    ax.set_ylim(0.0, max_force_n)
    ax.grid(True, alpha=0.3)
    if force_history:
        x = np.arange(len(force_history), dtype=np.int32)
        y = np.asarray(force_history, dtype=np.float64)
        running_peak = np.maximum.accumulate(y)
        ax.plot(x, y, color=line_color, linewidth=3.0, label=force_label)
        ax.plot(x, running_peak, color="tab:blue", linewidth=2.0, linestyle="--", label="peak")
        ax.axvline(x[-1], color="black", linewidth=1.5, linestyle=":")
        ax.scatter([x[-1]], [y[-1]], color="black", s=24)
        ax.legend(loc="upper left", fontsize=8, frameon=True)
        ax.text(
            0.98,
            0.95,
            f"F={y[-1]:.1f} N\nPeak={running_peak[-1]:.1f} N",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
        )
    fig.tight_layout()
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba(), dtype=np.uint8)
    plt.close(fig)
    return rgba[:, :, :3].copy()


def _annotate_frame(frame_rgb: np.ndarray, lines: list[str]) -> np.ndarray:
    image = Image.fromarray(frame_rgb)
    draw = ImageDraw.Draw(image)
    x = 10
    y = 10
    for line in lines:
        draw.text((x, y), line, fill=(255, 255, 255))
        y += 14
    return np.asarray(image, dtype=np.uint8)


def record_predictor_demo_clip(
    *,
    env: PandaVariableImpedanceEnv,
    predictor,
    clip_spec: DemoClipSpec,
    output_path: Path,
    fps: int = 4,
    scene_height: int = 240,
    scene_width: int = 320,
    plot_width: int = 320,
    step_repeat: int = 3,
    final_hold_frames: int = 8,
) -> dict[str, object]:
    observation, _ = env.reset(seed=clip_spec.eval_seed)
    renderer = mujoco.Renderer(env.model, scene_height, scene_width)
    camera = _build_side_camera(env.target_position.copy())
    wall_force_history: list[float] = []
    bottom_force_history: list[float] = []
    frames: list[np.ndarray] = []

    terminated = False
    truncated = False
    final_info: dict[str, object] = {
        "is_success": False,
        "is_jammed": False,
        "peak_contact_force": 0.0,
        "contact_force_norm": 0.0,
        "wall_contact_force_norm": 0.0,
        "bottom_contact_force_norm": 0.0,
    }

    while not (terminated or truncated):
        action, _ = predictor.predict(observation, deterministic=True)
        observation, _, terminated, truncated, final_info = env.step(action)
        wall_force_history.append(float(final_info["wall_contact_force_norm"]))
        bottom_force_history.append(float(final_info["bottom_contact_force_norm"]))
        current_outcome = (
            "jam"
            if bool(final_info["is_jammed"])
            else "success"
            if bool(final_info["is_success"])
            else "running"
        )
        scene_rgb = _render_scene_rgb(env=env, renderer=renderer, camera=camera)
        panel_height = max(scene_rgb.shape[0] // 2, 1)
        wall_plot_rgb = _render_force_plot_rgb(
            force_history=wall_force_history,
            panel_title=f"{clip_spec.name} | {current_outcome} | wall force",
            force_label="wall",
            line_color="tab:orange",
            height=panel_height,
            width=plot_width,
        )
        bottom_plot_rgb = _render_force_plot_rgb(
            force_history=bottom_force_history,
            panel_title="bottom force",
            force_label="bottom",
            line_color="tab:green",
            height=scene_rgb.shape[0] - panel_height,
            width=plot_width,
        )
        frame = compose_demo_frame(scene_rgb, wall_plot_rgb, bottom_plot_rgb)
        frame = _annotate_frame(
            frame,
            [
                f"split={clip_spec.eval_label}",
                f"seed={clip_spec.eval_seed}",
                f"expected={clip_spec.expected_outcome}",
                f"step={len(wall_force_history)}",
            ],
        )
        frames.extend([frame] * max(step_repeat, 1))

    renderer.close()

    outcome = "jam" if bool(final_info["is_jammed"]) else "success" if bool(final_info["is_success"]) else "truncated"
    if frames:
        frames.extend([frames[-1]] * max(final_hold_frames, 0))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(output_path, frames, fps=fps, loop=0)
    return {
        "clip_name": clip_spec.name,
        "path": str(output_path),
        "eval_label": clip_spec.eval_label,
        "eval_seed": clip_spec.eval_seed,
        "expected_outcome": clip_spec.expected_outcome,
        "actual_outcome": outcome,
        "num_steps": len(wall_force_history),
        "is_success": bool(final_info["is_success"]),
        "is_jammed": bool(final_info["is_jammed"]),
        "peak_contact_force": float(final_info["peak_contact_force"]),
        "fps": fps,
    }
