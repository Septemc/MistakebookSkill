#!/bin/bash
set -euo pipefail

CONFIG="${HOME:-~}/.mistakebook/config.json"

read_config_bool() {
  local key="$1"
  local default="$2"
  local python_bin=""

  if [ ! -f "$CONFIG" ]; then
    printf '%s\n' "$default"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  elif command -v python >/dev/null 2>&1; then
    python_bin="python"
  else
    printf '%s\n' "$default"
    return 0
  fi

  "$python_bin" - "$CONFIG" "$key" "$default" <<'PY'
import json
import sys

path, key, default = sys.argv[1], sys.argv[2], sys.argv[3]
default_bool = default.lower() == "true"

try:
    with open(path, "r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
except Exception:
    print("true" if default_bool else "false")
    raise SystemExit(0)

value = payload.get(key, default_bool)
if isinstance(value, bool):
    print("true" if value else "false")
else:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        print("true")
    elif text in {"0", "false", "no", "off"}:
        print("false")
    else:
        print("true" if default_bool else "false")
PY
}

SCHOLAR_ENABLED=$(read_config_bool "scholar" "true")
if [ "$SCHOLAR_ENABLED" != "true" ]; then
  exit 0
fi

cat <<'EOF'
<IMPORTANT>
[Mistakebook Scholar Preflight]

If the current user message is a fresh normal task, run scholar preflight once before your substantive answer:
`python scripts/mistakebook_cli.py scholar --host claude --project-root . --scope both --text "<current task>"`

Rules:
1. Only inject the returned reminder when `shouldInject = true`.
2. If `shouldInject = false`, stay silent and continue normally.
3. Do not run scholar during correction, notebook capture, or Ascended Mode.
4. Scholar prevents repeat mistakes; Ascended Mode still owns repeated-failure escalation.
</IMPORTANT>
EOF
