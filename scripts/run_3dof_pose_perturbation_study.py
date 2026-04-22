from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType


def _load_impl() -> ModuleType:
    module_path = (
        Path(__file__).resolve().parent
        / "experiments"
        / "run_3dof_pose_perturbation_study.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_3dof_pose_perturbation_study_impl",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load pose-perturbation runner from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_IMPL = _load_impl()

POSE_PERTURBATION_SUITE_NAMES = _IMPL.POSE_PERTURBATION_SUITE_NAMES
parse_args = _IMPL.parse_args
_default_output_path = _IMPL._default_output_path
_write_report = _IMPL._write_report
run_3dof_handcrafted_uncertainty_suite = (
    _IMPL.run_3dof_handcrafted_uncertainty_suite
)
_run_3dof_registry_suite_across_profiles = (
    _IMPL._run_3dof_registry_suite_across_profiles
)


def _sync_impl_overrides() -> None:
    _IMPL.POSE_PERTURBATION_SUITE_NAMES = POSE_PERTURBATION_SUITE_NAMES
    _IMPL.parse_args = parse_args
    _IMPL._default_output_path = _default_output_path
    _IMPL._write_report = _write_report
    _IMPL.run_3dof_handcrafted_uncertainty_suite = (
        run_3dof_handcrafted_uncertainty_suite
    )
    _IMPL._run_3dof_registry_suite_across_profiles = (
        _run_3dof_registry_suite_across_profiles
    )


def main() -> None:
    _sync_impl_overrides()
    _IMPL.main()


if __name__ == "__main__":
    main()
