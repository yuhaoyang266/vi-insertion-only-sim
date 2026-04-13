from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import gymnasium_robotics


@dataclass(frozen=True, slots=True)
class FrankaAssetBundle:
    bundle_root: Path
    franka_assets_dir: Path
    assets_xml: Path
    basic_scene_xml: Path
    chain_xml: Path
    actuator_xml: Path


def resolve_franka_asset_bundle() -> FrankaAssetBundle:
    package_root = Path(gymnasium_robotics.__file__).resolve().parent
    bundle_root = package_root / "envs" / "assets" / "kitchen_franka"
    franka_assets_dir = bundle_root / "franka_assets"
    assets_xml = franka_assets_dir / "assets.xml"
    basic_scene_xml = franka_assets_dir / "basic_scene.xml"
    chain_xml = franka_assets_dir / "chain.xml"
    actuator_xml = franka_assets_dir / "actuator.xml"
    return FrankaAssetBundle(
        bundle_root=bundle_root,
        franka_assets_dir=franka_assets_dir,
        assets_xml=assets_xml,
        basic_scene_xml=basic_scene_xml,
        chain_xml=chain_xml,
        actuator_xml=actuator_xml,
    )
