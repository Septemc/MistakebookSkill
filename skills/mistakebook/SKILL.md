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

## 生命周期 hook

宿主支持 hook 时，优先使用 `scripts/lifecycle_hooks.py` 统一处理运行态，而不是把状态恢复逻辑散落在长 prompt 里：

1. `UserPromptSubmit`
   - 使用 `scripts/trigger_report.py` 输出结构化 trigger report
   - correction、ascended、scholar preflight 都返回 `hookSpecificOutput.additionalContext`
   - 不再依赖不可测试的长 prompt 片段
2. `PreCompact`
   - 读取 `runtime-state.json`
   - 如果状态是 `armed`、`pending_review`、`followup_needed` 或 `summarizing`，写入 `~/.mistakebook/runtime-journal.md`
3. `PostCompact`
   - 读取最近的 `runtime-journal.md`
   - 如果宿主提供 compact summary，把摘要追加回 journal
   - 把 `case_id`、`status` 和“不要提前归档”的约束重新注入上下文
4. `SessionEnd`
   - 保存未完成闭环
   - 如果仍在 `summarizing`，提醒当前归档尚未确认，必须等待 `userConfirmed=true`
5. `SubagentStart`
   - 对子任务运行轻量 `scholar`
   - 只有 `evidencePacket.confidence = high` 且误注入风险可接受时才注入项目记忆
6. `SubagentStop`
   - 对实际使用过的 case 执行 `touch --kind hit`
   - 让 `hitCount`、`lastHitAt` 和缓存记忆能够反映子代理使用效果

## mistake 闭环

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
4. `userConfirmed`
5. `scopeDecision`
6. `scopeReasoning`
7. `rules`
8. `confirmedUnderstanding`

如果后续调用 CLI 时带 `--runtime-state-file`，并且 runtime state 里已有 `case_id`，payload 必须提供相同的 `caseId`。

编码完整性要求：

1. 归档前检查 payload 中不能出现连续四个以上问号、`U+FFFD` replacement character 或私用区字符。
2. 在 Windows / PowerShell / Codex `shell_command` 中，不要把中文 payload 直接写进命令文本；传输层一旦把中文改成连续问号，后续无法还原。
3. 如需通过命令传 payload，优先使用 UTF-8 `--payload-file`；必须走 stdin 时，使用 ASCII `\u` 转义 JSON。
4. 如果 CLI 报 `payload contains likely encoding corruption`，停止归档，重新生成未损坏的 payload，不要手工把问号写进 memory。

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

## 行为评测

改动触发词、归档契约、检索、compact 恢复或宿主入口后，优先运行统一评测：

```bash
python scripts/eval_harness.py --root .
```

评测必须覆盖：

1. `trigger_recall`
2. `trigger_precision`
3. `archive_contract`
4. `retrieval_quality`
5. `compact_recovery`
6. `cross_host`

## 宿主与路径

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

在新的普通任务开始前，如果当前不在 `mistake` 纠错闭环、`note` 流程或 `ascended` 模式里，先运行轻量预检：

```bash
python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<current task>"
```

执行规则：

1. 只有当 `scholar` 返回 `shouldInject = true` 时，才在正式回答前输出一行历史提醒。
2. 如果返回 `shouldInject = false`，必须保持静默，不要把 query 结果原样展示给用户。
3. 判断是否注入时，优先看 `evidencePacket.confidence`、`evidencePacket.whyMatched` 和 `evidencePacket.riskOfFalsePositive`。
4. 一旦进入纠错闭环或 Ascended Mode，就停止运行 `scholar`。
5. `scholar` 的职责是“回答前避错”，`ascended` 的职责是“失败后升级处置”，两者不能混成同一个重模式。
6. 如果用户说 `scholar off` 或 `scholar on`，可以在当前会话中临时关闭或恢复预检；如果用户要求长期关闭或开启，再执行：

```bash
python scripts/mistakebook_cli.py config --scholar off
python scripts/mistakebook_cli.py config --scholar on
```
