#!/bin/bash
set -euo pipefail

cat << 'EOF'
<EXTREMELY_IMPORTANT>
[Mistakebook Ascended Mode Activated]

The user explicitly requested the highest-level correction workflow.

You MUST do all of the following immediately:
1. Load the `mistakebook` skill if it is not already active.
2. First display exactly:
我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！
3. Treat the current issue as an Ascended Mode correction case.
4. Before proposing the next fix, comprehensively review:
   - project-level failures
   - project-level memory
   - global-level failures
   - global-level memory
   - current repo files, docs, and real outputs relevant to the problem
   - the entire user correction chain so far
5. Explain why previous correction attempts still failed.
6. Choose the single strongest currently-known solution and use that to re-handle the problem.
7. If the user still has not confirmed completion, remain inside the mistakebook correction loop and keep using the fixed follow-up question.
</EXTREMELY_IMPORTANT>
EOF
