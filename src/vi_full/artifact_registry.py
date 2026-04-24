from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from vi_full.artifact_provenance import calculate_sha256
except ModuleNotFoundError:  # pragma: no cover - supports direct file loading in tests.
    import importlib.util
    import sys

    module_path = Path(__file__).with_name("artifact_provenance.py")
    spec = importlib.util.spec_from_file_location("artifact_provenance_local", module_path)
    if spec is None or spec.loader is None:
        raise
    provenance_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = provenance_module
    spec.loader.exec_module(provenance_module)
    calculate_sha256 = provenance_module.calculate_sha256


DEFAULT_MANIFEST_PATH = Path("artifacts/main_benchmark/main_benchmark_manifest.json")
REQUIRED_ARTIFACT_FIELDS = {
    "role",
    "path",
    "sha256",
    "schema_version",
    "claim_scope",
    "source_role",
    "generating_command",
    "git_commit",
    "git_dirty",
    "generated_at_utc",
}


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_manifest(manifest, repo_root=_infer_repo_root(Path(path)))
    return manifest


def get_artifact(
    role: str,
    *,
    manifest: dict[str, Any] | None = None,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, Any]:
    loaded_manifest = load_manifest(manifest_path) if manifest is None else manifest
    try:
        return loaded_manifest["artifacts"][role]
    except KeyError as exc:
        raise KeyError(f"Artifact role not found in manifest: {role}") from exc


def validate_manifest(manifest: dict[str, Any], *, repo_root: Path) -> None:
    if manifest.get("manifest_version") != 1:
        raise ValueError("Manifest version must be 1.")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("Manifest must contain a non-empty artifacts mapping.")

    canonical_roles = [
        key for key, artifact in artifacts.items() if artifact.get("role") == "canonical_main_benchmark"
    ]
    if canonical_roles != ["canonical_main_benchmark"]:
        raise ValueError("Manifest must declare exactly one canonical main benchmark role.")

    for role, artifact in artifacts.items():
        _validate_artifact(role, artifact, repo_root=Path(repo_root))


def _validate_artifact(role: str, artifact: dict[str, Any], *, repo_root: Path) -> None:
    missing = REQUIRED_ARTIFACT_FIELDS - set(artifact)
    if missing:
        raise ValueError(f"Artifact '{role}' is missing required fields: {sorted(missing)}")

    raw_path = artifact["path"]
    path = Path(raw_path)
    if path.is_absolute():
        raise ValueError(f"Artifact '{role}' must use a repo-relative path.")
    if ".." in path.parts:
        raise ValueError(f"Artifact '{role}' must not escape the repository root.")

    artifact_path = repo_root / path
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact '{role}' path does not exist: {raw_path}")
    actual_sha256 = calculate_sha256(artifact_path)
    if artifact["sha256"] != actual_sha256:
        raise ValueError(f"Artifact '{role}' sha256 does not match {raw_path}.")

    if role == "schema2_diagnostic":
        if artifact["role"] != "appendix_diagnostic_legacy":
            raise ValueError("schema2_diagnostic must be appendix/diagnostic/legacy only.")
        if "main" in artifact["claim_scope"]:
            raise ValueError("schema2_diagnostic must not claim main-paper scope.")


def _infer_repo_root(path: Path) -> Path:
    resolved = path.resolve()
    for candidate in (resolved.parent, *resolved.parents):
        if (candidate / ".git").exists():
            return candidate
    return resolved.parents[2]
