---
name: notebook
description: "Codex skill entrypoint for Mistakebook note mode. Use this chip-style skill when you want to organize and archive a long-term note without expanding a prompt body into the composer."
---

# Notebook Entry

This is the Codex skill-chip wrapper for Mistakebook note mode.

Before acting, read these source files so this wrapper keeps the same behavior as the core Mistakebook note flow:

- `../../skills/mistakebook/SKILL.md`
- `../../skills/mistakebook/references/activation-patterns.md`
- `../../skills/mistakebook/references/storage-and-scope.md`
- `../../skills/mistakebook/references/archive-schema.md`

When this skill is invoked:

1. Treat the current task as a Mistakebook `note` flow
2. First organize the current long-term item
3. Explain why it is worth keeping
4. End with exactly:
   `如果这个事项值得长期注意，也可以告诉我“写入记事本”，我会把它归档到记事本并同步刷新记忆。`
5. Do not archive until the user explicitly confirms the note should be saved

This wrapper exists for Codex UX only. It should preserve the current notebook workflow while entering through a skill chip instead of a prompt body expansion.
