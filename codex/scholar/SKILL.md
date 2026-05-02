---
name: scholar
description: "Codex skill entrypoint for Mistakebook scholar preflight. Use this chip-style skill on a fresh normal task when you want lightweight retrieval without expanding a long prompt into the composer."
---

# Scholar Entry

This is the Codex skill-chip wrapper for Mistakebook scholar preflight.

Before acting, read these source files so this wrapper keeps the same lightweight preflight behavior as the existing implementation:

- `../../skills/mistakebook/SKILL.md`
- `../../commands/scholar.md`

When this skill is invoked:

1. Use it only for a fresh normal task
2. Do not use it if the current conversation is already in:
   - mistake correction mode
   - note archiving mode
   - Ascended Mode
3. If `scripts/mistakebook_cli.py` exists, prefer:
   `python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<当前任务>"`
4. Only inject a history reminder if `shouldInject = true`
5. Use `evidencePacket.confidence`, `evidencePacket.whyMatched`, and `evidencePacket.riskOfFalsePositive` to understand why it matched
6. If `shouldInject = false`, stay silent and continue normally

This wrapper exists for Codex UX only. It keeps scholar preflight lightweight while entering through a skill chip instead of a prompt body expansion.
