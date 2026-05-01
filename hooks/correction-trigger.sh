#!/bin/bash
set -euo pipefail

CONFIG="${HOME:-~}/.mistakebook/config.json"

if [ -f "$CONFIG" ]; then
  AUTO_DETECT=$(python3 -c "import json; print(json.load(open('$CONFIG')).get('auto_detect', True))" 2>/dev/null || echo "True")
  if [ "$AUTO_DETECT" = "False" ]; then
    exit 0
  fi
fi

cat << 'EOF'
<EXTREMELY_IMPORTANT>
[Mistakebook Activated - User Correction Detected]

The user is correcting you or asking to preserve a lasting item. Mistakebook mode is now active.

You MUST do all of the following:
1. Immediately load the `mistakebook` skill if it is not already active.
2. On your next correction response, first display exactly:
<Mistakebook.Skill>I will now correct my mistake based on your feedback, continue correcting until completion, and archive it to my mistakebook.
3. After every correction turn, unless the user has explicitly confirmed completion, end with exactly:
Have I fully understood the issue and successfully corrected the mistake? If not, please teach me again. (If I have completed the correction, please let me know so I can archive it to my mistakebook.)
4. If the current reply contains a stable long-term takeaway, also end with exactly:
If this item is worth long-term attention, you can also tell me “write to notebook” and I will archive it to the notebook and refresh my memory.
5. Do not archive the case until the user explicitly confirms completion or asks to write it into the notebook.
6. When the user confirms completion, summarize the case, decide whether it is project/global/both, archive it as `mistake` or `note`, and refresh memory.
7. Maintain a rejection counter for correction cases. If the same case has already been rejected twice or more, immediately escalate into Ascended Mode before your next substantive fix.
8. In Ascended Mode, first display exactly:
I will now handle this problem using the most effective method I have seen. I will search all my knowledge bases. I am ready!
9. In Ascended Mode, comprehensively inspect project failures, project notes, project memory, global failures, global notes, global memory, current repo files/docs, and the current correction chain before choosing the strongest fix.

Treat repeated user corrections or notebook refinements as the same case until the user explicitly ends the loop.
</EXTREMELY_IMPORTANT>
EOF
