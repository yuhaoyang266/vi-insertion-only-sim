from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "artifacts" / "main_benchmark" / "main_benchmark_manifest.json"
STAGE3_BENCHMARK_PATH = (
    "artifacts/main_benchmark/"
    "three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json"
)
SCHEMA2_BENCHMARK_PATH = (
    "artifacts/main_benchmark/"
    "three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
)
REQUIRED_ROLES = {
    "canonical_main_benchmark",
    "canonical_statistics_report",
    "schema2_diagnostic",
}


def _load_artifact_registry_module():
    module_path = REPO_ROOT / "src" / "vi_full" / "artifact_registry.py"
    spec = importlib.util.spec_from_file_location("artifact_registry_under_test", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_manifest_declares_single_canonical_main_benchmark() -> None:
    registry = _load_artifact_registry_module()
    manifest = registry.load_manifest(MANIFEST_PATH)

    artifacts = manifest["artifacts"]
    assert REQUIRED_ROLES <= set(artifacts)
    registry.validate_manifest(manifest, repo_root=REPO_ROOT)

    canonical = registry.get_artifact("canonical_main_benchmark", manifest=manifest)
    assert canonical["role"] == "canonical_main_benchmark"
    assert canonical["path"] == STAGE3_BENCHMARK_PATH
    assert canonical["source_role"] == "stage3_current_manuscript_claim"
    assert canonical["schema_version"] == 3
    assert canonical["claim_scope"] == "main manuscript Table 1 and Figure 2"

    canonical_benchmark_roles = [
        role
        for role, artifact in artifacts.items()
        if artifact["role"] == "canonical_main_benchmark"
    ]
    assert canonical_benchmark_roles == ["canonical_main_benchmark"]


def test_schema2_is_appendix_diagnostic_only() -> None:
    registry = _load_artifact_registry_module()
    manifest = registry.load_manifest(MANIFEST_PATH)

    schema2_roles = [
        (role, artifact)
        for role, artifact in manifest["artifacts"].items()
        if artifact["path"] == SCHEMA2_BENCHMARK_PATH
    ]
    assert [role for role, _ in schema2_roles] == ["schema2_diagnostic"]

    schema2 = schema2_roles[0][1]
    assert schema2["role"] == "appendix_diagnostic_legacy"
    assert schema2["source_role"] == "schema2_appendix_diagnostic_legacy"
    assert schema2["schema_version"] == 2
    assert "appendix" in schema2["claim_scope"]
    assert "main" not in schema2["claim_scope"]
