from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relative_path(path: Path, *, repo_root: Path) -> str:
    resolved_path = Path(path).resolve()
    resolved_root = Path(repo_root).resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path is outside repository root: {resolved_path}") from exc
    return relative.as_posix()


def git_commit(*, repo_root: Path) -> str:
    return _run_git(["rev-parse", "HEAD"], repo_root=repo_root)


def git_dirty(*, repo_root: Path) -> bool:
    return bool(_run_git(["status", "--porcelain"], repo_root=repo_root))


def _run_git(args: list[str], *, repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=Path(repo_root),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()

