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
DEFAULT_MEMORY_THRESHOLD = 12
DEFAULT_STALE_DAYS = 45
DEFAULT_AUTO_DETECT = True
DEFAULT_SCHOLAR = True
ENTRY_TYPES = ("mistake", "note")
SCHOLAR_PHASES = ("normal", "correction", "ascended")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def days_since(now: datetime, value: Any) -> int:
    parsed = parse_timestamp(value)
    if parsed is None:
        return 999999
    return max(0, int((now - parsed).total_seconds() // 86400))


def ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def ensure_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def ensure_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ensure_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def unique_items(items: list[str], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if limit is not None and len(result) >= limit:
            break
    return result


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", lowered)
    lowered = lowered.strip("-")
    return lowered[:64] or "case"


def normalize_entry_type(value: Any) -> str:
    text = str(value or "mistake").strip().lower()
    if text in {"note", "notebook", "memo"}:
        return "note"
    return "mistake"


def entry_directory(entry_type: str) -> str:
    return "notes" if entry_type == "note" else "failures"


def entry_label(entry_type: str) -> str:
    return "记事本" if entry_type == "note" else "错题"


def entry_summary_label(entry_type: str) -> str:
    return "事项总结" if entry_type == "note" else "错误总结"


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


def normalize_config(config: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(config or {})
    payload["auto_detect"] = ensure_bool(payload.get("auto_detect"), DEFAULT_AUTO_DETECT)
    payload["scholar"] = ensure_bool(payload.get("scholar"), DEFAULT_SCHOLAR)
    return payload


def load_config() -> dict[str, Any]:
    return normalize_config(read_json(CONFIG_PATH, {}))


def seed_index(scope_label: str, entry_type: str) -> str:
    name = f"{scope_label}{entry_label(entry_type)}索引"
    if entry_type == "note":
        note = "只收录已经明确确认值得长期注意的主动事项"
    else:
        note = "只收录已经被用户明确确认完成纠错的案例"
    return (
        f"# {name}\n\n"
        f"- updated_at: {utc_now()}\n"
        f"- total_entries: 0\n"
        f"- note: {note}\n\n"
        "## 条目\n"
        "- 暂无\n"
    )


def seed_memory(memory_title: str) -> str:
    return (
        f"# {memory_title}\n\n"
        f"- updated_at: {utc_now()}\n"
        "- source_entries: 0\n"
        "- active_cache_entries: 0\n"
        "- deferred_entries: 0\n"
        f"- memory_threshold: {DEFAULT_MEMORY_THRESHOLD}\n"
        f"- stale_after_days: {DEFAULT_STALE_DAYS}\n"
        "- cache_policy: 优先保留最近命中、最近检索、仍然稳定有效的内容\n\n"
        "## 当前稳定规则\n"
        "- 暂无\n\n"
        "## 当前注意事项\n"
        "- 暂无\n\n"
        "## 已经吃透\n"
        "- 暂无\n\n"
        "## 高风险提醒\n"
        "- 暂无\n\n"
        "## 暂时遗忘候选\n"
        "- 暂无\n\n"
        "## 最近一次刷新原因\n"
        "- 初始化\n"
    )


def ensure_store(base: Path, scope: str) -> dict[str, str]:
    failures_dir = base / "failures"
    notes_dir = base / "notes"
    memory_dir = base / "memory"
    state_dir = base / "state"
    failures_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    failures_index_path = failures_dir / "INDEX.md"
    notes_index_path = notes_dir / "INDEX.md"
    catalog_path = state_dir / "catalog.json"
    memory_state_path = state_dir / "memory_state.json"
    if scope == "project":
        memory_path = memory_dir / "PROJECT_MEMORY.md"
        memory_title = "项目记忆"
        scope_label = "项目级"
    else:
        memory_path = memory_dir / "GLOBAL_MEMORY.md"
        memory_title = "全局记忆"
        scope_label = "全局级"

    if not failures_index_path.exists():
        write_text(failures_index_path, seed_index(scope_label, "mistake"))
    if not notes_index_path.exists():
        write_text(notes_index_path, seed_index(scope_label, "note"))
    if not memory_path.exists():
        write_text(memory_path, seed_memory(memory_title))
    if not catalog_path.exists():
        write_json(catalog_path, [])
    if not memory_state_path.exists():
        write_json(memory_state_path, {"updatedAt": utc_now(), "activeEntries": [], "deferredEntries": []})

    return {
        "base": str(base),
        "failures_dir": str(failures_dir),
        "notes_dir": str(notes_dir),
        "failures_index_path": str(failures_index_path),
        "notes_index_path": str(notes_index_path),
        "memory_dir": str(memory_dir),
        "memory_path": str(memory_path),
        "memory_state_path": str(memory_state_path),
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


def render_entry_markdown(payload: dict[str, Any], file_name: str) -> str:
    entry_type = normalize_entry_type(payload.get("entryType"))
    archived_at = payload.get("archivedAt") or utc_now()
    keywords = ", ".join(ensure_list(payload.get("keywords"))) or "n/a"
    ascended_reason = str(payload.get("ascendedTriggerReason", "")).strip() or "n/a"
    common_prefix = [
        f"# {payload['title']}",
        "",
        f"- entry_type: {entry_type}",
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
        f"## {entry_summary_label(entry_type)}",
        str(payload["summary"]).strip(),
        "",
    ]

    if entry_type == "note":
        sections = common_prefix + [
            "## 为什么值得记录",
            str(payload.get("noteReason", "")).strip() or "（缺失）",
            "",
            "## 需要注意",
            render_bullets(ensure_list(payload.get("noteContent")) or ensure_list(payload.get("rules"))),
            "",
            "## 建议行动",
            render_bullets(ensure_list(payload.get("noteActionItems")) or ensure_list(payload.get("preventionChecklist"))),
            "",
            "## 来源上下文",
            str(payload.get("noteContext", "")).strip() or str(payload.get("originalPrompt", "")).strip() or "（缺失）",
            "",
            "## 已经确认的稳定规则",
            render_bullets(ensure_list(payload.get("rules"))),
            "",
            "## 已经吃透的点",
            render_bullets(ensure_list(payload.get("confirmedUnderstanding"))),
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
            "## 相关原始问题",
            str(payload.get("originalPrompt", "")).strip() or "（缺失）",
            "",
            "## 相关回答或方案",
            str(payload.get("finalReply", "")).strip()
            or str(payload.get("originalReply", "")).strip()
            or "（缺失）",
            "",
            "## 项目记忆增量",
            render_bullets(ensure_list(payload.get("projectMemoryDelta"))),
            "",
            "## 全局记忆增量",
            render_bullets(ensure_list(payload.get("globalMemoryDelta"))),
        ]
        return "\n".join(sections)

    sections = common_prefix + [
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


def normalize_catalog_entry(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(entry)
    entry_type = normalize_entry_type(normalized.get("entryType"))
    file_name = str(normalized.get("fileName") or "").strip()
    case_id = str(normalized.get("caseId") or file_name.removesuffix(".md") or slugify(normalized.get("title", "")))
    relative_path = str(normalized.get("relativePath") or f"{entry_directory(entry_type)}/{file_name}").strip()

    normalized["caseId"] = case_id
    normalized["entryType"] = entry_type
    normalized["title"] = str(normalized.get("title") or case_id).strip()
    normalized["fileName"] = file_name
    normalized["relativePath"] = relative_path
    normalized["archivedAt"] = str(normalized.get("archivedAt") or utc_now()).strip()
    normalized["updatedAt"] = str(normalized.get("updatedAt") or normalized["archivedAt"]).strip()
    normalized["scopeDecision"] = str(normalized.get("scopeDecision") or "project").strip()
    normalized["summary"] = str(normalized.get("summary") or "").strip()
    normalized["keywords"] = ensure_list(normalized.get("keywords"))
    normalized["rules"] = ensure_list(normalized.get("rules"))
    normalized["confirmedUnderstanding"] = ensure_list(normalized.get("confirmedUnderstanding"))
    normalized["whatWentWrong"] = ensure_list(normalized.get("whatWentWrong"))
    normalized["preventionChecklist"] = ensure_list(normalized.get("preventionChecklist"))
    normalized["projectMemoryDelta"] = ensure_list(normalized.get("projectMemoryDelta"))
    normalized["globalMemoryDelta"] = ensure_list(normalized.get("globalMemoryDelta"))
    normalized["knowledgeSourcesReviewed"] = ensure_list(normalized.get("knowledgeSourcesReviewed"))
    normalized["correctionAttemptCount"] = ensure_int(normalized.get("correctionAttemptCount"), 1)
    normalized["ascendedTriggered"] = ensure_bool(normalized.get("ascendedTriggered"), False)
    normalized["ascendedTriggerReason"] = str(normalized.get("ascendedTriggerReason") or "").strip()
    normalized["noteContent"] = ensure_list(normalized.get("noteContent"))
    normalized["noteActionItems"] = ensure_list(normalized.get("noteActionItems"))
    normalized["noteContext"] = str(normalized.get("noteContext") or "").strip()
    normalized["noteReason"] = str(normalized.get("noteReason") or "").strip()
    normalized["retrievalCount"] = ensure_int(normalized.get("retrievalCount"), 0)
    normalized["lastRetrievedAt"] = str(normalized.get("lastRetrievedAt") or "").strip()
    normalized["hitCount"] = ensure_int(normalized.get("hitCount"), 0)
    normalized["lastHitAt"] = str(normalized.get("lastHitAt") or "").strip()
    normalized["memoryPriority"] = ensure_float(normalized.get("memoryPriority"), 0.0)
    return normalized


def load_catalog(catalog_path: Path) -> list[dict[str, Any]]:
    return [normalize_catalog_entry(item) for item in read_json(catalog_path, [])]


def write_catalog(catalog_path: Path, catalog: list[dict[str, Any]]) -> None:
    catalog.sort(key=lambda item: item["archivedAt"], reverse=True)
    write_json(catalog_path, catalog)


def render_index(entries: list[dict[str, Any]], scope_label: str, entry_type: str) -> str:
    filtered = [entry for entry in entries if normalize_entry_type(entry.get("entryType")) == entry_type]
    header = [
        f"# {scope_label}{entry_label(entry_type)}索引",
        "",
        f"- updated_at: {utc_now()}",
        f"- total_entries: {len(filtered)}",
        "- note: 只展示当前仍可回放的结构化条目",
        "",
        "## 条目",
    ]
    if not filtered:
        header.append("- 暂无")
        return "\n".join(header)

    for entry in filtered:
        tags = ", ".join(entry.get("keywords", [])) or "n/a"
        summary = entry.get("summary", "").strip()
        if len(summary) > 80:
            summary = summary[:77] + "..."
        path = entry.get("relativePath") or f"{entry_directory(entry_type)}/{entry['fileName']}"
        header.append(
            f"- {entry['archivedAt']} | [{entry['title']}]({path}) | type={entry_type} | scope={entry['scopeDecision']} | tags={tags} | {summary}"
        )
    return "\n".join(header)


def build_catalog_entry(payload: dict[str, Any], file_name: str) -> dict[str, Any]:
    entry_type = normalize_entry_type(payload.get("entryType"))
    case_id = str(payload.get("caseId") or file_name.removesuffix(".md")).strip()
    return normalize_catalog_entry(
        {
            "caseId": case_id,
            "entryType": entry_type,
            "title": payload["title"],
            "fileName": file_name,
            "relativePath": f"{entry_directory(entry_type)}/{file_name}",
            "archivedAt": payload["archivedAt"],
            "updatedAt": utc_now(),
            "scopeDecision": payload["scopeDecision"],
            "keywords": ensure_list(payload.get("keywords")),
            "summary": payload["summary"],
            "rules": ensure_list(payload.get("rules")),
            "confirmedUnderstanding": ensure_list(payload.get("confirmedUnderstanding")),
            "whatWentWrong": ensure_list(payload.get("whatWentWrong")),
            "preventionChecklist": ensure_list(payload.get("preventionChecklist")),
            "projectMemoryDelta": ensure_list(payload.get("projectMemoryDelta")),
            "globalMemoryDelta": ensure_list(payload.get("globalMemoryDelta")),
            "knowledgeSourcesReviewed": ensure_list(payload.get("knowledgeSourcesReviewed")),
            "correctionAttemptCount": payload.get("correctionAttemptCount", 1),
            "ascendedTriggered": payload.get("ascendedTriggered", False),
            "ascendedTriggerReason": payload.get("ascendedTriggerReason", ""),
            "noteContent": ensure_list(payload.get("noteContent")),
            "noteActionItems": ensure_list(payload.get("noteActionItems")),
            "noteContext": payload.get("noteContext", ""),
            "noteReason": payload.get("noteReason", ""),
            "retrievalCount": payload.get("retrievalCount", 0),
            "lastRetrievedAt": payload.get("lastRetrievedAt", ""),
            "hitCount": payload.get("hitCount", 0),
            "lastHitAt": payload.get("lastHitAt", ""),
            "memoryPriority": payload.get("memoryPriority", 0.0),
        }
    )


def merge_with_previous_metrics(new_entry: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    if previous is None:
        return new_entry
    merged = dict(new_entry)
    merged["retrievalCount"] = ensure_int(new_entry.get("retrievalCount"), ensure_int(previous.get("retrievalCount"), 0))
    merged["lastRetrievedAt"] = str(new_entry.get("lastRetrievedAt") or previous.get("lastRetrievedAt") or "").strip()
    merged["hitCount"] = ensure_int(new_entry.get("hitCount"), ensure_int(previous.get("hitCount"), 0))
    merged["lastHitAt"] = str(new_entry.get("lastHitAt") or previous.get("lastHitAt") or "").strip()
    merged["memoryPriority"] = ensure_float(new_entry.get("memoryPriority"), ensure_float(previous.get("memoryPriority"), 0.0))
    return normalize_catalog_entry(merged)


def append_entry(catalog_path: Path, payload: dict[str, Any], file_name: str) -> list[dict[str, Any]]:
    catalog = load_catalog(catalog_path)
    case_id = str(payload.get("caseId") or file_name.removesuffix(".md")).strip()
    previous = next((entry for entry in catalog if entry.get("caseId") == case_id), None)
    catalog = [entry for entry in catalog if entry.get("caseId") != case_id]
    new_entry = build_catalog_entry(payload, file_name)
    catalog.append(merge_with_previous_metrics(new_entry, previous))
    write_catalog(catalog_path, catalog)
    return load_catalog(catalog_path)


def compute_entry_score(entry: dict[str, Any], now: datetime, stale_days: int) -> dict[str, Any]:
    normalized = normalize_catalog_entry(entry)
    age_days = days_since(now, normalized.get("archivedAt"))
    last_signal = normalized.get("lastHitAt") or normalized.get("lastRetrievedAt") or normalized.get("archivedAt")
    idle_days = days_since(now, last_signal)
    hit_count = ensure_int(normalized.get("hitCount"), 0)
    retrieval_count = ensure_int(normalized.get("retrievalCount"), 0)
    hit_probability = (hit_count + 1.0) / (retrieval_count + 2.0)
    freshness_score = max(0.0, 2.5 - age_days / 30.0)
    engagement_score = max(0.0, 2.0 - idle_days / 30.0)
    score = (
        ensure_float(normalized.get("memoryPriority"), 0.0)
        + freshness_score
        + engagement_score
        + hit_probability * 3.0
        + hit_count * 1.5
        + retrieval_count * 0.5
        + (0.4 if normalized.get("entryType") == "note" else 0.0)
        + (0.3 if ensure_bool(normalized.get("ascendedTriggered"), False) else 0.0)
    )
    stale_candidate = idle_days > stale_days and hit_probability < 0.55 and hit_count == 0
    decorated = dict(normalized)
    decorated["_memoryScore"] = round(score, 4)
    decorated["_hitProbability"] = round(hit_probability, 4)
    decorated["_ageDays"] = age_days
    decorated["_idleDays"] = idle_days
    decorated["_staleCandidate"] = stale_candidate
    return decorated


QUERY_FIELD_WEIGHTS: dict[str, float] = {
    "title": 4.5,
    "summary": 3.5,
    "keywords": 3.5,
    "rules": 3.0,
    "confirmedUnderstanding": 2.5,
    "whatWentWrong": 2.0,
    "preventionChecklist": 2.0,
    "noteContent": 2.5,
    "noteActionItems": 2.0,
    "noteReason": 1.8,
    "noteContext": 1.2,
    "projectMemoryDelta": 1.5,
    "globalMemoryDelta": 1.5,
}


def normalize_query_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def extract_query_terms(text: str, limit: int = 24) -> list[str]:
    normalized = normalize_query_text(text)
    terms: set[str] = set()
    for segment in re.findall(r"[a-z0-9_+-]+|[\u4e00-\u9fff]+", normalized):
        if not segment:
            continue
        if re.fullmatch(r"[a-z0-9_+-]+", segment):
            if len(segment) >= 2:
                terms.add(segment)
            continue
        terms.add(segment)
        for size in (4, 3, 2):
            if len(segment) < size:
                continue
            for index in range(len(segment) - size + 1):
                terms.add(segment[index : index + size])
    ordered = sorted(terms, key=lambda item: (-len(item), item))
    return ordered[:limit]


def build_query_field_values(entry: dict[str, Any]) -> dict[str, list[str]]:
    normalized = normalize_catalog_entry(entry)
    field_values: dict[str, list[str]] = {}
    for field in QUERY_FIELD_WEIGHTS:
        value = normalized.get(field)
        if isinstance(value, list):
            field_values[field] = [normalize_query_text(item) for item in value if normalize_query_text(item)]
        else:
            text = normalize_query_text(value)
            field_values[field] = [text] if text else []
    return field_values


def query_catalog_entry(entry: dict[str, Any], query_text: str, stale_days: int, store_scope: str) -> dict[str, Any] | None:
    normalized_query = normalize_query_text(query_text)
    terms = extract_query_terms(normalized_query)
    if not normalized_query:
        return None

    decorated = compute_entry_score(entry, datetime.now(timezone.utc), stale_days)
    field_values = build_query_field_values(decorated)
    matched_terms: list[str] = []
    match_reasons: list[str] = []
    lexical_score = 0.0
    any_match = False

    for field, weight in QUERY_FIELD_WEIGHTS.items():
        values = field_values.get(field, [])
        if not values:
            continue
        query_hit = any(normalized_query in value for value in values)
        term_hits = [term for term in terms if any(term in value for value in values)]
        if not query_hit and not term_hits:
            continue
        any_match = True
        field_score = weight * (1.6 if query_hit else 1.0 + 0.15 * min(len(term_hits), 3))
        lexical_score += field_score
        if query_hit:
            match_reasons.append(f"{field}:query")
            matched_terms.append(normalized_query)
        elif term_hits:
            match_reasons.append(f"{field}:{','.join(term_hits[:3])}")
        matched_terms.extend(term_hits[:4])

    if not any_match:
        return None

    unique_terms = unique_items(matched_terms, limit=12)
    unique_reasons = unique_items(match_reasons, limit=8)
    result = {
        "storeScope": store_scope,
        "caseId": decorated["caseId"],
        "entryType": decorated["entryType"],
        "title": decorated["title"],
        "summary": decorated["summary"],
        "relativePath": decorated["relativePath"],
        "scopeDecision": decorated["scopeDecision"],
        "archivedAt": decorated["archivedAt"],
        "score": round(decorated["_memoryScore"] + lexical_score, 4),
        "memoryScore": decorated["_memoryScore"],
        "matchedTerms": unique_terms,
        "matchReasons": unique_reasons,
        "keywords": decorated["keywords"],
        "hitCount": decorated["hitCount"],
        "retrievalCount": decorated["retrievalCount"],
    }
    return result


def query_catalog(
    catalog: list[dict[str, Any]],
    query_text: str,
    stale_days: int,
    store_scope: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for entry in catalog:
        match = query_catalog_entry(entry, query_text, stale_days, store_scope)
        if match is not None:
            results.append(match)
    results.sort(key=lambda item: (item["score"], item["memoryScore"], item["archivedAt"]), reverse=True)
    return results


def query_store(
    host: str,
    store_scope: str,
    project_root: Path,
    global_root: str | None,
    query_text: str,
    stale_days: int,
) -> list[dict[str, Any]]:
    base = resolve_project_base(host, project_root) if store_scope == "project" else resolve_global_base(host, global_root)
    store = ensure_store(base, store_scope)
    catalog = load_catalog(Path(store["catalog_path"]))
    return query_catalog(catalog, query_text, stale_days, store_scope)


def trim_scholar_hint(text: Any, limit: int = 80) -> str:
    normalized = re.sub(r"\s+", " ", str(text or "").strip())
    normalized = normalized.rstrip("。.!?;；：:，,")
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def build_scholar_guidance(entry: dict[str, Any]) -> str:
    candidates = (
        ensure_list(entry.get("rules"))
        + ensure_list(entry.get("confirmedUnderstanding"))
        + ensure_list(entry.get("noteContent"))
    )
    if not candidates:
        candidates = ensure_list(entry.get("summary"))
    return trim_scholar_hint(candidates[0] if candidates else "")


def build_scholar_message(entry: dict[str, Any]) -> str:
    title = trim_scholar_hint(entry.get("title"), limit=48)
    guidance = build_scholar_guidance(entry)
    if not guidance:
        return f'历史提醒：这个任务和“{title}”高度相关，这次先复用这条经验。'
    if guidance.startswith(("先", "先把", "优先", "避免", "检查", "确认")):
        return f'历史提醒：这个任务和“{title}”高度相关，这次{guidance}。'
    return f'历史提醒：这个任务和“{title}”高度相关，这次先{guidance}。'


def classify_scholar_confidence(results: list[dict[str, Any]]) -> str:
    if not results:
        return "none"
    top_result = results[0]
    second_score = results[1]["score"] if len(results) > 1 else 0.0
    score_gap = top_result["score"] - second_score
    direct_query_match = any(reason.endswith(":query") for reason in top_result["matchReasons"])
    strong_support = len(top_result["matchReasons"]) >= 2 or len(top_result["matchedTerms"]) >= 2
    dense_lexical_match = len(top_result["matchedTerms"]) >= 3

    if (
        top_result["score"] >= 12.0
        and strong_support
        and (direct_query_match or dense_lexical_match)
        and (len(results) == 1 or score_gap >= 1.5)
    ):
        return "high"
    if top_result["score"] >= 8.0 and (direct_query_match or strong_support):
        return "medium"
    if top_result["score"] >= 6.0:
        return "low"
    return "none"


def collect_scholar_results(
    host: str,
    scope: str,
    project_root: Path,
    global_root: str | None,
    query_text: str,
    stale_days: int,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    combined_results: list[dict[str, Any]] = []
    entry_lookup: dict[tuple[str, str], dict[str, Any]] = {}

    for store_scope in ("project", "global"):
        if scope not in {store_scope, "both"}:
            continue
        base = resolve_project_base(host, project_root) if store_scope == "project" else resolve_global_base(host, global_root)
        store = ensure_store(base, store_scope)
        catalog = load_catalog(Path(store["catalog_path"]))
        for entry in catalog:
            entry_lookup[(store_scope, entry["caseId"])] = entry
        combined_results.extend(query_catalog(catalog, query_text, stale_days, store_scope))

    combined_results.sort(key=lambda item: (item["score"], item["memoryScore"], item["archivedAt"]), reverse=True)
    return combined_results, entry_lookup


def select_memory_entries(
    catalog: list[dict[str, Any]],
    threshold: int,
    stale_days: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    now = datetime.now(timezone.utc)
    decorated = [compute_entry_score(entry, now, stale_days) for entry in catalog]
    decorated.sort(
        key=lambda item: (
            item["_staleCandidate"],
            -item["_memoryScore"],
            item["_idleDays"],
            item["archivedAt"],
        )
    )

    if len(decorated) <= threshold:
        active = decorated
        deferred: list[dict[str, Any]] = []
    else:
        active = decorated[:threshold]
        deferred = decorated[threshold:]

    for item in deferred:
        if item["_staleCandidate"]:
            item["_deferredReason"] = "长期未命中且最近没有被重新检索，暂时移出缓存"
        else:
            item["_deferredReason"] = "当前缓存已超过阈值，暂时保留在详细条目中"

    return active, deferred


def collect_section_items(kind: str, active_entries: list[dict[str, Any]], section: str, limit: int = 10) -> list[str]:
    collected: list[str] = []
    for entry in active_entries:
        if section == "rules":
            collected.extend(ensure_list(entry.get("rules")))
            if kind == "project":
                collected.extend(ensure_list(entry.get("projectMemoryDelta")))
            else:
                collected.extend(ensure_list(entry.get("globalMemoryDelta")))
        elif section == "notes":
            if entry.get("entryType") == "note":
                collected.extend(ensure_list(entry.get("noteContent")))
                collected.extend(ensure_list(entry.get("noteActionItems")))
            elif kind == "project":
                collected.extend(ensure_list(entry.get("projectMemoryDelta")))
            else:
                collected.extend(ensure_list(entry.get("globalMemoryDelta")))
        elif section == "understood":
            collected.extend(ensure_list(entry.get("confirmedUnderstanding")))
        elif section == "risks":
            collected.extend(ensure_list(entry.get("whatWentWrong")))
            collected.extend(ensure_list(entry.get("preventionChecklist")))
        else:
            raise ValueError(f"unknown section: {section}")
    return unique_items(collected, limit=limit)


def build_deferred_candidates(deferred_entries: list[dict[str, Any]], limit: int = 6) -> list[str]:
    items: list[str] = []
    for entry in deferred_entries[:limit]:
        label = entry_label(normalize_entry_type(entry.get("entryType")))
        items.append(f"{entry['title']}（{label}，score={entry['_memoryScore']}）：{entry['_deferredReason']}")
    return items


def build_memory_markdown(
    kind: str,
    active_entries: list[dict[str, Any]],
    deferred_entries: list[dict[str, Any]],
    total_entries: int,
    threshold: int,
    stale_days: int,
    reason: str,
) -> str:
    title = "项目记忆" if kind == "project" else "全局记忆"
    rules_title = "当前稳定规则" if kind == "project" else "通用稳定规则"
    notes_title = "当前注意事项" if kind == "project" else "通用注意事项"
    understood_title = "已经吃透" if kind == "project" else "通用已吃透"
    risks_title = "高风险提醒" if kind == "project" else "通用高风险提醒"
    rules = collect_section_items(kind, active_entries, "rules")
    notes = collect_section_items(kind, active_entries, "notes")
    understood = collect_section_items(kind, active_entries, "understood")
    risks = collect_section_items(kind, active_entries, "risks")
    deferred = build_deferred_candidates(deferred_entries)

    return (
        f"# {title}\n\n"
        f"- updated_at: {utc_now()}\n"
        f"- source_entries: {total_entries}\n"
        f"- active_cache_entries: {len(active_entries)}\n"
        f"- deferred_entries: {len(deferred_entries)}\n"
        f"- memory_threshold: {threshold}\n"
        f"- stale_after_days: {stale_days}\n"
        "- cache_policy: 优先保留最近命中、最近检索、仍然稳定有效的内容；旧且低命中的内容暂时退出缓存，但仍保留在详细条目里\n\n"
        f"## {rules_title}\n"
        f"{render_bullets(rules)}\n\n"
        f"## {notes_title}\n"
        f"{render_bullets(notes)}\n\n"
        f"## {understood_title}\n"
        f"{render_bullets(understood)}\n\n"
        f"## {risks_title}\n"
        f"{render_bullets(risks)}\n\n"
        "## 暂时遗忘候选\n"
        f"{render_bullets(deferred)}\n\n"
        "## 最近一次刷新原因\n"
        f"- {reason}\n"
    )


def build_memory_state(
    kind: str,
    active_entries: list[dict[str, Any]],
    deferred_entries: list[dict[str, Any]],
    threshold: int,
    stale_days: int,
    reason: str,
) -> dict[str, Any]:
    return {
        "updatedAt": utc_now(),
        "kind": kind,
        "memoryThreshold": threshold,
        "staleAfterDays": stale_days,
        "reason": reason,
        "activeEntries": [
            {
                "caseId": entry["caseId"],
                "title": entry["title"],
                "entryType": entry["entryType"],
                "memoryScore": entry["_memoryScore"],
                "hitProbability": entry["_hitProbability"],
                "retrievalCount": entry["retrievalCount"],
                "hitCount": entry["hitCount"],
                "idleDays": entry["_idleDays"],
            }
            for entry in active_entries
        ],
        "deferredEntries": [
            {
                "caseId": entry["caseId"],
                "title": entry["title"],
                "entryType": entry["entryType"],
                "memoryScore": entry["_memoryScore"],
                "hitProbability": entry["_hitProbability"],
                "retrievalCount": entry["retrievalCount"],
                "hitCount": entry["hitCount"],
                "idleDays": entry["_idleDays"],
                "reason": entry["_deferredReason"],
            }
            for entry in deferred_entries
        ],
    }


def rewrite_indices(store: dict[str, str], catalog: list[dict[str, Any]], scope_label: str) -> None:
    write_text(Path(store["failures_index_path"]), render_index(catalog, scope_label, "mistake"))
    write_text(Path(store["notes_index_path"]), render_index(catalog, scope_label, "note"))


def refresh_store_memory(
    kind: str,
    base: Path,
    threshold: int,
    stale_days: int,
    reason: str,
    memory_override: str | None = None,
) -> dict[str, Any]:
    store = ensure_store(base, kind)
    catalog = load_catalog(Path(store["catalog_path"]))
    active_entries, deferred_entries = select_memory_entries(catalog, threshold, stale_days)
    if memory_override:
        memory_content = memory_override.strip()
    else:
        memory_content = build_memory_markdown(
            kind,
            active_entries,
            deferred_entries,
            len(catalog),
            threshold,
            stale_days,
            reason,
        ).strip()
    write_text(Path(store["memory_path"]), memory_content)
    memory_state = build_memory_state(kind, active_entries, deferred_entries, threshold, stale_days, reason)
    write_json(Path(store["memory_state_path"]), memory_state)
    rewrite_indices(store, catalog, "项目级" if kind == "project" else "全局级")
    return {
        "memory_path": store["memory_path"],
        "memory_state_path": store["memory_state_path"],
        "total_entries": len(catalog),
        "active_cache_entries": len(active_entries),
        "deferred_entries": len(deferred_entries),
        "threshold": threshold,
        "stale_after_days": stale_days,
    }


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload_sources = [bool(args.payload_file), bool(args.payload), bool(getattr(args, "payload_stdin", False))]
    provided_sources = sum(1 for source in payload_sources if source)
    if provided_sources == 0:
        raise SystemExit("archive requires exactly one of --payload-file, --payload, or --payload-stdin")
    if provided_sources > 1:
        raise SystemExit("archive accepts only one of --payload-file, --payload, or --payload-stdin")

    if args.payload_file:
        with Path(args.payload_file).open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
    elif args.payload:
        payload = json.loads(args.payload)
    elif getattr(args, "payload_stdin", False):
        raw_payload = sys.stdin.read()
        if not raw_payload.strip():
            raise SystemExit("archive received empty stdin payload")
        try:
            payload = json.loads(raw_payload.lstrip("\ufeff"))
        except json.JSONDecodeError as exc:
            raise SystemExit("archive failed to parse JSON from stdin") from exc
    else:
        raise SystemExit("archive requires exactly one of --payload-file, --payload, or --payload-stdin")

    if args.entry_type:
        payload["entryType"] = args.entry_type

    for field in ("title", "summary"):
        if field not in payload or not str(payload[field]).strip():
            raise SystemExit(f"payload missing required field: {field}")

    entry_type = normalize_entry_type(payload.get("entryType"))
    payload["entryType"] = entry_type
    payload.setdefault("schemaVersion", "2.0.0")
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
    payload.setdefault("memoryPriority", 0.0)
    payload.setdefault("retrievalCount", 0)
    payload.setdefault("lastRetrievedAt", "")
    payload.setdefault("hitCount", 0)
    payload.setdefault("lastHitAt", "")
    payload.setdefault("originalPrompt", "")
    payload.setdefault("originalReply", "")
    payload.setdefault("correctionFeedback", "")
    payload.setdefault("finalReply", "")
    payload.setdefault("noteContent", [])
    payload.setdefault("noteActionItems", [])
    payload.setdefault("noteContext", "")
    payload.setdefault("noteReason", "")

    if entry_type == "note" and not ensure_list(payload.get("noteContent")):
        payload["noteContent"] = ensure_list(payload.get("summary"))

    return payload


def archive_to_store(
    kind: str,
    base: Path,
    payload: dict[str, Any],
    threshold: int,
    stale_days: int,
    memory_override: str | None,
) -> dict[str, Any]:
    store = ensure_store(base, kind)
    entry_type = normalize_entry_type(payload.get("entryType"))
    file_name = f"{timestamp_slug()}_{slugify(payload['title'])}.md"
    case_path = Path(store[f"{entry_directory(entry_type)}_dir"]) / file_name
    write_text(case_path, render_entry_markdown(payload, file_name))

    catalog = append_entry(Path(store["catalog_path"]), payload, file_name)
    scope_label = "项目级" if kind == "project" else "全局级"
    rewrite_indices(store, catalog, scope_label)

    memory_result = refresh_store_memory(
        kind,
        base,
        threshold,
        stale_days,
        reason=f"新增{entry_label(entry_type)}《{payload['title']}》后刷新缓存记忆",
        memory_override=memory_override,
    )

    return {
        "entry_type": entry_type,
        "case_path": str(case_path),
        "index_path": store[f"{entry_directory(entry_type)}_index_path"],
        **memory_result,
    }


def touch_catalog_entries(
    catalog: list[dict[str, Any]],
    case_ids: set[str],
    kind: str,
    count: int,
    when: str,
) -> tuple[list[dict[str, Any]], int]:
    updated_count = 0
    metric_field = "hitCount" if kind == "hit" else "retrievalCount"
    time_field = "lastHitAt" if kind == "hit" else "lastRetrievedAt"
    for entry in catalog:
        if entry.get("caseId") not in case_ids:
            continue
        entry[metric_field] = ensure_int(entry.get(metric_field), 0) + count
        entry[time_field] = when
        entry["updatedAt"] = when
        updated_count += 1
    return catalog, updated_count


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
    result: dict[str, Any] = {
        "host": args.host,
        "scopeDecision": scope,
        "entryType": payload["entryType"],
    }

    if scope in {"project", "both"}:
        project_base = resolve_project_base(args.host, project_root)
        result["project"] = archive_to_store(
            "project",
            project_base,
            payload,
            args.memory_threshold,
            args.stale_days,
            payload.get("projectMemoryMarkdown"),
        )

    if scope in {"global", "both"}:
        global_base = resolve_global_base(args.host, args.global_root)
        result["global"] = archive_to_store(
            "global",
            global_base,
            payload,
            args.memory_threshold,
            args.stale_days,
            payload.get("globalMemoryMarkdown"),
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def consolidate_scope(
    host: str,
    store_scope: str,
    project_root: Path,
    global_root: str | None,
    threshold: int,
    stale_days: int,
    reason: str,
) -> dict[str, Any]:
    if store_scope == "project":
        base = resolve_project_base(host, project_root)
    else:
        base = resolve_global_base(host, global_root)
    result = refresh_store_memory(store_scope, base, threshold, stale_days, reason)
    result["base"] = str(base)
    return result


def consolidate_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    result: dict[str, Any] = {"host": args.host, "scope": args.scope}
    reason = args.reason or "执行 consolidate，按缓存阈值与命中情况重写记忆"
    if args.scope in {"project", "both"}:
        result["project"] = consolidate_scope(
            args.host,
            "project",
            project_root,
            args.global_root,
            args.memory_threshold,
            args.stale_days,
            reason,
        )
    if args.scope in {"global", "both"}:
        result["global"] = consolidate_scope(
            args.host,
            "global",
            project_root,
            args.global_root,
            args.memory_threshold,
            args.stale_days,
            reason,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def touch_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    case_ids = {case_id.strip() for case_id in args.case_id if case_id.strip()}
    when = args.when or utc_now()
    result: dict[str, Any] = {"host": args.host, "kind": args.kind, "caseIds": sorted(case_ids)}
    updated_any = 0

    for store_scope in ("project", "global"):
        if args.scope not in {store_scope, "both"}:
            continue
        base = resolve_project_base(args.host, project_root) if store_scope == "project" else resolve_global_base(args.host, args.global_root)
        store = ensure_store(base, store_scope)
        catalog_path = Path(store["catalog_path"])
        catalog = load_catalog(catalog_path)
        catalog, updated_count = touch_catalog_entries(catalog, case_ids, args.kind, args.count, when)
        if updated_count == 0:
            continue
        updated_any += updated_count
        write_catalog(catalog_path, catalog)
        memory_result = refresh_store_memory(
            store_scope,
            base,
            args.memory_threshold,
            args.stale_days,
            reason=f"记录缓存命中事件（{args.kind}）后刷新记忆",
        )
        result[store_scope] = {
            "updated_entries": updated_count,
            **memory_result,
        }

    if updated_any == 0:
        raise SystemExit("touch did not find any matching caseId in the selected stores")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def load_scope_context(
    host: str,
    store_scope: str,
    project_root: Path,
    global_root: str | None,
    mark_retrieval: bool,
    threshold: int,
    stale_days: int,
) -> dict[str, Any]:
    base = resolve_project_base(host, project_root) if store_scope == "project" else resolve_global_base(host, global_root)
    store = ensure_store(base, store_scope)
    catalog_path = Path(store["catalog_path"])
    catalog = load_catalog(catalog_path)

    if mark_retrieval and catalog:
        case_ids = {entry["caseId"] for entry in catalog}
        catalog, _ = touch_catalog_entries(catalog, case_ids, "retrieval", 1, utc_now())
        write_catalog(catalog_path, catalog)
        refresh_store_memory(
            store_scope,
            base,
            threshold,
            stale_days,
            reason="飞升模式读取全部错题与记事本后刷新缓存记忆",
        )
        catalog = load_catalog(catalog_path)

    memory_markdown = Path(store["memory_path"]).read_text(encoding="utf-8") if Path(store["memory_path"]).exists() else ""
    memory_state = read_json(Path(store["memory_state_path"]), {})
    return {
        "base": str(base),
        "memoryPath": store["memory_path"],
        "memoryMarkdown": memory_markdown,
        "memoryState": memory_state,
        "mistakes": [entry for entry in catalog if entry.get("entryType") == "mistake"],
        "notes": [entry for entry in catalog if entry.get("entryType") == "note"],
    }


def annotate_full_scope_context(scope_context: dict[str, Any], limit: int) -> dict[str, Any]:
    total_entries = len(scope_context["mistakes"]) + len(scope_context["notes"])
    result = dict(scope_context)
    result.update(
        {
            "pruned": False,
            "query": "",
            "limit": limit,
            "totalEntries": total_entries,
            "returnedEntries": total_entries,
        }
    )
    return result


def load_pruned_scope_context(
    host: str,
    store_scope: str,
    project_root: Path,
    global_root: str | None,
    mark_retrieval: bool,
    threshold: int,
    stale_days: int,
    query_text: str,
    limit: int,
) -> dict[str, Any]:
    base = resolve_project_base(host, project_root) if store_scope == "project" else resolve_global_base(host, global_root)
    store = ensure_store(base, store_scope)
    catalog_path = Path(store["catalog_path"])
    catalog = load_catalog(catalog_path)
    ranked_results = query_catalog(catalog, query_text, stale_days, store_scope)
    selected_case_ids = [entry["caseId"] for entry in ranked_results[:limit]]

    if mark_retrieval and selected_case_ids:
        catalog, _ = touch_catalog_entries(catalog, set(selected_case_ids), "retrieval", 1, utc_now())
        write_catalog(catalog_path, catalog)
        refresh_store_memory(
            store_scope,
            base,
            threshold,
            stale_days,
            reason="Refresh memory after exporting pruned ascended context.",
        )
        catalog = load_catalog(catalog_path)

    catalog_by_case_id = {entry["caseId"]: entry for entry in catalog}
    selected_catalog = [catalog_by_case_id[case_id] for case_id in selected_case_ids if case_id in catalog_by_case_id]
    memory_markdown = Path(store["memory_path"]).read_text(encoding="utf-8") if Path(store["memory_path"]).exists() else ""
    memory_state = read_json(Path(store["memory_state_path"]), {})
    return {
        "base": str(base),
        "pruned": True,
        "query": query_text,
        "limit": limit,
        "totalEntries": len(catalog),
        "returnedEntries": len(selected_catalog),
        "memoryPath": store["memory_path"],
        "memoryMarkdown": memory_markdown,
        "memoryState": memory_state,
        "mistakes": [entry for entry in selected_catalog if entry.get("entryType") == "mistake"],
        "notes": [entry for entry in selected_catalog if entry.get("entryType") == "note"],
    }


def context_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    query_text = str(args.query or "").strip()
    if args.query is not None and not query_text:
        raise SystemExit("context requires non-empty --query")
    if args.limit < 1:
        raise SystemExit("context requires --limit >= 1")
    result: dict[str, Any] = {
        "host": args.host,
        "scope": args.scope,
        "generatedAt": utc_now(),
        "markRetrieval": args.mark_retrieval,
        "goal": "为飞升模式导出项目级/全局级错题、记事本与缓存记忆上下文",
    }
    if args.scope in {"project", "both"}:
        if query_text:
            result["project"] = load_pruned_scope_context(
                args.host,
                "project",
                project_root,
                args.global_root,
                args.mark_retrieval,
                args.memory_threshold,
                args.stale_days,
                query_text,
                args.limit,
            )
        else:
            result["project"] = annotate_full_scope_context(
                load_scope_context(
                    args.host,
                    "project",
                    project_root,
                    args.global_root,
                    args.mark_retrieval,
                    args.memory_threshold,
                    args.stale_days,
                ),
                args.limit,
            )
    if args.scope in {"global", "both"}:
        if query_text:
            result["global"] = load_pruned_scope_context(
                args.host,
                "global",
                project_root,
                args.global_root,
                args.mark_retrieval,
                args.memory_threshold,
                args.stale_days,
                query_text,
                args.limit,
            )
        else:
            result["global"] = annotate_full_scope_context(
                load_scope_context(
                    args.host,
                    "global",
                    project_root,
                    args.global_root,
                    args.mark_retrieval,
                    args.memory_threshold,
                    args.stale_days,
                ),
                args.limit,
            )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def query_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    query_text = str(args.text or "").strip()
    if not query_text:
        raise SystemExit("query requires non-empty --text")
    if args.limit < 1:
        raise SystemExit("query requires --limit >= 1")

    combined_results: list[dict[str, Any]] = []
    for store_scope in ("project", "global"):
        if args.scope not in {store_scope, "both"}:
            continue
        combined_results.extend(
            query_store(
                args.host,
                store_scope,
                project_root,
                args.global_root,
                query_text,
                args.stale_days,
            )
        )

    combined_results.sort(key=lambda item: (item["score"], item["memoryScore"], item["archivedAt"]), reverse=True)
    result = {
        "host": args.host,
        "scope": args.scope,
        "query": query_text,
        "limit": args.limit,
        "generatedAt": utc_now(),
        "results": combined_results[: args.limit],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def scholar_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    query_text = str(args.text or "").strip()
    if not query_text:
        raise SystemExit("scholar requires non-empty --text")
    if args.limit < 1:
        raise SystemExit("scholar requires --limit >= 1")

    config = load_config()
    result: dict[str, Any] = {
        "host": args.host,
        "scope": args.scope,
        "query": query_text,
        "limit": args.limit,
        "phase": args.phase,
        "generatedAt": utc_now(),
        "enabled": config["scholar"],
        "shouldInject": False,
        "confidence": "none",
        "reason": "",
        "message": "",
        "matchedCaseIds": [],
        "results": [],
    }

    if not config["scholar"]:
        result["reason"] = "disabled"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.phase != "normal":
        result["reason"] = "phase_blocked"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    combined_results, entry_lookup = collect_scholar_results(
        args.host,
        args.scope,
        project_root,
        args.global_root,
        query_text,
        args.stale_days,
    )
    confidence = classify_scholar_confidence(combined_results)
    result["confidence"] = confidence
    result["results"] = combined_results[: args.limit]

    if not combined_results:
        result["reason"] = "no_match"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if confidence != "high":
        result["reason"] = "low_confidence"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    top_result = combined_results[0]
    top_entry = entry_lookup.get((top_result["storeScope"], top_result["caseId"]))
    if top_entry is None:
        result["reason"] = "missing_entry"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    result["shouldInject"] = True
    result["reason"] = "inject"
    result["message"] = build_scholar_message(top_entry)
    result["matchedCaseIds"] = [top_result["caseId"]]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def status_command(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    result: dict[str, Any] = {
        "host": args.host,
        "config": load_config(),
        "runtimeJournalExists": Path("~/.mistakebook/runtime-journal.md").expanduser().exists(),
    }
    for store_scope in ("project", "global"):
        if args.scope not in {store_scope, "both"}:
            continue
        base = resolve_project_base(args.host, project_root) if store_scope == "project" else resolve_global_base(args.host, args.global_root)
        store = ensure_store(base, store_scope)
        catalog = load_catalog(Path(store["catalog_path"]))
        result[store_scope] = {
            "base": str(base),
            "totalEntries": len(catalog),
            "mistakes": len([entry for entry in catalog if entry.get("entryType") == "mistake"]),
            "notes": len([entry for entry in catalog if entry.get("entryType") == "note"]),
            "memoryPath": store["memory_path"],
            "memoryStatePath": store["memory_state_path"],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def config_command(args: argparse.Namespace) -> int:
    if args.auto_detect is None and args.scholar is None:
        raise SystemExit("config requires at least one of --auto-detect or --scholar")

    config = load_config()
    if args.auto_detect is not None:
        config["auto_detect"] = args.auto_detect == "on"
    if args.scholar is not None:
        config["scholar"] = args.scholar == "on"
    config["updatedAt"] = utc_now()
    write_json(CONFIG_PATH, config)
    print(json.dumps(config, ensure_ascii=False, indent=2))
    return 0


def add_common_location_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", choices=sorted(PROJECT_ROOTS), default="generic")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--global-root")


def add_memory_policy_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--memory-threshold", type=int, default=DEFAULT_MEMORY_THRESHOLD)
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mistakebook archive and memory helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap", help="Create project/global stores.")
    add_common_location_args(bootstrap)
    bootstrap.add_argument("--scope", choices=("project", "global", "both"), default="both")
    bootstrap.set_defaults(func=bootstrap_command)

    archive = subparsers.add_parser("archive", help="Archive one mistake or notebook entry and refresh memories.")
    add_common_location_args(archive)
    add_memory_policy_args(archive)
    archive.add_argument("--entry-type", choices=ENTRY_TYPES)
    archive.add_argument("--payload-file")
    archive.add_argument("--payload")
    archive.add_argument("--payload-stdin", action="store_true")
    archive.set_defaults(func=archive_command)

    consolidate = subparsers.add_parser("consolidate", help="Rebuild cache memories from all mistakes and notes.")
    add_common_location_args(consolidate)
    add_memory_policy_args(consolidate)
    consolidate.add_argument("--scope", choices=("project", "global", "both"), default="both")
    consolidate.add_argument("--reason")
    consolidate.set_defaults(func=consolidate_command)

    touch = subparsers.add_parser("touch", help="Record retrieval/hit metrics for archived entries.")
    add_common_location_args(touch)
    add_memory_policy_args(touch)
    touch.add_argument("--scope", choices=("project", "global", "both"), default="both")
    touch.add_argument("--case-id", nargs="+", required=True)
    touch.add_argument("--kind", choices=("retrieval", "hit"), default="hit")
    touch.add_argument("--count", type=int, default=1)
    touch.add_argument("--when")
    touch.set_defaults(func=touch_command)

    context = subparsers.add_parser("context", help="Export full mistake/note/memory context for Ascended Mode.")
    add_common_location_args(context)
    add_memory_policy_args(context)
    context.add_argument("--scope", choices=("project", "global", "both"), default="both")
    context.add_argument("--mark-retrieval", action="store_true")
    context.add_argument("--query")
    context.add_argument("--limit", type=int, default=3)
    context.set_defaults(func=context_command)

    query = subparsers.add_parser("query", help="Search archived mistakes and notes with lexical match + memory score.")
    add_common_location_args(query)
    query.add_argument("--scope", choices=("project", "global", "both"), default="both")
    query.add_argument("--text", required=True)
    query.add_argument("--limit", type=int, default=3)
    query.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    query.set_defaults(func=query_command)

    scholar = subparsers.add_parser("scholar", help="Run lightweight preflight retrieval for scholar mode.")
    add_common_location_args(scholar)
    scholar.add_argument("--scope", choices=("project", "global", "both"), default="both")
    scholar.add_argument("--text", required=True)
    scholar.add_argument("--limit", type=int, default=3)
    scholar.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    scholar.add_argument("--phase", choices=SCHOLAR_PHASES, default="normal")
    scholar.set_defaults(func=scholar_command)

    status = subparsers.add_parser("status", help="Show config and store summary.")
    add_common_location_args(status)
    status.add_argument("--scope", choices=("project", "global", "both"), default="both")
    status.set_defaults(func=status_command)

    config = subparsers.add_parser("config", help="Update mistakebook config.")
    config.add_argument("--auto-detect", choices=("on", "off"))
    config.add_argument("--scholar", choices=("on", "off"))
    config.set_defaults(func=config_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
