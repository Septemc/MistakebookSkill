#!/bin/bash
set -euo pipefail

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

TASK_TEXT="${MISTAKEBOOK_SUBAGENT_TASK:-${CLAUDE_USER_PROMPT:-${USER_PROMPT:-}}}"
if [ -z "$TASK_TEXT" ]; then
  exit 0
fi

HOST="${MISTAKEBOOK_HOST:-claude}"
PROJECT_ROOT="${MISTAKEBOOK_PROJECT_ROOT:-${CLAUDE_PROJECT_DIR:-$(pwd)}}"
SCOPE="${MISTAKEBOOK_SCOPE:-both}"

exec "$PYTHON_BIN" "$ROOT/scripts/lifecycle_hooks.py" subagent-start \
  --host "$HOST" \
  --project-root "$PROJECT_ROOT" \
  --scope "$SCOPE" \
  --task-text "$TASK_TEXT"
