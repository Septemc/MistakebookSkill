#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


CORRECTION_ACTIVATION_SENTENCE = (
    "<错题集 Skill>我接下来会进行纠错，并根据你的纠错信息，"
    "持续纠错直到完成，然后写入我的错题集。"
)
CORRECTION_FOLLOWUP_SENTENCE = (
    "我有没有吃透当前问题，是否成功纠正错误，如果没有的话，"
    "请你再教我一遍。（如果我已经完成了纠错，也请你告诉我一声，"
    "我可以把错题写入我的错题集。）"
)
NOTE_FOLLOWUP_SENTENCE = (
    "如果这个事项值得长期注意，也可以告诉我“写入记事本”，"
    "我会把它归档到记事本并同步刷新记忆。"
)
ASCENDED_SENTENCE = (
    "我现在会根据我见过最有效的方法来处理这个问题，"
    "我将检索我的所有知识库，我现在什么都不缺了！"
)


def resolve_home() -> Path:
    raw_home = os.environ.get("HOME") or os.environ.get("USERPROFILE") or "~"
    return Path(raw_home).expanduser()


def config_path() -> Path:
    return resolve_home() / ".mistakebook" / "config.json"


def read_config_bool(key: str, default: bool) -> bool:
    path = config_path()
    if not path.exists():
        return default
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default
    value = payload.get(key, default) if isinstance(payload, dict) else default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def output_hook(additional_context: str = "", **extra: Any) -> int:
    payload: dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context,
        }
    }
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=True))
    return 0


def correction_context() -> str:
    return "\n".join(
        [
            "[Mistakebook Trigger Report]",
            "triggerType=correction",
            "entryType=mistake_or_note",
            "runtimeStatus=armed",
            "mode=normal",
            "nextAction=load mistakebook skill, continue the same case, then answer with the fixed loop rules",
            "Do not archive until explicit user confirmation or a notebook-write request is present.",
            "",
            "Required correction activation sentence:",
            CORRECTION_ACTIVATION_SENTENCE,
            "",
            "Required correction follow-up sentence:",
            CORRECTION_FOLLOWUP_SENTENCE,
            "",
            "Required notebook follow-up sentence when a stable long-term item exists:",
            NOTE_FOLLOWUP_SENTENCE,
        ]
    )


def ascended_context() -> str:
    return "\n".join(
        [
            "[Mistakebook Trigger Report]",
            "triggerType=ascended",
            "entryType=mistake",
            "runtimeStatus=armed",
            "mode=ascended",
            "nextAction=load mistakebook skill, export full context, explain previous failure, then choose the strongest fix",
            "Do not archive until explicit user confirmation is present.",
            "",
            "Required ascended sentence:",
            ASCENDED_SENTENCE,
            "",
            "Preferred context command:",
            "python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval",
        ]
    )


def scholar_context() -> str:
    return "\n".join(
        [
            "[Mistakebook Scholar Preflight]",
            "triggerType=scholar_preflight",
            "runtimeStatus=disabled_or_normal_task",
            "mode=normal",
            "",
            "If the current user message is a fresh normal task, run scholar preflight once before the substantive answer:",
            'python scripts/mistakebook_cli.py scholar --host claude --project-root . --scope both --text "<current task>"',
            "",
            "Rules:",
            "1. Only inject the returned reminder when shouldInject = true.",
            "2. If shouldInject = false, stay silent and continue normally.",
            "3. Do not run scholar during correction, notebook capture, or Ascended Mode.",
            "4. Scholar prevents repeat mistakes; Ascended Mode still owns repeated-failure escalation.",
        ]
    )


def correction_command(_: argparse.Namespace) -> int:
    if not read_config_bool("auto_detect", True):
        return output_hook()
    return output_hook(correction_context(), triggerType="correction", runtimeStatus="armed")


def ascended_command(_: argparse.Namespace) -> int:
    return output_hook(ascended_context(), triggerType="ascended", runtimeStatus="armed")


def scholar_preflight_command(_: argparse.Namespace) -> int:
    if not read_config_bool("scholar", True):
        return output_hook()
    return output_hook(scholar_context(), triggerType="scholar_preflight", runtimeStatus="normal_task")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mistakebook UserPromptSubmit trigger report helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    correction = subparsers.add_parser("correction", help="Emit correction/notebook trigger report.")
    correction.set_defaults(func=correction_command)

    ascended = subparsers.add_parser("ascended", help="Emit Ascended Mode trigger report.")
    ascended.set_defaults(func=ascended_command)

    scholar = subparsers.add_parser("scholar-preflight", help="Emit scholar preflight trigger report.")
    scholar.set_defaults(func=scholar_preflight_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
