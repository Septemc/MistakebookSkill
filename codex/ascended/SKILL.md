---
name: ascended
description: "Codex skill entrypoint for Mistakebook Ascended Mode. Use this chip-style skill when you want the strongest retrieval workflow without expanding a long prompt into the composer."
---

# Ascended Entry

This is the Codex skill-chip wrapper for Mistakebook Ascended Mode.

Before acting, read these source files so this wrapper keeps the same behavior as the core Mistakebook protocol:

- `../../skills/mistakebook/SKILL.md`
- `../../skills/mistakebook/references/activation-patterns.md`
- `../../skills/mistakebook/references/storage-and-scope.md`
- `../../skills/mistakebook/references/archive-schema.md`
- `../../skills/mistakebook/references/ascended-mode.md`

When this skill is invoked:

1. Treat the current task as a Mistakebook Ascended Mode case
2. First output exactly:
   `我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！`
3. Then follow the existing Mistakebook Ascended Mode workflow
4. If `scripts/mistakebook_cli.py` exists, prefer:
   `python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval`
5. Before giving the new answer, explain why previous handling failed and which knowledge sources you reviewed

This wrapper exists for Codex UX only. It should behave like the existing Ascended Mode protocol, but enter through a skill chip instead of a prompt body expansion.
