#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from runtime_state import RuntimeStateError, load_state
except ModuleNotFoundError:
    from scripts.runtime_state import RuntimeStateError, load_state


ACTIVE_STATUSES = {"armed", "pending_review", "followup_needed", "summarizing"}
STATE_KEYS = (
    "status",
    "entry_type",
    "mode",
    "host",
    "project_root",
    "case_id",
    "session_id",
    "trace_id",
    "rejection_count",
    "correction_attempt_count",
    "ascended_trigger_reason",
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "scripts" / "mistakebook_cli.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_home() -> Path:
    raw_home = os.environ.get("HOME") or os.environ.get("USERPROFILE") or "~"
    return Path(raw_home).expanduser()


def default_state_path() -> Path:
    return resolve_home() / ".mistakebook" / "runtime-state.json"


def default_journal_path() -> Path:
    return resolve_home() / ".mistakebook" / "runtime-journal.md"


def output_hook(event_name: str, additional_context: str = "", **extra: Any) -> int:
    payload: dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": additional_context,
        }
    }
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=True))
    return 0


def load_runtime_state(path: Path) -> dict[str, Any]:
    try:
        return load_state(path)
    except (RuntimeStateError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to load runtime state: {exc}") from exc


def is_active_state(state: dict[str, Any]) -> bool:
    return str(state.get("status") or "") in ACTIVE_STATUSES


def text_value(value: Any, default: str = "n/a") -> str:
    text = str(value or "").strip()
    return text if text else default


def render_journal(state: dict[str, Any], event_name: str) -> str:
    lines = [
        "# Mistakebook Runtime Journal",
        "",
        "## Timestamp",
        utc_now(),
        "",
        "## Source Event",
        event_name,
        "",
        "## Runtime State",
    ]
    for key in STATE_KEYS:
        lines.append(f"- {key}: {text_value(state.get(key))}")
    lines.extend(
        [
            "",
            "## Next Expected Action",
            "Resume the same mistakebook loop after interruption or compaction.",
            "Do not archive until the user explicitly confirms completion or asks to write the item into memory.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_journal(state: dict[str, Any], event_name: str, journal_path: Path) -> None:
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_text(render_journal(state, event_name), encoding="utf-8")


def read_recent_journal(journal_path: Path, max_age_seconds: int) -> str:
    if not journal_path.exists():
        return ""
    age_seconds = int(datetime.now().timestamp() - journal_path.stat().st_mtime)
    if age_seconds > max_age_seconds:
        return ""
    return journal_path.read_text(encoding="utf-8")


def read_optional_text(path_text: str | None) -> str:
    if not path_text:
        return ""
    path = Path(path_text).expanduser()
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def extract_case_id(journal: str) -> str:
    for line in journal.splitlines():
        stripped = line.strip()
        if stripped.startswith("- case_id:"):
            return stripped.split(":", 1)[1].strip()
    return ""


def refresh_journal_with_compact_summary(journal_path: Path, compact_summary: str) -> str:
    current = journal_path.read_text(encoding="utf-8")
    compact_summary = compact_summary.strip()
    if not compact_summary:
        return current
    marker = "\n## Compact Summary\n"
    if marker in current:
        current = current.split(marker, 1)[0].rstrip() + "\n"
    updated = f"{current.rstrip()}\n\n## Compact Summary\n{compact_summary}\n"
    journal_path.write_text(updated, encoding="utf-8")
    return updated


def checkpoint_context(state: dict[str, Any], journal_path: Path) -> str:
    return (
        "[Mistakebook Checkpoint]\n"
        f"Correction state saved to {journal_path}.\n"
        f"case_id={text_value(state.get('case_id'))}\n"
        f"status={text_value(state.get('status'))}\n"
        "Do not archive until explicit user confirmation is present."
    )


def pre_compact_command(args: argparse.Namespace) -> int:
    state = load_runtime_state(Path(args.state_file).expanduser())
    if not is_active_state(state):
        return output_hook("PreCompact")
    journal_path = Path(args.journal_file).expanduser() if args.journal_file else default_journal_path()
    write_journal(state, "PreCompact", journal_path)
    return output_hook("PreCompact", checkpoint_context(state, journal_path))


def post_compact_command(args: argparse.Namespace) -> int:
    journal_path = Path(args.journal_file).expanduser() if args.journal_file else default_journal_path()
    journal = read_recent_journal(journal_path, args.max_age_seconds)
    if not journal:
        return output_hook("PostCompact", activeCaseSurvived=False)

    compact_summary = read_optional_text(args.compact_summary_file)
    active_case_survived = True
    recovery_check = "Recovery check: no compact summary provided; runtime journal is the authority."
    if compact_summary:
        case_id = extract_case_id(journal)
        active_case_survived = not case_id or case_id in compact_summary
        recovery_check = (
            "Recovery check: active case survived compact summary."
            if active_case_survived
            else "Recovery check: active case missing from compact summary; restore from runtime journal."
        )
        journal = refresh_journal_with_compact_summary(journal_path, compact_summary)

    context = (
        "[Mistakebook PostCompact Restore]\n"
        f"A recent checkpoint exists at {journal_path}.\n"
        "Resume the same case when the current discussion continues that loop.\n"
        "Do not archive until the user explicitly confirms completion or asks to write the item into memory.\n\n"
        f"{recovery_check}\n\n"
        f"{journal}"
    )
    return output_hook("PostCompact", context, activeCaseSurvived=active_case_survived)


def session_end_command(args: argparse.Namespace) -> int:
    state = load_runtime_state(Path(args.state_file).expanduser())
    if not is_active_state(state):
        return output_hook("SessionEnd")
    journal_path = Path(args.journal_file).expanduser() if args.journal_file else default_journal_path()
    write_journal(state, "SessionEnd", journal_path)

    warning = ""
    if state.get("status") == "summarizing":
        warning = (
            "\nWarning: pending archive is unconfirmed. "
            "Do not archive this case unless userConfirmed=true is available."
        )

    context = (
        "[Mistakebook SessionEnd]\n"
        f"Saved unfinished case to {journal_path}.\n"
        f"case_id={text_value(state.get('case_id'))}\n"
        f"status={text_value(state.get('status'))}"
        f"{warning}"
    )
    return output_hook("SessionEnd", context)


def run_cli(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    completed = subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
    )
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "mistakebook_cli failed").strip()
        raise SystemExit(message)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"mistakebook_cli returned invalid JSON: {completed.stdout}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("mistakebook_cli returned non-object JSON")
    return payload


def subagent_start_command(args: argparse.Namespace) -> int:
    task_text = (
        args.task_text
        or os.environ.get("MISTAKEBOOK_SUBAGENT_TASK")
        or os.environ.get("CLAUDE_USER_PROMPT")
        or os.environ.get("USER_PROMPT")
        or ""
    ).strip()
    if not task_text:
        return output_hook("SubagentStart")

    payload = run_cli(
        [
            "scholar",
            "--host",
            args.host,
            "--project-root",
            args.project_root,
            "--scope",
            args.scope,
            "--text",
            task_text,
            "--limit",
            str(args.limit),
            "--stale-days",
            str(args.stale_days),
        ]
    )
    evidence = payload.get("evidencePacket") if isinstance(payload.get("evidencePacket"), dict) else {}
    matched_case_ids = evidence.get("matchedCaseIds") or payload.get("matchedCaseIds") or []
    confidence = evidence.get("confidence") or payload.get("confidence") or "none"
    risk = evidence.get("riskOfFalsePositive") or payload.get("riskOfFalsePositive") or "none"
    should_inject = bool(payload.get("shouldInject") or evidence.get("shouldInject"))

    context = ""
    if should_inject:
        top_result = (payload.get("results") or [{}])[0]
        top_title = text_value(top_result.get("title"))
        message = text_value(payload.get("message"), default="")
        context = (
            "[Mistakebook Subagent Memory]\n"
            f"matchedCaseIds={', '.join(str(item) for item in matched_case_ids)}\n"
            f"confidence={confidence}\n"
            f"risk={risk}\n"
            f"title={top_title}\n"
            f"message={message}\n"
            "Use this reminder before starting delegated work."
        )

    return output_hook(
        "SubagentStart",
        context,
        shouldInject=should_inject,
        matchedCaseIds=matched_case_ids,
        confidence=confidence,
        riskOfFalsePositive=risk,
    )


def normalize_case_ids(values: list[str]) -> list[str]:
    case_ids: list[str] = []
    for value in values:
        for item in str(value).replace(",", " ").split():
            if item.strip():
                case_ids.append(item.strip())
    return case_ids


def count_updated_entries(payload: dict[str, Any]) -> int:
    total = 0
    for key in ("project", "global"):
        section = payload.get(key)
        if isinstance(section, dict):
            total += int(section.get("updated_entries") or 0)
    return total


def subagent_stop_command(args: argparse.Namespace) -> int:
    case_ids = normalize_case_ids(args.case_id or [])
    if not case_ids:
        env_ids = os.environ.get("MISTAKEBOOK_CASE_IDS") or os.environ.get("MISTAKEBOOK_CASE_ID") or ""
        case_ids = normalize_case_ids([env_ids])
    if not case_ids:
        return output_hook("SubagentStop", updatedCount=0)

    payload = run_cli(
        [
            "touch",
            "--host",
            args.host,
            "--project-root",
            args.project_root,
            "--scope",
            args.scope,
            "--case-id",
            *case_ids,
            "--kind",
            args.kind,
            "--count",
            str(args.count),
        ]
    )
    updated_count = count_updated_entries(payload)
    context = (
        "[Mistakebook SubagentStop]\n"
        f"caseIds={', '.join(case_ids)}\n"
        f"kind={args.kind}\n"
        f"updatedCount={updated_count}"
    )
    return output_hook("SubagentStop", context, updatedCount=updated_count, touchResult=payload)


def add_state_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state-file", default=str(default_state_path()))
    parser.add_argument("--journal-file")


def add_cli_location_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", choices=("codex", "claude", "vscode", "generic"), default="claude")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--scope", choices=("project", "global", "both"), default="both")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mistakebook lifecycle hook helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pre_compact = subparsers.add_parser("pre-compact", help="Persist active runtime state before compaction.")
    add_state_args(pre_compact)
    pre_compact.set_defaults(func=pre_compact_command)

    post_compact = subparsers.add_parser("post-compact", help="Restore runtime journal after compaction.")
    post_compact.add_argument("--journal-file")
    post_compact.add_argument("--compact-summary-file")
    post_compact.add_argument("--max-age-seconds", type=int, default=86400)
    post_compact.set_defaults(func=post_compact_command)

    session_end = subparsers.add_parser("session-end", help="Save unfinished runtime state at session end.")
    add_state_args(session_end)
    session_end.set_defaults(func=session_end_command)

    subagent_start = subparsers.add_parser("subagent-start", help="Inject high-confidence memory for subagents.")
    add_cli_location_args(subagent_start)
    subagent_start.add_argument("--task-text", default="")
    subagent_start.add_argument("--limit", type=int, default=3)
    subagent_start.add_argument("--stale-days", type=int, default=45)
    subagent_start.set_defaults(func=subagent_start_command)

    subagent_stop = subparsers.add_parser("subagent-stop", help="Record subagent memory hit metrics.")
    add_cli_location_args(subagent_stop)
    subagent_stop.add_argument("--case-id", nargs="*")
    subagent_stop.add_argument("--kind", choices=("retrieval", "hit"), default="hit")
    subagent_stop.add_argument("--count", type=int, default=1)
    subagent_stop.set_defaults(func=subagent_stop_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
