#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = {
    ".json",
    ".md",
    ".py",
    ".sh",
    ".txt",
    ".yaml",
    ".yml",
}

QUESTION_MARK_RUN = re.compile(r"\?{4,}")

SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
}


@dataclass(frozen=True)
class TextIssue:
    path: Path
    line: int
    column: int
    codepoint: str
    reason: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate source text files for known encoding corruption.")
    parser.add_argument("--root", default=".", help="Repository root or directory to scan.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan all matching files under root instead of git-tracked/unignored files.",
    )
    return parser.parse_args(argv)


def is_text_candidate(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def iter_all_text_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if is_text_candidate(path) and not should_skip(path.relative_to(root))
    )


def iter_git_text_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
        text=False,
    )
    if result.returncode != 0:
        return iter_all_text_files(root)

    paths: list[Path] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = root / raw.decode("utf-8", errors="surrogateescape")
        if is_text_candidate(path) and not should_skip(path.relative_to(root)):
            paths.append(path)
    return sorted(paths)


def issue_for_char(path: Path, line: int, column: int, char: str) -> TextIssue | None:
    codepoint = f"U+{ord(char):04X}"
    if char == "\ufffd":
        return TextIssue(path, line, column, codepoint, "replacement character")
    if "\ue000" <= char <= "\uf8ff":
        return TextIssue(path, line, column, codepoint, "private-use character")
    return None


def scan_file(path: Path) -> list[TextIssue]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        return [TextIssue(path, exc.start + 1, 1, "decode-error", str(exc))]

    issues: list[TextIssue] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for column, char in enumerate(line, start=1):
            issue = issue_for_char(path, line_number, column, char)
            if issue is not None:
                issues.append(issue)
        for match in QUESTION_MARK_RUN.finditer(line):
            issues.append(
                TextIssue(
                    path,
                    line_number,
                    match.start() + 1,
                    match.group(0),
                    "question-mark run",
                )
            )
    return issues


def format_issue(issue: TextIssue, root: Path) -> str:
    try:
        display_path = issue.path.relative_to(root)
    except ValueError:
        display_path = issue.path
    return f"{display_path}:{issue.line}:{issue.column}: {issue.codepoint} {issue.reason}"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"root does not exist: {root}")

    files = iter_all_text_files(root) if args.all else iter_git_text_files(root)
    issues: list[TextIssue] = []
    for path in files:
        issues.extend(scan_file(path))

    if issues:
        print("text integrity: FAIL")
        for issue in issues:
            print(format_issue(issue, root))
        print(f"checked_files: {len(files)}")
        print(f"issues: {len(issues)}")
        return 1

    print("text integrity: PASS")
    print(f"checked_files: {len(files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
