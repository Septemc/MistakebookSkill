#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOTS = {
    "codex": ".codex/mistakebook",
    "claude": ".claude/mistakebook",
    "vscode": ".vscode/mistakebook",
    "generic": ".mistakebook",
}

GLOBAL_ROOTS = {
    "codex": "~/.codex/mistakebook",
    "claude": "~/.claude/mistakebook",
    "vscode": "~/.vscode/mistakebook",
    "generic": "~/.mistakebook",
}

CONFIG_PATH = Path("~/.mistakebook/config.json").expanduser()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", lowered)
    lowered = lowered.strip("-")
    return lowered[:64] or "case"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_project_base(host: str, project_root: Path) -> Path:
    suffix = PROJECT_ROOTS[host]
    return project_root / Path(suffix)


def resolve_global_base(host: str, override: str | None) -> Path:
    root = override if override else GLOBAL_ROOTS[host]
    return Path(root).expanduser()


def seed_index(scope_label: str) -> str:
    return (
        f"# {scope_label}错题索引\n\n"
        f"- updated_at: {utc_now()}\n"
        f"- total_cases: 0\n"
        f"- note: 只收录已经被用户明确确认完成纠错的案例\n\n"
        "## 条目\n"
        "- 暂无\n"
    )


def seed_memory(memory_title: str) -> str:
    return (
        f"# {memory_title}\n\n"
        f"- updated_at: {utc_now()}\n"
        "- source_cases: 0\n"
        "- principle: 只保留真实、稳定、可执行、未来值得再次注入的内容\n\n"
        "## 当前稳定规则\n"
        "- 暂无\n\n"
        "## 已经吃透\n"
        "- 暂无\n\n"
        "## 高风险提醒\n"
        "- 暂无\n\n"
        "## 最近一次刷新原因\n"
        "- 初始化\n"
    )


def ensure_store(base: Path, scope: str) -> dict[str, str]:
    failures_dir = base / "failures"
    memory_dir = base / "memory"
    state_dir = base / "state"
    failures_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    index_path = failures_dir / "INDEX.md"
    catalog_path = state_dir / "catalog.json"
    if scope == "project":
        memory_path = memory_dir / "PROJECT_MEMORY.md"
        memory_title = "项目记忆"
        scope_label = "项目级"
    else:
        memory_path = memory_dir / "GLOBAL_MEMORY.md"
        memory_title = "全局记忆"
        scope_label = "全局级"

    if not index_path.exists():
        write_text(index_path, seed_index(scope_label))
    if not memory_path.exists():
        write_text(memory_path, seed_memory(memory_title))
    if not catalog_path.exists():
        write_json(catalog_path, [])

    return {
        "base": str(base),
        "failures_dir": str(failures_dir),
        "memory_dir": str(memory_dir),
        "index_path": str(index_path),
        "memory_path": str(memory_path),
        "catalog_path": str(catalog_path),
    }


def render_bullets(items: list[str], empty_message: str = "- 暂无") -> str:
    if not items:
        return empty_message
    return "\n".join(f"- {item}" for item in items)


def render_numbered(items: list[str], empty_message: str = "1. 暂无") -> str:
    if not items:
        return empty_message
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def render_case_markdown(payload: dict[str, Any], file_name: str) -> str:
    archived_at = payload.get("archivedAt") or utc_now()
    keywords = ", ".join(ensure_list(payload.get("keywords"))) or "n/a"
    ascended_reason = str(payload.get("ascendedTriggerReason", "")).strip() or "n/a"
    sections = [
        f"# {payload['title']}",
        "",
        f"- archived_at: {archived_at}",
        f"- host: {payload.get('host', 'generic')}",
        f"- session: {payload.get('sessionId', 'n/a')}",
        f"- trace: {payload.get('traceId', 'n/a')}",
        f"- case_id: {payload.get('caseId', file_name.removesuffix('.md'))}",
        f"- scope: {payload.get('scopeDecision', 'project')}",
        f"- severity: {payload.get('severity', 'n/a')}",
        f"- correction_attempt_count: {payload.get('correctionAttemptCount', 'n/a')}",
        f"- ascended_triggered: {payload.get('ascendedTriggered', False)}",
        f"- keywords: {keywords}",
        "",
        "## 错误总结",
        str(payload["summary"]).strip(),
        "",
        "## 这次到底错在哪里",
        render_bullets(ensure_list(payload.get("whatWentWrong"))),
        "",
        "## 以后必须遵守",
        render_bullets(ensure_list(payload.get("rules"))),
        "",
        "## 已经纠正并吃透的点",
        render_bullets(ensure_list(payload.get("confirmedUnderstanding"))),
        "",
        "## 下次开始前自检",
        render_bullets(ensure_list(payload.get("preventionChecklist"))),
        "",
        "## 归档范围判断",
        render_bullets(ensure_list(payload.get("scopeReasoning"))),
        "",
        "## 飞升模式记录",
        render_bullets(
            [
                f"ascended_triggered: {payload.get('ascendedTriggered', False)}",
                f"ascended_trigger_reason: {ascended_reason}",
            ]
        ),
        "",
        "## 飞升模式检索来源",
        render_bullets(ensure_list(payload.get("knowledgeSourcesReviewed"))),
        "",
        "## 原始问题",
        str(payload.get("originalPrompt", "")).strip() or "（缺失）",
        "",
        "## 原始回答",
        str(payload.get("originalReply", "")).strip() or "（缺失）",
        "",
        "## 用户纠错反馈",
        str(payload.get("correctionFeedback", "")).strip() or "（缺失）",
        "",
        "## 追纠记录",
        render_numbered(ensure_list(payload.get("followupCorrections"))),
        "",
        "## 最终正确回答",
        str(payload.get("finalReply", "")).strip() or "（缺失）",
        "",
        "## 项目记忆增量",
        render_bullets(ensure_list(payload.get("projectMemoryDelta"))),
        "",
        "## 全局记忆增量",
        render_bullets(ensure_list(payload.get("globalMemoryDelta"))),
    ]
    return "\n".join(sections)


def render_index(entries: list[dict[str, Any]], scope_label: str) -> str:
    header = [
        f"# {scope_label}错题索引",
        "",
        f"- updated_at: {utc_now()}",
        f"- total_cases: {len(entries)}",
        "- note: 只收录已经被用户明确确认完成纠错的案例",
        "",
        "## 条目",
    ]
    if not entries:
        header.append("- 暂无")
        return "\n".join(header)

    for entry in entries:
        tags = ", ".join(entry.get("keywords", [])) or "n/a"
        summary = entry.get("summary", "").strip()
        if len(summary) > 80:
            summary = summary[:77] + "..."
        header.append(
            f"- {entry['archivedAt']} | [{entry['title']}]({entry['fileName']}) | scope={entry['scopeDecision']} | tags={tags} | {summary}"
        )
    return "\n".join(header)


def fallback_memory_markdown(kind: str, payload: dict[str, Any], source_cases: int) -> str:
    title = "项目记忆" if kind == "project" else "全局记忆"
    stable_title = "当前稳定规则" if kind == "project" else "通用稳定规则"
    understood_title = "已经吃透" if kind == "project" else "通用已吃透"
    risks_title = "高风险提醒" if kind == "project" else "通用高风险提醒"
    rules = ensure_list(payload.get("rules"))
    understood = ensure_list(payload.get("confirmedUnderstanding"))
    risks = ensure_list(payload.get("whatWentWrong")) or ensure_list(payload.get("preventionChecklist"))
    reason = f"根据最新案例《{payload['title']}》自动回填"
    return (
        f"# {title}\n\n"
        f"- updated_at: {utc_now()}\n"
        f"- source_cases: {source_cases}\n"
        "- refresh_mode: fallback-generated\n\n"
        f"## {stable_title}\n"
        f"{render_bullets(rules)}\n\n"
        f"## {understood_title}\n"
        f"{render_bullets(understood)}\n\n"
        f"## {risks_title}\n"
        f"{render_bullets(risks)}\n\n"
        "## 最近一次刷新原因\n"
        f"- {reason}\n"
    )


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload_file:
        with Path(args.payload_file).open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
    elif args.payload:
        payload = json.loads(args.payload)
    else:
        raise SystemExit("archive requires --payload-file or --payload")

    for field in ("title", "summary", "originalPrompt", "originalReply", "correctionFeedback", "finalReply"):
        if field not in payload:
            raise SystemExit(f"payload missing required field: {field}")

    payload.setdefault("schemaVersion", "1.0.0")
    payload.setdefault("host", args.host)
    payload.setdefault("agentId", args.host)
    payload.setdefault("archivedAt", utc_now())
    payload.setdefault("scopeDecision", "project")
    payload.setdefault("scopeReasoning", [])
    payload.setdefault("correctionAttemptCount", 1)
    payload.setdefault("ascendedTriggered", False)
    payload.setdefault("ascendedTriggerReason", "")
    payload.setdefault("knowledgeSourcesReviewed", [])
    payload.setdefault("rules", [])
    payload.setdefault("confirmedUnderstanding", [])
    payload.setdefault("whatWentWrong", [])
    payload.setdefault("preventionChecklist", [])
    payload.setdefault("projectMemoryDelta", [])
    payload.setdefault("globalMemoryDelta", [])
    payload.setdefault("followupCorrections", [])
    payload.setdefault("keywords", [])
    payload.setdefault("severity", "medium")
    return payload


def append_entry(catalog_path: Path, payload: dict[str, Any], file_name: str) -> list[dict[str, Any]]:
    catalog = read_json(catalog_path, [])
    case_id = payload.get("caseId") or file_name.removesuffix(".md")
    catalog = [entry for entry in catalog if entry.get("caseId") != case_id]
    catalog.append(
        {
            "caseId": case_id,
            "title": payload["title"],
            "fileName": file_name,
            "archivedAt": payload["archivedAt"],
            "scopeDecision": payload["scopeDecision"],
            "keywords": ensure_list(payload.get("keywords")),
            "summary": payload["summary"],
        }
    )
    catalog.sort(key=lambda item: item["archivedAt"], reverse=True)
    write_json(catalog_path, catalog)
    return catalog


def archive_to_store(
    kind: str,
    base: Path,
    payload: dict[str, Any],
    memory_override: str | None,
) -> dict[str, Any]:
    store = ensure_store(base, kind)
    file_name = f"{timestamp_slug()}_{slugify(payload['title'])}.md"
    case_path = Path(store["failures_dir"]) / file_name
    write_text(case_path, render_case_markdown(payload, file_name))

    catalog = append_entry(Path(store["catalog_path"]), payload, file_name)
    scope_label = "项目级" if kind == "project" else "全局级"
    write_text(Path(store["index_path"]), render_index(catalog, scope_label))

    if memory_override:
        memory_content = memory_override.strip()
    else:
        memory_content = fallback_memory_markdown(kind, payload, len(catalog)).strip()
    write_text(Path(store["memory_path"]), memory_content)

    return {
        "case_path": str(case_path),
        "index_path": store["index_path"],
        "memory_path": store["memory_path"],
        "total_cases": len(catalog),
        "full_rollup_recommended": len(catalog) % 5 == 0,
    }


def bootstrap_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    result: dict[str, Any] = {"host": args.host}
    if args.scope in {"project", "both"}:
        result["project"] = ensure_store(resolve_project_base(args.host, project_root), "project")
    if args.scope in {"global", "both"}:
        result["global"] = ensure_store(resolve_global_base(args.host, args.global_root), "global")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def archive_command(args: argparse.Namespace) -> int:
    payload = load_payload(args)
    project_root = Path(args.project_root).resolve()
    scope = payload.get("scopeDecision", "project")
    result: dict[str, Any] = {"host": args.host, "scopeDecision": scope}

    if scope in {"project", "both"}:
        project_base = resolve_project_base(args.host, project_root)
        result["project"] = archive_to_store(
            "project",
            project_base,
            payload,
            payload.get("projectMemoryMarkdown"),
        )

    if scope in {"global", "both"}:
        global_base = resolve_global_base(args.host, args.global_root)
        result["global"] = archive_to_store(
            "global",
            global_base,
            payload,
            payload.get("globalMemoryMarkdown"),
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def config_command(args: argparse.Namespace) -> int:
    config = read_json(CONFIG_PATH, {})
    config["auto_detect"] = args.auto_detect == "on"
    config["updatedAt"] = utc_now()
    write_json(CONFIG_PATH, config)
    print(json.dumps(config, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mistakebook archive and storage helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap", help="Create project/global mistakebook stores.")
    bootstrap.add_argument("--host", choices=sorted(PROJECT_ROOTS), default="generic")
    bootstrap.add_argument("--project-root", default=".")
    bootstrap.add_argument("--global-root")
    bootstrap.add_argument("--scope", choices=("project", "global", "both"), default="both")
    bootstrap.set_defaults(func=bootstrap_command)

    archive = subparsers.add_parser("archive", help="Archive one correction case and refresh memories.")
    archive.add_argument("--host", choices=sorted(PROJECT_ROOTS), default="generic")
    archive.add_argument("--project-root", default=".")
    archive.add_argument("--global-root")
    archive.add_argument("--payload-file")
    archive.add_argument("--payload")
    archive.set_defaults(func=archive_command)

    config = subparsers.add_parser("config", help="Update mistakebook config.")
    config.add_argument("--auto-detect", choices=("on", "off"), required=True)
    config.set_defaults(func=config_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
