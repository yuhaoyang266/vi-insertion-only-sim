from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner_module():
    module_path = REPO_ROOT / "scripts" / "experiments" / "run_cross_sim_via_paper_b.py"
    spec = importlib.util.spec_from_file_location(
        "run_cross_sim_via_paper_b_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_git(repo_path: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _make_paper_b_repo(tmp_path: Path) -> tuple[Path, str]:
    paper_b_repo = tmp_path / "paper_b"
    paper_b_docs = paper_b_repo / "docs"
    paper_b_docs.mkdir(parents=True)
    paper_b_contract = paper_b_docs / "cross_paper_interface_contract.md"
    paper_a_contract = REPO_ROOT / "docs" / "cross_paper_interface_contract.md"
    paper_b_contract.write_bytes(paper_a_contract.read_bytes())
    _run_git(paper_b_repo, "init")
    _run_git(paper_b_repo, "config", "user.email", "test@example.com")
    _run_git(paper_b_repo, "config", "user.name", "Test User")
    _run_git(paper_b_repo, "add", "docs/cross_paper_interface_contract.md")
    _run_git(paper_b_repo, "commit", "-m", "mirror contract")
    return paper_b_repo, _run_git(paper_b_repo, "rev-parse", "--short", "HEAD")


def test_cross_sim_runner_writes_dry_run_ranking_artifacts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    paper_b_repo, paper_b_commit = _make_paper_b_repo(tmp_path)
    output_path = tmp_path / "cross_sim" / "paper_b_smoke.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_cross_sim_via_paper_b.py",
            "--paper-b-repo-path",
            str(paper_b_repo),
            "--paper-b-commit",
            paper_b_commit,
            "--profiles",
            "nominal",
            "--seeds",
            "0",
            "--episodes-per-seed",
            "2",
            "--suites",
            "repaired_mainline_bc_to_ppo",
            "--dry-run",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["artifact_type"] == "cross_sim_ranking"
    assert "paper_b_commit" not in payload["metadata"]
    assert payload["metadata"]["paper_b_checkout_commit"] == paper_b_commit
    assert payload["metadata"]["paper_b_verified_env_commit"] == "3eb8408"
    assert payload["metadata"]["paper_b_contract_mirror_commit"] == "dfb3c5c"
    assert payload["metadata"]["paper_a_policy_artifact"] == "not_available"
    assert payload["metadata"]["paper_b_env_config"] == "not_available"
    assert payload["metadata"]["mapping_dyaw"] == 0.0
    assert payload["metadata"]["torque_drop_guard_n_m"] == 0.1
    assert payload["metadata"]["dry_run"] is True
    assert payload["rows"][0]["suite_name"] == "repaired_mainline_bc_to_ppo"
    assert payload["rows"][0]["status"] == "not_available"
    assert output_path.with_suffix(".csv").exists()
    assert output_path.with_suffix(".md").exists()


def test_cross_sim_runner_rejects_unknown_profiles(monkeypatch, tmp_path: Path) -> None:
    module = _load_runner_module()
    paper_b_repo, paper_b_commit = _make_paper_b_repo(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_cross_sim_via_paper_b.py",
            "--paper-b-repo-path",
            str(paper_b_repo),
            "--paper-b-commit",
            paper_b_commit,
            "--profiles",
            "invalid_profile",
            "--dry-run",
            "--output",
            str(tmp_path / "cross_sim.json"),
        ],
    )

    with pytest.raises(ValueError, match="invalid_profile"):
        module.main()


def test_cross_sim_runner_rejects_wrong_paper_b_commit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    paper_b_repo, _paper_b_commit = _make_paper_b_repo(tmp_path)
    output_path = tmp_path / "cross_sim.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_cross_sim_via_paper_b.py",
            "--paper-b-repo-path",
            str(paper_b_repo),
            "--paper-b-commit",
            "deadbee",
            "--dry-run",
            "--output",
            str(output_path),
        ],
    )

    with pytest.raises(RuntimeError, match="Paper-B commit mismatch"):
        module.main()

    assert not output_path.exists()


def test_cross_sim_runner_records_actual_checkout_commit_when_omitted(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    paper_b_repo, paper_b_commit = _make_paper_b_repo(tmp_path)
    output_path = tmp_path / "cross_sim.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_cross_sim_via_paper_b.py",
            "--paper-b-repo-path",
            str(paper_b_repo),
            "--profiles",
            "nominal",
            "--seeds",
            "0",
            "--episodes-per-seed",
            "1",
            "--suites",
            "repaired_mainline_bc_to_ppo",
            "--dry-run",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["metadata"]["paper_b_checkout_commit"] == paper_b_commit


def test_cross_sim_runner_help_works_from_repo_root() -> None:
    script_path = REPO_ROOT / "scripts" / "experiments" / "run_cross_sim_via_paper_b.py"

    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Run a Paper-A to Paper-B cross-sim bridge smoke" in completed.stdout
