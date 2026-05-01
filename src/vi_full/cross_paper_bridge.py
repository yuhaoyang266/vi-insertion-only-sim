from __future__ import annotations

import hashlib
from pathlib import Path


CONTRACT_RELATIVE_PATH = Path("docs") / "cross_paper_interface_contract.md"
CONTRACT_SHA = "d0463ee78952bec382cc55cadeb6b32dc00494f391024d0903c17b0fcf29d45e"
CONTRACT_VERSION = "2026-05-01"


def resolve_contract_path(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    return root / CONTRACT_RELATIVE_PATH


def compute_contract_sha(contract_path: Path | None = None) -> str:
    path = contract_path if contract_path is not None else resolve_contract_path()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_contract_sha_current(contract_path: Path | None = None) -> str:
    actual_sha = compute_contract_sha(contract_path)
    if actual_sha != CONTRACT_SHA:
        raise RuntimeError(
            "Cross-paper interface contract SHA mismatch: "
            f"expected {CONTRACT_SHA}, got {actual_sha}"
        )
    return actual_sha
