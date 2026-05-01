#!/bin/bash
set -euo pipefail

cat << 'EOF'
<EXTREMELY_IMPORTANT>
[Mistakebook Ascended Mode Activated]

The user explicitly requested the highest-level correction workflow.

You MUST do all of the following immediately:
1. Load the `mistakebook` skill if it is not already active.
2. First display exactly:
I will now handle this problem using the most effective method I have seen. I will search all my knowledge bases. I am ready!
3. Treat the current issue as an Ascended Mode correction case.
4. Before proposing the next fix, comprehensively review:
   - project-level failures
   - project-level notes
   - project-level memory
   - project-level memory cache state
   - global-level failures
   - global-level notes
   - global-level memory
   - global-level memory cache state
   - current repo files, docs, and real outputs relevant to the problem
   - the entire user correction chain so far
5. If `scripts/mistakebook_cli.py` exists, prefer collecting the full context via:
   - `python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval`
6. Explain why previous correction attempts still failed.
7. Choose the single strongest currently-known solution and use that to re-handle the problem.
8. If the user still has not confirmed completion, remain inside the mistakebook loop and keep using the fixed follow-up question plus the notebook follow-up when relevant.
</EXTREMELY_IMPORTANT>
EOF
