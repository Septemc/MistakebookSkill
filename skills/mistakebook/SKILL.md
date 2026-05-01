---
name: mistakebook
description: "Detects when the user is correcting, reworking, pointing out mistakes, or requesting long-term notes to be preserved; launches a human-confirmation loop. Supports both `mistake` and `note` entry types, writing to project-level and/or global-level mistakebook / notebook, and synchronously refreshes cached project memory and global memory. If the same case is rejected twice or more by the user, or the user says 'use the most effective method you have seen to handle this' or inputs '/ascended', automatically escalates to Ascended Mode — comprehensively retrieving project/global mistakes, notes, memory cache, and current knowledge base before proceeding. Common triggers: 'you are wrong', 'this is not right', 'redo this', 'let me correct you', 'still not fixed', 'write to notebook', 'note this item', '/mistakebook', '/ascended'."
---

# Mistakebook / Notebook Skill

This Skill handles not only "correction archiving" but also "active item preservation."

Four unified goals:

1. Turn user corrections into a closed loop
2. Preserve long-term attention items into the notebook
3. Maintain project memory and global memory as caches, not append-only logs
4. When ordinary fixes are insufficient, escalate to Ascended Mode for full retrieval and strongest-possible handling

## After Loading

After loading this Skill, immediately read these files:

1. `references/activation-patterns.md`
2. `references/storage-and-scope.md`
3. `references/archive-schema.md`
4. `references/ascended-mode.md`

Do not wait for "on-demand discovery" — these four files collectively define triggering, escalation, archiving, caching, and deferral strategy.

## Mandatory Display Text

### When Entering Correction Mode

When you first determine that the user is correcting you, you must output this exact text:

`<Mistakebook.Skill>I will now correct my mistake based on your feedback, continue correcting until completion, and archive it to my mistakebook.`

### After Each Correction Turn

As long as the current `mistake` case has not been explicitly confirmed complete by the user, you must append this exact text at the end of every reply:

`Have I fully understood the issue and successfully corrected the mistake? If not, please teach me again. (If I have completed the correction, please let me know so I can archive it to my mistakebook.)`

### Notebook Follow-up

Whenever your reply contains a stable long-term takeaway worth preserving, append this exact text at the end:

`If this item is worth long-term attention, you can also tell me "write to notebook" and I will archive it to the notebook and refresh my memory.`

### Ascended Mode Mandatory Text

When entering Ascended Mode, you must first output this exact text:

`I will now handle this problem using the most effective method I have seen. I will search all my knowledge bases. I am ready!`

## Entry Types

From now on, maintain only two types of archived entries:

1. `mistake`
   - Error cases that have been fully corrected and are worth reviewing
2. `note`
   - Not necessarily errors, but items worth long-term attention and active recording

## State Machine

Model the current flow as these states:

1. `disabled`
   - Not currently in any loop
2. `armed`
   - Correction or note need detected
3. `pending_review`
   - Current fix or note summary given, awaiting user confirmation
4. `followup_needed`
   - User requests continued correction or additional note content
5. `summarizing`
   - User has explicitly confirmed, begin payload assembly
6. `archived`
   - Written to detailed entry and cached memory

Additionally, maintain:

1. `entry_type`
   - `mistake` or `note`
2. `mode`
   - `normal` or `ascended`

## When to Enter `mistake`

Enter `mistake` when any condition is met:

1. User explicitly says you are wrong, haven't fixed it, or made the same error again
2. User begins correcting your statements, code, solutions, or behavior item by item
3. User gives instructions like "fix it my way", "let me teach you", "redo it"
4. User mentions "mistakebook", "correction mode", "archive this mistake"

## When to Enter `note`

Enter `note` archive candidate flow when any condition is met:

1. User explicitly says "write to notebook"
2. User says "note this item"
3. User explicitly states "this is not a mistake, but needs long-term attention"
4. You have formed a stable, executable, long-term-worth-preserving attention item

## Runtime State

Maintain at least this information until archiving is complete:

1. `entry_type`
2. `case_id`
3. `host`
4. `project_root`
5. `original_prompt`
6. `original_reply`
7. `correction_feedback_chain`
8. `latest_fixed_reply`
9. `scope_guess`
10. `status`
11. `rejection_count`
12. `correction_attempt_count`
13. `ascended_mode`
14. `ascended_trigger_reason`
15. `knowledge_sources_reviewed`
16. `note_candidates`

If context compaction occurs, prioritize checkpointing this information to `~/.mistakebook/runtime-journal.md`.

## `mistake` Loop

### 1. Entry

Once confirmed as a correction scenario:

1. Output the activation message
2. Provide the corrected answer
3. Append the fixed correction follow-up at the end
4. If this round also surfaces a long-term item, additionally append the notebook follow-up

### 2. User Says "Still Not Fixed"

You must:

1. Merge this user feedback into the same case
2. Continue correcting based on feedback, do not archive prematurely
3. Continue appending the fixed correction follow-up at the end of this round
4. `rejection_count += 1`
5. `correction_attempt_count += 1`

### 3. Automatic Escalation to Ascended Mode

If the same `mistake` case has been explicitly rejected by the user twice or more, do not continue with ordinary fix mode — automatically escalate to Ascended Mode.

Automatic escalation conditions:

1. `rejection_count >= 2`
2. The same case has clearly entered "still wrong after multiple fixes" state

Once automatically escalated:

1. First output the Ascended Mode mandatory text
2. Then comprehensively retrieve project-level and global-level knowledge sources
3. First analyze why consecutive corrections still failed
4. Then provide a new correction

## `note` Loop

### 1. Entry

Once confirmed as an active item to record:

1. First provide the current item summary
2. Clearly explain why this item is worth long-term preservation
3. Append the notebook follow-up at the end

### 2. When Unconfirmed

If the user continues adding content:

1. Merge additions into the same `note` case
2. Update items, action items, or boundary descriptions
3. Do not archive prematurely

### 3. Completion Signal

Only archive the current item as `note` after explicit user confirmation.

Expressions considered explicit confirmation:

1. `write to notebook`
2. `note it down`
3. `preserve this long-term`
4. `save this item`
5. `remember this going forward`

## Manual Entry to Ascended Mode

Any of the following must immediately enter Ascended Mode:

1. User says: `use the most effective method you have seen to handle this`
2. User inputs: `/ascended`

Manual trigger takes priority over automatic judgment. Enter Ascended Mode immediately upon receipt — no need to wait for the next round.

## Knowledge Sources for Ascended Mode

After entering Ascended Mode, you must thoroughly retrieve and use these sources:

1. Current project-level mistake archive `failures/`
2. Current project-level notebook `notes/`
3. Current project-level memory `memory/PROJECT_MEMORY.md`
4. Current project-level cache state `state/memory_state.json`
5. Current global-level mistake archive `failures/`
6. Current global-level notebook `notes/`
7. Current global-level memory `memory/GLOBAL_MEMORY.md`
8. Current global-level cache state `state/memory_state.json`
9. Real files, real outputs, real docs in the current repo relevant to the problem
10. This Skill's rule files and reference documents
11. All user correction chains and item chains accumulated in the current session

Do not just say "I will do deep analysis" without performing real retrieval.

## Ascended Mode Output Discipline

After entering Ascended Mode, before providing a new correction, you must at least:

1. Clearly state why the previous rounds still failed
2. Clearly describe which mistakes, notes, memory, or real files you consulted
3. Clearly select the single most effective handling approach available
4. Prioritize real files and real outputs over impression-based patching

## Archive Flow

### 1. Generate Structured Payload

Use the schema in `references/archive-schema.md` to generate the payload.

Must include at minimum:

1. `entryType`
2. `title`
3. `summary`
4. `scopeDecision`
5. `scopeReasoning`
6. `rules`
7. `confirmedUnderstanding`

For `mistake`, additionally include:

1. `originalPrompt`
2. `correctionFeedback`
3. `finalReply`

For `note`, additionally include:

1. `noteReason`
2. `noteContent`
3. `noteActionItems`
4. `noteContext`

### 2. Prefer Script-Based Archiving

If `scripts/mistakebook_cli.py` exists in the repo, prefer using it:

```bash
python scripts/mistakebook_cli.py bootstrap --host codex --project-root .
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-file <temp-json>
```

### 3. Record Cache Hits

If a mistake, note, or memory entry is later retrieved or proves effective again, record the hit:

```bash
python scripts/mistakebook_cli.py touch --host codex --project-root . --scope both --case-id <case-id> --kind hit
```

### 4. Rewrite Cache Memory

If entries are growing or the cache needs deferral cleanup, run:

```bash
python scripts/mistakebook_cli.py consolidate --host codex --project-root . --scope both
```

### 5. Export Ascended Mode Context

If entering Ascended Mode, prefer running:

```bash
python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval
```

## Memory Is Not an Append-Only Log

Project memory and global memory are cache layers, not full archives.

They must be:

1. Concise
2. Condensed
3. Accurate
4. Executable
5. Deferrable

## Cache and Deferral

Default policy:

1. When entries are few, nearly all can be retained
2. After reaching threshold, filter by `hitCount`, `retrievalCount`, recent activity time, and priority
3. Long-inactive, low-hit entries temporarily exit the cache
4. Detailed entries are always preserved in `failures/` and `notes/`

## Host and Paths

Default directories:

1. Project-level
   - `failures/`
   - `notes/`
   - `memory/`
   - `state/`
2. Global-level
   - `failures/`
   - `notes/`
   - `memory/`
   - `state/`

If the host can only write to a skill/plugin directory, redirect the global root to a `.data` or `.mistakebook` subdirectory within the host directory.

## Common Pitfalls

1. Do not mistake "user is discussing a bug" for "user is correcting you"
2. Do not archive before the user has confirmed
3. Do not only record "what went wrong" — also record "what was fully understood"
4. Do not let memory become an append-only log; retain only high-density, executable content
5. Do not confuse "temporary deferral" with "deleting detailed entries"
6. Do not enter Ascended Mode and only check the cache without reviewing detailed mistakes and notes

## Scholar Preflight

Before a new normal task begins, if the current session is not in `mistake` correction loop, `note` flow, or `ascended` mode, run a lightweight preflight check:

```bash
python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<current task>"
```

Execution rules:

1. Only output a history reminder before the substantive answer when `scholar` returns `shouldInject = true`
2. If `shouldInject = false`, stay silent and do not show query results to the user
3. Stop running `scholar` once entering correction loop or Ascended Mode
4. `scholar` is responsible for "pre-answer mistake prevention"; `ascended` is responsible for "post-failure escalation" — do not conflate the two into a single heavy mode
5. If the user says `scholar off` or `scholar on`, you can temporarily disable or re-enable preflight in the current session; for long-term changes, run:

```bash
python scripts/mistakebook_cli.py config --scholar off
python scripts/mistakebook_cli.py config --scholar on
```
