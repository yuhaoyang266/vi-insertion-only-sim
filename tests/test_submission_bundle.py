import json
from pathlib import Path

import pytest

from vi_full.submission_bundle import build_submission_bundle


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_minimal_submission_source_tree(tmp_path: Path) -> Path:
    source_root = tmp_path / "source_repo"
    _write_text(
        source_root / "README.md",
        """# vi-insertion-only-sim

Simulation-only research package for the manuscript.

Repository URL embedded in the manuscript:

`https://github.com/yuhaoyang266/vi-insertion-only-sim`
""",
    )
    _write_text(
        source_root / "paper" / "main.tex",
        r"""\documentclass{article}
\newcommand{\repositoryurl}{\url{https://github.com/yuhaoyang266/vi-insertion-only-sim}}
\title{Support-Gated Variable-Impedance Learning in a 3DoF Insertion Benchmark}
\author{Yu Haoyang\\Shanghai University\\Shanghai Institute of Applied Mathematics and Mechanics\\\texttt{yuhaoyang@shu.edu.cn}}
\date{\small Project repository: \repositoryurl}
\begin{document}
\maketitle
\end{document}
""",
    )
    _write_text(source_root / "paper" / "references.bib", "% references\n")
    _write_text(source_root / "docs" / "cover_letter_draft.md", "Sincerely,\n\nYu Haoyang\n")
    _write_text(
        source_root / "docs" / "github_upload.md",
        "git remote add origin https://github.com/yuhaoyang266/vi-insertion-only-sim.git\n",
    )
    _write_text(source_root / "src" / "vi_full" / "__init__.py", "__all__ = []\n")
    _write_text(source_root / "scripts" / "experiments" / "dummy.py", "print('dummy')\n")
    _write_text(source_root / "tests" / "test_dummy.py", "def test_dummy():\n    assert True\n")
    _write_text(source_root / "environment.yml", "name: vi-insertion-only-sim\n")
    _write_text(source_root / "pyproject.toml", "[project]\nname='vi-insertion-full'\n")
    _write_text(source_root / "figures" / "main" / "fig1.pdf", "pdf\n")
    _write_text(source_root / "supplement" / "figures" / "supplement.pdf", "pdf\n")
    _write_text(source_root / "artifacts" / "main_benchmark" / "artifact.json", "{}\n")
    _write_text(source_root / "outputs" / "evidence_matrix" / "table.md", "# table\n")
    return source_root


def _scan_snapshot_for_identity_strings(snapshot_dir: Path) -> list[str]:
    flagged_terms = (
        "Yu Haoyang",
        "yuhaoyang@shu.edu.cn",
        "github.com/yuhaoyang266",
    )
    findings: list[str] = []
    for path in snapshot_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        matches = [term for term in flagged_terms if term in text]
        if matches:
            findings.append(f"{path.relative_to(snapshot_dir)}: {', '.join(matches)}")
    return findings


def test_build_submission_bundle_anonymizes_identity_surfaces(tmp_path: Path) -> None:
    source_root = _create_minimal_submission_source_tree(tmp_path)
    output_dir = tmp_path / "bundle_output"

    artifacts = build_submission_bundle(
        source_root=source_root,
        output_dir=output_dir,
        venue="journal-double-blind",
        create_archives=False,
    )

    anonymous_snapshot_dir = artifacts["anonymous_snapshot_dir"]
    editor_materials_dir = artifacts["editor_materials_dir"]
    manifest_path = artifacts["manifest_path"]

    assert anonymous_snapshot_dir.is_dir()
    assert editor_materials_dir.is_dir()
    assert manifest_path.is_file()

    snapshot_readme = (anonymous_snapshot_dir / "README.md").read_text(encoding="utf-8")
    assert snapshot_readme.startswith("# Anonymous Submission Snapshot")
    assert "yuhaoyang266" not in snapshot_readme
    assert "Project repository" not in snapshot_readme

    anonymized_main_tex = (anonymous_snapshot_dir / "paper" / "main.tex").read_text(
        encoding="utf-8"
    )
    assert "Anonymous Authors" in anonymized_main_tex
    assert "yuhaoyang@shu.edu.cn" not in anonymized_main_tex
    assert "yuhaoyang266" not in anonymized_main_tex
    assert "Project repository" not in anonymized_main_tex

    assert not (anonymous_snapshot_dir / "docs").exists()
    assert not (anonymous_snapshot_dir / "tests").exists()
    assert (editor_materials_dir / "cover_letter_draft.md").is_file()
    assert _scan_snapshot_for_identity_strings(anonymous_snapshot_dir) == []

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["venue"] == "journal-double-blind"
    assert manifest["identity_token_scan_passed"] is True
    assert manifest["paper_pdf"]["status"] == "missing"
    assert "paper/main.tex" in manifest["redacted_files"]
    assert "README.md" in manifest["redacted_files"]
    assert "docs/github_upload.md" in manifest["excluded_paths"]


def test_build_submission_bundle_can_include_optional_pdf_and_archives(
    tmp_path: Path,
) -> None:
    source_root = _create_minimal_submission_source_tree(tmp_path)
    paper_pdf = tmp_path / "compiled" / "anonymous_manuscript.pdf"
    _write_text(paper_pdf, "%PDF-1.4\n")

    artifacts = build_submission_bundle(
        source_root=source_root,
        output_dir=tmp_path / "bundle_output",
        venue="journal-double-blind",
        paper_pdf=paper_pdf,
        create_archives=True,
    )

    assert artifacts["paper_pdf_path"].is_file()
    assert artifacts["anonymous_snapshot_zip"].is_file()
    assert artifacts["editor_materials_zip"].is_file()

    manifest = json.loads(artifacts["manifest_path"].read_text(encoding="utf-8"))
    assert manifest["paper_pdf"]["status"] == "included"
    assert manifest["paper_pdf"]["filename"] == "anonymous_manuscript.pdf"


def test_build_submission_bundle_rejects_pdf_inside_output_dir(tmp_path: Path) -> None:
    source_root = _create_minimal_submission_source_tree(tmp_path)
    output_dir = tmp_path / "bundle_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    paper_pdf = output_dir / "anonymous_manuscript.pdf"
    _write_text(paper_pdf, "%PDF-1.4\n")

    with pytest.raises(
        ValueError,
        match="outside the submission bundle output directory",
    ):
        build_submission_bundle(
            source_root=source_root,
            output_dir=output_dir,
            venue="journal-double-blind",
            paper_pdf=paper_pdf,
            create_archives=False,
        )

    assert paper_pdf.is_file()


def test_submission_docs_match_completed_local_pdf_build_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    checklist = (
        repo_root / "docs" / "submission_package_checklist.md"
    ).read_text(encoding="utf-8")

    assert "No repository-local blocker remains for the Phase 5 submission package." in checklist
    assert "pdflatex -interaction=nonstopmode -halt-on-error main.tex" in readme
    assert "bibtex main" in readme
    assert "outside the staged bundle directory" in readme
    assert "were all missing when the Phase 5 submission staging pass was checked" not in readme
