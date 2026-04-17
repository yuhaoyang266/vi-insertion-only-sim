import importlib.util
from pathlib import Path
import sys


def _load_export_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "export"
        / "export_paper_only_sim_high_friction_trace_figure.py"
    )
    spec = importlib.util.spec_from_file_location(
        "export_high_friction_trace_figure_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_export_high_friction_trace_uses_benchmark_contract_default(
    monkeypatch,
) -> None:
    import vi_full.three_dof_contract as contract_module

    class _Contract:
        max_episode_steps = 77

    monkeypatch.setattr(
        contract_module,
        "DEFAULT_3DOF_BENCHMARK_CONTRACT",
        _Contract(),
    )
    module = _load_export_module()
    monkeypatch.setattr(
        sys,
        "argv",
        ["export_paper_only_sim_high_friction_trace_figure.py"],
    )

    args = module.parse_args()

    assert args.max_episode_steps == 77
