from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from vi_full.three_dof_config import ThreeDoFInsertionConfig
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_profiles import build_3dof_profile_config


ALT_CONTACT_MODEL_NAME = "within_a_soft_wall_contact_cross_check"
ALT_CONTACT_MODEL_CHANGED_FIELDS = (
    "contact_xy_scale",
    "contact_z_scale",
    "in_hole_drag_scale",
    "contact_transition_band_m",
)


@dataclass(frozen=True, slots=True)
class AltContactModelSpec:
    name: str
    claim_scope: str
    base_profile: str
    changed_fields: tuple[str, ...]
    config: ThreeDoFInsertionConfig


def build_alt_contact_model_config(
    profile_name: str = "nominal",
    *,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
) -> ThreeDoFInsertionConfig:
    base = build_3dof_profile_config(
        profile_name,
        max_episode_steps=max_episode_steps,
    )
    return replace(
        base,
        contact_xy_scale=base.contact_xy_scale * 0.85,
        contact_z_scale=base.contact_z_scale * 1.15,
        in_hole_drag_scale=base.in_hole_drag_scale * 1.10,
        contact_transition_band_m=base.contact_transition_band_m * 1.25,
    )


def build_alt_contact_model_spec(
    profile_name: str = "nominal",
    *,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
) -> AltContactModelSpec:
    return AltContactModelSpec(
        name=ALT_CONTACT_MODEL_NAME,
        claim_scope=(
            "within-A fallback contact-law cross-check; not a second-simulator or "
            "hardware-validity claim"
        ),
        base_profile=profile_name,
        changed_fields=ALT_CONTACT_MODEL_CHANGED_FIELDS,
        config=build_alt_contact_model_config(
            profile_name,
            max_episode_steps=max_episode_steps,
        ),
    )


def summarize_alt_contact_model_spec(
    spec: AltContactModelSpec,
) -> dict[str, Any]:
    base = build_3dof_profile_config(
        spec.base_profile,
        max_episode_steps=spec.config.max_episode_steps,
    )
    return {
        "name": spec.name,
        "claim_scope": spec.claim_scope,
        "base_profile": spec.base_profile,
        "changed_fields": list(spec.changed_fields),
        "invariant_fields": [
            "action_dim",
            "observation_dim",
            "success_lateral_tolerance_m",
            "success_axial_tolerance_m",
            "jam_force_threshold_n",
            "jam_persistence_steps",
            "max_episode_steps",
        ],
        "field_deltas": {
            field: {
                "base": getattr(base, field),
                "alternative": getattr(spec.config, field),
            }
            for field in spec.changed_fields
        },
    }
