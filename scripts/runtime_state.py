#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUSES = {
    "disabled",
    "armed",
    "pending_review",
    "followup_needed",
    "summarizing",
    "archived",
}

ENTRY_TYPES = {"", "mistake", "note"}
MODES = {"normal", "ascended"}

ALLOWED_TRANSITIONS = {
    "disabled": {"armed", "disabled"},
    "armed": {"pending_review", "followup_needed", "summarizing", "disabled"},
    "pending_review": {"followup_needed", "summarizing", "disabled"},
    "followup_needed": {"pending_review", "summarizing", "disabled"},
    "summarizing": {"archived", "followup_needed", "disabled"},
    "archived": {"disabled", "armed"},
}


class RuntimeStateError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def normalize_entry_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"mistake", "note"}:
        return text
    if text in {"notebook", "memo"}:
        return "note"
    if not text:
        return ""
    raise RuntimeStateError(f"unknown runtime entry_type: {text}")


def default_runtime_state(
    *,
    host: str = "generic",
    project_root: str = "",
    entry_type: str = "",
    case_id: str = "",
    status: str = "disabled",
    mode: str = "normal",
) -> dict[str, Any]:
    return normalize_state(
        {
            "status": status,
            "entry_type": entry_type,
            "mode": mode,
            "host": host,
            "project_root": project_root,
            "case_id": case_id,
            "rejection_count": 0,
            "correction_attempt_count": 0,
            "ascended_trigger_reason": "",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
    )


def normalize_state(payload: dict[str, Any] | None) -> dict[str, Any]:
    state = dict(payload or {})
    status = str(state.get("status") or "disabled").strip()
    if status not in STATUSES:
        raise RuntimeStateError(f"unknown runtime status: {status}")

    mode = str(state.get("mode") or "normal").strip()
    if mode not in MODES:
        raise RuntimeStateError(f"unknown runtime mode: {mode}")

    state["status"] = status
    state["entry_type"] = normalize_entry_type(state.get("entry_type") or state.get("entryType"))
    state["mode"] = mode
    state["host"] = str(state.get("host") or "generic").strip()
    state["project_root"] = str(state.get("project_root") or state.get("projectRoot") or "").strip()
    state["case_id"] = str(state.get("case_id") or state.get("caseId") or "").strip()
    state["rejection_count"] = int(state.get("rejection_count") or state.get("rejectionCount") or 0)
    state["correction_attempt_count"] = int(
        state.get("correction_attempt_count") or state.get("correctionAttemptCount") or 0
    )
    state["ascended_trigger_reason"] = str(
        state.get("ascended_trigger_reason") or state.get("ascendedTriggerReason") or ""
    ).strip()
    state["created_at"] = str(state.get("created_at") or state.get("createdAt") or utc_now()).strip()
    state["updated_at"] = str(state.get("updated_at") or state.get("updatedAt") or utc_now()).strip()
    return state


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_runtime_state()
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeStateError("runtime state must be a JSON object")
    return normalize_state(payload)


def save_state(path: Path, state: dict[str, Any]) -> None:
    normalized = normalize_state(state)
    normalized["updated_at"] = utc_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def transition(state: dict[str, Any], next_status: str, **updates: Any) -> dict[str, Any]:
    current = normalize_state(state)
    if next_status not in STATUSES:
        raise RuntimeStateError(f"unknown runtime status: {next_status}")
    allowed = ALLOWED_TRANSITIONS[current["status"]]
    if next_status not in allowed:
        raise RuntimeStateError(f"invalid runtime state transition: {current['status']} -> {next_status}")
    transitioned = dict(current)
    transitioned.update(updates)
    transitioned["status"] = next_status
    transitioned["updated_at"] = utc_now()
    return normalize_state(transitioned)


def payload_entry_type(payload: dict[str, Any]) -> str:
    value = payload.get("entryType", payload.get("entry_type", ""))
    return normalize_entry_type(value)


def payload_case_id(payload: dict[str, Any]) -> str:
    return str(payload.get("caseId") or payload.get("case_id") or "").strip()


def assert_can_archive(state: dict[str, Any], payload: dict[str, Any]) -> None:
    normalized_state = normalize_state(state)
    if normalized_state["status"] != "summarizing":
        raise RuntimeStateError("archive requires status=summarizing")
    if not ensure_bool(payload.get("userConfirmed")):
        raise RuntimeStateError("archive payload must set userConfirmed=true")

    state_entry_type = normalized_state["entry_type"]
    archive_entry_type = payload_entry_type(payload)
    if state_entry_type and archive_entry_type and state_entry_type != archive_entry_type:
        raise RuntimeStateError(f"archive entry_type mismatch: state={state_entry_type} payload={archive_entry_type}")

    state_case_id = normalized_state["case_id"]
    archive_case_id = payload_case_id(payload)
    if state_case_id and not archive_case_id:
        raise RuntimeStateError(f"archive payload missing caseId for active runtime case: {state_case_id}")
    if state_case_id and archive_case_id != state_case_id:
        raise RuntimeStateError(f"archive case_id mismatch: state={state_case_id} payload={archive_case_id}")
