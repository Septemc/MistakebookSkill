# Storage And Scope

## Unified Directory Layout

All agent tools (Codex, Claude Code, VSCode, generic) share the same storage paths.

### Project-level

`<project>/.mistakebook/`

```
.mistakebook/
├─ failures/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ notes/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ memory/
│  └─ PROJECT_MEMORY.md
└─ state/
   ├─ catalog.json
   └─ memory_state.json
```

### Global-level

`~/.mistakebook/`

```
.mistakebook/
├─ failures/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ notes/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ memory/
│  └─ GLOBAL_MEMORY.md
└─ state/
   ├─ catalog.json
   └─ memory_state.json
```

### Runtime state

- Config: `~/.mistakebook/config.json`
- Session checkpoint: `~/.mistakebook/runtime-journal.md`

## Migration from Legacy Paths

Older versions stored data in per-agent directories:

- `<project>/.codex/mistakebook/`
- `<project>/.claude/mistakebook/`
- `<project>/.vscode/mistakebook/`
- `~/.codex/mistakebook/`
- `~/.claude/mistakebook/`
- `~/.vscode/mistakebook/`

Running `bootstrap`, `consolidate`, or `migrate` automatically detects and migrates these legacy directories into the unified `.mistakebook/` path, then deletes the old directories.

```bash
python scripts/mistakebook_cli.py migrate --host codex --project-root .
```

## Minimum Files Per Store

1. `failures/INDEX.md`
2. `notes/INDEX.md`
3. `memory/PROJECT_MEMORY.md` or `memory/GLOBAL_MEMORY.md`
4. `state/catalog.json`
5. `state/memory_state.json`

## scopeDecision Rules

### `project`

Applies to:

1. Project directory structure
2. Project-specific naming
3. Project business rules
4. Project build/test/deploy workflows
5. Repo-specific constraints

### `global`

Applies to:

1. General verification gaps
2. General fact-checking gaps
3. General communication misreads
4. General reasoning deviations
5. General engineering bad habits

### `both`

Use when both conditions hold:

1. The entry has detailed review or long-term attention value within the current project
2. It also extracts a stable, generalizable, cross-project reusable rule

## Entry Types

### `mistake`

Applies to:

1. Errors that have occurred
2. Failure cases that have been fully corrected
3. Content requiring "why was this wrong" review

### `note`

Applies to:

1. Not errors, but worth long-term preservation
2. Operational constraints that repeatedly affect future work
3. Proactively recorded reminders, boundaries, collaboration habits

## Memory Writing

### Project Memory

Project memory should retain:

1. Current project stable constraints
2. Current project active notes
3. Current project high-risk pitfalls
4. Validated best practices

### Global Memory

Global memory should retain:

1. Cross-project general rules
2. General verification discipline
3. General communication discipline
4. General active notes

## Memory Is a Cache, Not a Full Index

Project and global memory should be treated as cache layers:

1. When entries are few, nearly all can be retained
2. After reaching threshold, stop mechanical accumulation
3. Begin filtering by hit/retrieval/freshness/priority
4. Detailed entries always stay in `failures/` and `notes/`
5. Cache layer only retains high-value, concise summaries

## Hit and Deferral

Maintain two metrics:

1. `retrievalCount`
   - How many times read by ascended mode or context collection
2. `hitCount`
   - How many times proven "still worth keeping in cache"

Strategy:

1. High hit + recently active
   - Prioritize keeping in cache
2. Low hit + long unretrieved
   - Move to `deferredEntries`
3. Temporary deferral only
   - Do not delete detailed entries, only temporarily remove from memory cache

## Every Archive Updates Memory

Recommended practice:

1. Write current entry as detailed Markdown
2. Synchronously update `state/catalog.json`
3. Auto-refresh `memory/*.md`
4. If entry volume and noise increase, run `consolidate`

## full rollup / Consolidate Triggers

In addition to normal refresh, do a focused cleanup when:

1. Same topic has 3+ entries
2. A store has 5+ new entries since last cleanup
3. More than 14 days since last focused cleanup
4. Memory content clearly exceeds threshold

`consolidate` goals are not to increase word count, but to:

1. Merge duplicates
2. Remove stale entries
3. Increase visibility of high-hit entries
4. Temporarily remove long low-hit entries from cache
5. Keep memory files short, accurate, and executable
