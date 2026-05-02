#!/bin/bash
set -euo pipefail

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

STATE_ARGS=()
if [ -n "${MISTAKEBOOK_RUNTIME_STATE_FILE:-}" ]; then
  STATE_ARGS=(--state-file "$MISTAKEBOOK_RUNTIME_STATE_FILE")
fi

JOURNAL_ARGS=()
if [ -n "${MISTAKEBOOK_RUNTIME_JOURNAL_FILE:-}" ]; then
  JOURNAL_ARGS=(--journal-file "$MISTAKEBOOK_RUNTIME_JOURNAL_FILE")
fi

exec "$PYTHON_BIN" "$ROOT/scripts/lifecycle_hooks.py" session-end "${STATE_ARGS[@]}" "${JOURNAL_ARGS[@]}"
