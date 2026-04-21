#!/bin/bash
set -euo pipefail

JOURNAL="${HOME:-~}/.mistakebook/runtime-journal.md"

if [ ! -f "$JOURNAL" ]; then
  exit 0
fi

if [ "$(uname)" = "Darwin" ]; then
  AGE=$(( $(date +%s) - $(stat -f %m "$JOURNAL") ))
else
  AGE=$(( $(date +%s) - $(stat -c %Y "$JOURNAL") ))
fi

if [ "$AGE" -gt 86400 ]; then
  exit 0
fi

escape_for_json() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

read -r -d '' RESTORE_MSG << 'EOF' || true
[Mistakebook Session Restore]
A recent mistakebook checkpoint exists at ~/.mistakebook/runtime-journal.md.

If the user is still discussing the same issue or the same long-term note, immediately read that file and resume the same state instead of creating a brand-new case.

Restore at least:
1. current status
2. project_root
3. case_id
4. original prompt / original reply summary
5. accumulated correction or note feedback
6. latest fixed reply summary
7. scope guess
8. rejection_count / correction_attempt_count
9. whether Ascended Mode was active
10. which knowledge sources had already been reviewed

Important:
- Do not archive until the user explicitly confirms completion or asks to write the item into the notebook.
- If the activation sentence was already shown in the same case, do not repeat it unless you are clearly re-entering correction mode after a long interruption.
- If correction mode is active, keep ending correction turns with the exact fixed follow-up question.
- If a stable long-term item was already being discussed, keep using the exact notebook follow-up sentence when relevant.
- If Ascended Mode was already active for the same case, do not silently downgrade back to shallow correction.
EOF

ESCAPED=$(escape_for_json "$RESTORE_MSG")
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$ESCAPED"
