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

The user is correcting you. Mistakebook correction mode is now active.

You MUST do all of the following:
1. Immediately load the `mistakebook` skill if it is not already active.
2. On your next correction response, first display exactly:
<错题集.Skill>我接下来会进行纠错，并根据你的纠错信息，持续纠错直到完成，然后写入我的错题集。
3. After every correction turn, unless the user has explicitly confirmed completion, end with exactly:
我有没有吃透当前问题，是否成功纠正错误，如果没有的话，请你再教我一遍。（如果我已经完成了纠错，也请你告诉我一声，我可以把错题写入我的错题集）
4. Do not archive the case until the user explicitly says the correction is complete.
5. When the user confirms completion, summarize the case, decide whether it is project/global/both, archive it, and refresh memory.
6. Maintain a rejection counter for this case. If the same case has already been rejected twice or more, immediately escalate into Ascended Mode before your next substantive fix.
7. In Ascended Mode, first display exactly:
我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！
8. In Ascended Mode, comprehensively inspect project failures, project memory, global failures, global memory, current repo files/docs, and the current correction chain before choosing the strongest fix.

Treat repeated user corrections as the same case until the user explicitly ends the correction loop.
</EXTREMELY_IMPORTANT>
EOF
