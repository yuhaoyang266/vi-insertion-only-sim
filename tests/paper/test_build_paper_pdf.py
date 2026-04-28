from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from scripts.export import build_paper_pdf


def test_pdf_builder_probes_windows_miktex_path_when_tools_are_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(build_paper_pdf.shutil, "which", lambda _name: None)
    monkeypatch.setattr(Path, "exists", lambda _self: False)

    with pytest.raises(FileNotFoundError) as exc_info:
        build_paper_pdf.resolve_tool("pdflatex")

    message = str(exc_info.value)
    assert "MiKTeX" in message
    assert str(build_paper_pdf.MIKTEX_WINDOWS_BIN) in message
    assert str(build_paper_pdf.LOCAL_MIKTEX_WINDOWS_BIN) in message
    assert "PATH" in message


def test_pdf_builder_runs_direct_latex_bibtex_latex_latex_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    (paper_dir / "main.tex").write_text(r"\documentclass{article}\begin{document}x\end{document}")
    calls: list[tuple[list[str], Path]] = []

    def _record_run(command, *, cwd, check):
        calls.append((list(command), Path(cwd)))
        assert check is True
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(build_paper_pdf.subprocess, "run", _record_run)

    pdf_path = build_paper_pdf.build_pdf(
        paper_dir=paper_dir,
        tex="main.tex",
        pdflatex=Path("pdflatex"),
        bibtex=Path("bibtex"),
    )

    assert pdf_path == paper_dir / "main.pdf"
    assert [call[0][0] for call in calls] == [
        "pdflatex",
        "bibtex",
        "pdflatex",
        "pdflatex",
        "pdflatex",
    ]
    assert all(call[1] == paper_dir for call in calls)
