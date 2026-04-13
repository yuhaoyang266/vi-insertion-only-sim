from __future__ import annotations

import math
from pathlib import Path
import shutil
from uuid import uuid4

import mujoco

from vi_full.assets import FrankaAssetBundle


_FULL_SYSTEM_MODEL_CACHE: dict[str, mujoco.MjModel] = {}


def clear_full_system_model_cache() -> None:
    _FULL_SYSTEM_MODEL_CACHE.clear()


def build_panda_chain_with_peg_xml(bundle: FrankaAssetBundle) -> str:
    chain_xml = bundle.chain_xml.read_text(encoding="utf-8")
    peg_body = """                                    <body name="peg_tool" pos="0 0 0.210" euler="0 0 -0.785398">
                                        <site name="peg_base" pos="0 0 0" size="0.003" rgba="0 0 1 1"/>
                                        <geom name="peg_shaft" type="cylinder" pos="0 0 0.03" size="0.005 0.03" rgba="0.85 0.55 0.2 1"/>
                                        <site name="peg_tip" pos="0 0 0.06" size="0.003" rgba="1 0 0 1"/>
                                    </body>
"""
    insertion_anchor = '                                    <body name="panda0_leftfinger"'
    if insertion_anchor not in chain_xml:
        raise ValueError("Could not find Panda finger attachment point in chain.xml.")
    return chain_xml.replace(insertion_anchor, peg_body + insertion_anchor, 1)


def build_panda_probe_xml(bundle: FrankaAssetBundle) -> str:
    return """<mujoco model="panda_probe">
  <include file="franka_assets/assets.xml"/>
  <include file="franka_assets/basic_scene.xml"/>
  <worldbody>
    <body name="panda_root" pos="0 0 0">
      <include file="franka_assets/chain.xml"/>
    </body>
  </worldbody>
  <include file="franka_assets/actuator.xml"/>
</mujoco>
"""


def _materialize_local_bundle_copy(bundle: FrankaAssetBundle) -> FrankaAssetBundle:
    workspace_root = Path(__file__).resolve().parents[2]
    cache_root = workspace_root / ".cache" / "kitchen_franka"
    franka_assets_dir = cache_root / "franka_assets"
    if not franka_assets_dir.exists():
        shutil.copytree(bundle.bundle_root, cache_root, dirs_exist_ok=True)
    return FrankaAssetBundle(
        bundle_root=cache_root,
        franka_assets_dir=franka_assets_dir,
        assets_xml=franka_assets_dir / "assets.xml",
        basic_scene_xml=franka_assets_dir / "basic_scene.xml",
        chain_xml=franka_assets_dir / "chain.xml",
        actuator_xml=franka_assets_dir / "actuator.xml",
    )


def _build_socket_wall_xml() -> str:
    inner_radius = 0.006
    wall_half_thickness = 0.0012
    wall_half_length = inner_radius * math.tan(math.pi / 8.0) + 0.0006
    wall_half_height = 0.022
    wall_center_radius = inner_radius + wall_half_thickness
    wall_center_z = 0.032
    socket_walls: list[str] = []
    for wall_index in range(8):
        yaw = wall_index * (math.pi / 4.0)
        wall_x = wall_center_radius * math.cos(yaw)
        wall_y = wall_center_radius * math.sin(yaw)
        socket_walls.append(
            f'      <geom name="socket_wall_{wall_index}" type="box" '
            f'pos="{wall_x:.6f} {wall_y:.6f} {wall_center_z:.6f}" '
            f'euler="0 0 {yaw:.6f}" '
            f'size="{wall_half_thickness:.6f} {wall_half_length:.6f} {wall_half_height:.6f}" '
            'rgba="0.2 0.2 0.2 1"/>'
        )
    return "\n".join(socket_walls)


def build_full_system_xml(
    bundle: FrankaAssetBundle, chain_include_filename: str = "generated_chain_with_peg.xml"
) -> str:
    socket_wall_xml = _build_socket_wall_xml()
    return f"""<mujoco model="vi_full_system">
  <include file="franka_assets/assets.xml"/>
  <include file="franka_assets/basic_scene.xml"/>
  <worldbody>
    <geom name="insertion_table" type="box" pos="0.55 0.0 0.2" size="0.25 0.35 0.2" rgba="0.35 0.35 0.35 1"/>
    <body name="hole_block" pos="0.58 0.0 0.41">
      <geom name="base_plate" type="box" pos="0 0 0.01" size="0.04 0.04 0.01" rgba="0.25 0.25 0.25 1"/>
{socket_wall_xml}
      <site name="hole_target" pos="0 0 0.02" size="0.002" rgba="0 1 0 1"/>
      <site name="peg_approach" pos="0 0 0.08" size="0.002" rgba="1 0.5 0 1"/>
    </body>
    <body name="panda_root" pos="0 0 0">
      <include file="{chain_include_filename}"/>
    </body>
  </worldbody>
  <include file="franka_assets/actuator.xml"/>
</mujoco>
"""


def load_panda_probe_model(bundle: FrankaAssetBundle) -> mujoco.MjModel:
    working_bundle = _materialize_local_bundle_copy(bundle)
    xml = build_panda_probe_xml(working_bundle)
    temp_path = working_bundle.bundle_root / f"tmp_panda_probe_{uuid4().hex}.xml"
    temp_path.write_text(xml, encoding="utf-8")
    try:
        return mujoco.MjModel.from_xml_path(str(temp_path))
    finally:
        temp_path.unlink(missing_ok=True)


def load_full_system_model(bundle: FrankaAssetBundle) -> mujoco.MjModel:
    working_bundle = _materialize_local_bundle_copy(bundle)
    cache_key = str(working_bundle.bundle_root.resolve())
    if cache_key in _FULL_SYSTEM_MODEL_CACHE:
        return _FULL_SYSTEM_MODEL_CACHE[cache_key]
    chain_include_filename = f"generated_chain_with_peg_{uuid4().hex}.xml"
    chain_xml = build_panda_chain_with_peg_xml(working_bundle)
    xml = build_full_system_xml(working_bundle, chain_include_filename=chain_include_filename)
    chain_path = working_bundle.bundle_root / chain_include_filename
    temp_path = working_bundle.bundle_root / f"tmp_vi_full_{uuid4().hex}.xml"
    chain_path.write_text(chain_xml, encoding="utf-8")
    temp_path.write_text(xml, encoding="utf-8")
    try:
        # Reuse the compiled model to avoid repeated XML/mesh reload failures on Windows.
        model = mujoco.MjModel.from_xml_path(str(temp_path))
        _FULL_SYSTEM_MODEL_CACHE[cache_key] = model
        return model
    finally:
        temp_path.unlink(missing_ok=True)
        chain_path.unlink(missing_ok=True)
