from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PAPER_DIR = Path("paper")
DEFAULT_TEX = "main.tex"
LOCAL_MIKTEX_WINDOWS_BIN = Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64"
MIKTEX_WINDOWS_BIN = LOCAL_MIKTEX_WINDOWS_BIN


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _tool_candidates(tool_name: str, override: Path | None = None) -> list[Path]:
    candidates: list[Path] = []
    if override is not None:
        candidates.append(override)
    discovered = shutil.which(tool_name)
    if discovered is not None:
        candidates.append(Path(discovered))
    candidates.append(MIKTEX_WINDOWS_BIN / f"{tool_name}.exe")
    if LOCAL_MIKTEX_WINDOWS_BIN != MIKTEX_WINDOWS_BIN:
        candidates.append(LOCAL_MIKTEX_WINDOWS_BIN / f"{tool_name}.exe")
    return candidates


def resolve_tool(tool_name: str, override: Path | None = None) -> Path:
    for candidate in _tool_candidates(tool_name, override):
        if candidate.exists():
            return candidate
    searched = "\n".join(f"  - {candidate}" for candidate in _tool_candidates(tool_name, override))
    raise FileNotFoundError(
        f"Could not find `{tool_name}`.\n"
        "Install MiKTeX or add its binary directory to PATH, then retry.\n"
        f"Expected Windows MiKTeX path: {MIKTEX_WINDOWS_BIN}\n"
        f"Current-user MiKTeX path: {LOCAL_MIKTEX_WINDOWS_BIN}\n"
        "Searched:\n"
        f"{searched}"
    )


def _run(command: list[str], *, cwd: Path) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def build_pdf(
    *,
    paper_dir: Path,
    tex: str,
    pdflatex: Path,
    bibtex: Path,
) -> Path:
    paper_dir = _repo_path(paper_dir)
    tex_path = paper_dir / tex
    if not tex_path.is_file():
        raise FileNotFoundError(f"TeX source not found: {tex_path}")

    stem = tex_path.stem
    pdf_path = paper_dir / f"{stem}.pdf"
    latex_command = [
        str(pdflatex),
        "-interaction=nonstopmode",
        "-halt-on-error",
        tex_path.name,
    ]
    _run(latex_command, cwd=paper_dir)
    _run([str(bibtex), stem], cwd=paper_dir)
    _run(latex_command, cwd=paper_dir)
    _run(latex_command, cwd=paper_dir)
    _run(latex_command, cwd=paper_dir)
    return pdf_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build paper/main.pdf with a direct pdflatex -> bibtex chain.",
    )
    parser.add_argument("--paper-dir", type=Path, default=DEFAULT_PAPER_DIR)
    parser.add_argument("--tex", default=DEFAULT_TEX)
    parser.add_argument("--pdflatex", type=Path, default=None)
    parser.add_argument("--bibtex", type=Path, default=None)
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        pdflatex = resolve_tool("pdflatex", args.pdflatex)
        bibtex = resolve_tool("bibtex", args.bibtex)
        pdf_path = build_pdf(
            paper_dir=args.paper_dir,
            tex=args.tex,
            pdflatex=pdflatex,
            bibtex=bibtex,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(pdf_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
