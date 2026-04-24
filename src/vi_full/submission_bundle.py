from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil


ANONYMOUS_SNAPSHOT_DIRS = (
    "artifacts",
    "figures",
    "outputs",
    "paper",
    "scripts",
    "src",
    "supplement",
)
ANONYMOUS_SNAPSHOT_TEST_DIRS = ("tests/reviewer",)
ANONYMOUS_SNAPSHOT_FILES = ("environment.yml", "pyproject.toml")
EDITOR_ONLY_DOCS = ("cover_letter_draft.md", "submission_package_checklist.md")
EXCLUDED_PATHS = (
    "docs/github_upload.md",
    "docs/cover_letter_draft.md",
    "docs/submission_package_checklist.md",
    "findings.md",
    "narrative_branches.md",
    "progress.md",
    "protocol_freeze.md",
    "task_plan.md",
    "tests/",
)
IGNORE_PATTERNS = shutil.ignore_patterns(
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".claude",
    "scratch",
    "tmp",
)
REPOSITORY_URL_PATTERN = re.compile(
    r"\nRepository URL embedded in the manuscript:\n\n`[^`]+`\n",
    flags=re.MULTILINE,
)
HTTP_URL_PATTERN = re.compile(r"https?://[^\s`}]+")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


def _copy_tree(source_path: Path, destination_path: Path) -> None:
    if not source_path.exists():
        return
    shutil.copytree(source_path, destination_path, ignore=IGNORE_PATTERNS)


def _anonymize_readme(readme_text: str) -> str:
    sanitized = REPOSITORY_URL_PATTERN.sub("\n", readme_text)
    sanitized = re.sub(
        r"^# .+$",
        "# Anonymous Submission Snapshot",
        sanitized,
        count=1,
        flags=re.MULTILINE,
    )
    sanitized = sanitized.replace(
        "This repository contains",
        "This submission snapshot contains",
    )
    if "Anonymous Submission Snapshot" not in sanitized:
        sanitized = "# Anonymous Submission Snapshot\n\n" + sanitized.lstrip()
    return sanitized


def _anonymize_main_tex(main_tex: str) -> str:
    redacted_lines: list[str] = []
    for raw_line in main_tex.splitlines():
        if raw_line.startswith(r"\newcommand{\repositoryurl}"):
            redacted_lines.append(
                r"\newcommand{\repositoryurl}{\url{anonymous-repository-url.invalid}}"
            )
            continue
        if raw_line.startswith(r"\author{"):
            redacted_lines.append(r"\author{Anonymous Authors}")
            continue
        if raw_line.startswith(r"\date{"):
            redacted_lines.append(r"\date{\small Anonymous submission package}")
            continue
        line = EMAIL_PATTERN.sub("anonymous@example.invalid", raw_line)
        line = HTTP_URL_PATTERN.sub("anonymous-repository-url.invalid", line)
        redacted_lines.append(line)
    redacted_text = "\n".join(redacted_lines)
    if main_tex.endswith("\n"):
        redacted_text += "\n"
    return redacted_text


def _write_editor_readme(editor_materials_dir: Path) -> None:
    content = """# Editor Materials

This directory contains non-anonymous staging files intended for editor-facing
submission assembly rather than reviewer-facing supplementary release.
"""
    (editor_materials_dir / "README.md").write_text(content, encoding="utf-8")


def _write_summary(
    output_dir: Path,
    venue: str,
    anonymous_snapshot_dir: Path,
    editor_materials_dir: Path,
    paper_pdf_path: Path | None,
) -> Path:
    paper_status = (
        f"included as `{paper_pdf_path.name}`" if paper_pdf_path is not None else "not included"
    )
    summary = f"""# Submission Bundle Summary

- Venue label: `{venue}`
- Anonymous snapshot: `{anonymous_snapshot_dir.name}/`
- Editor materials: `{editor_materials_dir.name}/`
- Paper PDF: {paper_status}
- Identity redactions: `README.md`, `paper/main.tex`
- Explicitly excluded from anonymous snapshot: `docs/github_upload.md`
"""
    summary_path = output_dir / "submission_bundle_summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    return summary_path


def _make_archive(output_dir: Path, directory_name: str) -> Path:
    archive_base = output_dir / directory_name
    archive_path = shutil.make_archive(
        str(archive_base),
        "zip",
        root_dir=output_dir,
        base_dir=directory_name,
    )
    return Path(archive_path)


def _collect_identity_tokens(source_root: Path) -> list[str]:
    tokens: set[str] = set()

    readme_path = source_root / "README.md"
    if readme_path.exists():
        readme_text = readme_path.read_text(encoding="utf-8")
        tokens.update(HTTP_URL_PATTERN.findall(readme_text))

    main_tex_path = source_root / "paper" / "main.tex"
    if main_tex_path.exists():
        main_tex = main_tex_path.read_text(encoding="utf-8")
        tokens.update(HTTP_URL_PATTERN.findall(main_tex))
        tokens.update(EMAIL_PATTERN.findall(main_tex))
        for line in main_tex.splitlines():
            if line.startswith(r"\author{"):
                author_payload = line.removeprefix(r"\author{").rstrip("}")
                author_name = author_payload.split(r"\\", 1)[0].strip()
                if author_name:
                    tokens.add(author_name)

    return sorted(token for token in tokens if token and "Anonymous" not in token)


def _scan_for_identity_leaks(snapshot_dir: Path, identity_tokens: list[str]) -> dict[str, list[str]]:
    leaks: dict[str, list[str]] = {}
    if not identity_tokens:
        return leaks

    for path in snapshot_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        matches = [token for token in identity_tokens if token in text]
        if matches:
            leaks[str(path.relative_to(snapshot_dir))] = matches
    return leaks


def _resolve_bundle_paper_pdf(output_dir: Path, paper_pdf: Path | None) -> Path | None:
    if paper_pdf is None:
        return None

    resolved_paper_pdf = Path(paper_pdf).resolve()
    if resolved_paper_pdf.is_relative_to(output_dir):
        raise ValueError(
            "paper_pdf must point to a file outside the submission bundle output directory."
        )
    return resolved_paper_pdf


def _validate_bundle_output_dir(source_root: Path, output_dir: Path) -> None:
    if output_dir == source_root or source_root.is_relative_to(output_dir):
        raise ValueError(
            "output_dir must not point at the source repository root or one of its parents."
        )

    for directory_name in ANONYMOUS_SNAPSHOT_DIRS:
        copied_source_dir = source_root / directory_name
        if output_dir.is_relative_to(copied_source_dir):
            raise ValueError(
                "output_dir must stay outside the source directories copied into the bundle."
            )


def build_submission_bundle(
    *,
    source_root: Path,
    output_dir: Path,
    venue: str,
    paper_pdf: Path | None = None,
    create_archives: bool = True,
) -> dict[str, Path | None]:
    source_root = Path(source_root).resolve()
    output_dir = Path(output_dir).resolve()
    _validate_bundle_output_dir(source_root, output_dir)
    paper_pdf = _resolve_bundle_paper_pdf(output_dir, paper_pdf)
    anonymous_snapshot_dir = output_dir / "anonymous_snapshot"
    editor_materials_dir = output_dir / "editor_materials"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    copied_directories = list(ANONYMOUS_SNAPSHOT_DIRS)
    for directory_name in ANONYMOUS_SNAPSHOT_DIRS:
        source_dir = source_root / directory_name
        if source_dir.exists():
            _copy_tree(source_dir, anonymous_snapshot_dir / directory_name)

    for directory_name in ANONYMOUS_SNAPSHOT_TEST_DIRS:
        source_dir = source_root / directory_name
        if source_dir.exists():
            _copy_tree(source_dir, anonymous_snapshot_dir / directory_name)
            copied_directories.append(f"{directory_name}/")

    anonymous_snapshot_dir.mkdir(parents=True, exist_ok=True)
    for file_name in ANONYMOUS_SNAPSHOT_FILES:
        source_file = source_root / file_name
        if source_file.exists():
            shutil.copy2(source_file, anonymous_snapshot_dir / file_name)

    readme_path = source_root / "README.md"
    if readme_path.exists():
        anonymized_readme = _anonymize_readme(readme_path.read_text(encoding="utf-8"))
        (anonymous_snapshot_dir / "README.md").write_text(
            anonymized_readme,
            encoding="utf-8",
        )

    main_tex_path = anonymous_snapshot_dir / "paper" / "main.tex"
    if main_tex_path.exists():
        anonymized_main_tex = _anonymize_main_tex(main_tex_path.read_text(encoding="utf-8"))
        main_tex_path.write_text(anonymized_main_tex, encoding="utf-8")

    identity_tokens = _collect_identity_tokens(source_root)
    identity_leaks = _scan_for_identity_leaks(anonymous_snapshot_dir, identity_tokens)
    if identity_leaks:
        leak_lines = [
            f"{path}: {', '.join(matches)}"
            for path, matches in sorted(identity_leaks.items())
        ]
        raise ValueError(
            "Identity leak detected in anonymous snapshot:\n" + "\n".join(leak_lines)
        )

    editor_materials_dir.mkdir(parents=True, exist_ok=True)
    for doc_name in EDITOR_ONLY_DOCS:
        source_doc = source_root / "docs" / doc_name
        if source_doc.exists():
            shutil.copy2(source_doc, editor_materials_dir / doc_name)
    _write_editor_readme(editor_materials_dir)

    copied_paper_pdf_path: Path | None = None
    if paper_pdf is not None:
        copied_paper_pdf_path = output_dir / paper_pdf.name
        shutil.copy2(paper_pdf, copied_paper_pdf_path)

    anonymous_snapshot_zip = (
        _make_archive(output_dir, anonymous_snapshot_dir.name) if create_archives else None
    )
    editor_materials_zip = (
        _make_archive(output_dir, editor_materials_dir.name) if create_archives else None
    )

    manifest = {
        "venue": venue,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source_root),
        "anonymous_snapshot_dir": str(anonymous_snapshot_dir),
        "editor_materials_dir": str(editor_materials_dir),
        "copied_directories": copied_directories,
        "copied_files": ["README.md", *ANONYMOUS_SNAPSHOT_FILES],
        "redacted_files": ["README.md", "paper/main.tex"],
        "excluded_paths": list(EXCLUDED_PATHS),
        "identity_token_scan_passed": True,
        "paper_pdf": {
            "status": "included" if copied_paper_pdf_path is not None else "missing",
            "filename": copied_paper_pdf_path.name
            if copied_paper_pdf_path is not None
            else None,
        },
        "archives": {
            "anonymous_snapshot_zip": str(anonymous_snapshot_zip)
            if anonymous_snapshot_zip is not None
            else None,
            "editor_materials_zip": str(editor_materials_zip)
            if editor_materials_zip is not None
            else None,
        },
    }
    manifest_path = output_dir / "submission_bundle_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    summary_path = _write_summary(
        output_dir=output_dir,
        venue=venue,
        anonymous_snapshot_dir=anonymous_snapshot_dir,
        editor_materials_dir=editor_materials_dir,
        paper_pdf_path=copied_paper_pdf_path,
    )

    return {
        "anonymous_snapshot_dir": anonymous_snapshot_dir,
        "editor_materials_dir": editor_materials_dir,
        "manifest_path": manifest_path,
        "summary_path": summary_path,
        "paper_pdf_path": copied_paper_pdf_path,
        "anonymous_snapshot_zip": anonymous_snapshot_zip,
        "editor_materials_zip": editor_materials_zip,
    }
