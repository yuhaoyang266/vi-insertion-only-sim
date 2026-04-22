from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType


def _load_impl() -> ModuleType:
    module_path = (
        Path(__file__).resolve().parent
        / "experiments"
        / "run_3dof_tuned_fixed_impedance_sweep.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_3dof_tuned_fixed_impedance_sweep_impl",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load tuned fixed-impedance runner from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_IMPL = _load_impl()

_parse_args = _IMPL._parse_args
_default_output_path = _IMPL._default_output_path
_json_safe = _IMPL._json_safe
_write_json = _IMPL._write_json
_format_value_tag = _IMPL._format_value_tag
_fixed_train_overrides = _IMPL._fixed_train_overrides
_run_fixed_config = _IMPL._run_fixed_config
run_3dof_condition_across_profiles = _IMPL.run_3dof_condition_across_profiles
select_top_3dof_tuned_fixed_configs = _IMPL.select_top_3dof_tuned_fixed_configs
build_3dof_fixed_impedance_env_overrides_for = (
    _IMPL.build_3dof_fixed_impedance_env_overrides_for
)


def _sync_impl_overrides() -> None:
    _IMPL._parse_args = _parse_args
    _IMPL._default_output_path = _default_output_path
    _IMPL._json_safe = _json_safe
    _IMPL._write_json = _write_json
    _IMPL._format_value_tag = _format_value_tag
    _IMPL._fixed_train_overrides = _fixed_train_overrides
    _IMPL._run_fixed_config = _run_fixed_config
    _IMPL.run_3dof_condition_across_profiles = run_3dof_condition_across_profiles
    _IMPL.select_top_3dof_tuned_fixed_configs = select_top_3dof_tuned_fixed_configs
    _IMPL.build_3dof_fixed_impedance_env_overrides_for = (
        build_3dof_fixed_impedance_env_overrides_for
    )


def main() -> None:
    _sync_impl_overrides()
    _IMPL.main()


if __name__ == "__main__":
    main()
