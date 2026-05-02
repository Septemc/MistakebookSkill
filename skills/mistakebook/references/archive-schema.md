# Archive Schema

## 统一条目模型

从现在开始，归档条目不再只有“错题”一种，而是统一支持两类：

1. `mistake`
   - 已经完成纠错、值得复盘的错误案例
2. `note`
   - 不一定是错误，但值得长期注意、主动记录的事项

两类条目都进入同一个 store：

1. 详细条目分别落到 `failures/` 或 `notes/`
2. 同时进入 `state/catalog.json`
3. 每次写入后都要刷新 `memory/`
4. 必要时再执行一次 `consolidate`

## 推荐 payload

```json
{
  "schemaVersion": "2.0.0",
  "entryType": "mistake",
  "host": "codex",
  "agentId": "codex",
  "sessionId": "optional",
  "traceId": "optional",
  "caseId": "optional",
  "archivedAt": "2026-04-21T08:00:00Z",
  "title": "没有先读真实文件就修改协议",
  "summary": "修改协议前没有先读真实实现，导致多宿主规则开始漂移。",
  "userConfirmed": true,
  "severity": "medium",
  "scopeDecision": "both",
  "scopeReasoning": [
    "问题发生在当前仓库协议和脚本之间，项目内需要复盘",
    "先读真实实现再改协议也是稳定的通用规则"
  ],
  "keywords": ["read-first", "protocol-sync"],
  "rules": [
    "修改系统协议前，先阅读真实实现与真实入口"
  ],
  "confirmedUnderstanding": [
    "我已经理解：协议更新必须先和真实脚本对齐"
  ],
  "whatWentWrong": [
    "先改文案，后看实现，导致行为口径不一致"
  ],
  "preventionChecklist": [
    "先读核心脚本",
    "先读核心 Skill",
    "再同步宿主镜像"
  ],
  "projectMemoryDelta": [
    "协议更新前先核对核心脚本与多宿主镜像"
  ],
  "globalMemoryDelta": [
    "在修改系统协议前先核对真实实现与入口"
  ],
  "knowledgeSourcesReviewed": [
    "project_failures",
    "project_notes",
    "project_memory",
    "global_failures",
    "global_notes",
    "global_memory",
    "current_repo_files"
  ],
  "correctionAttemptCount": 3,
  "ascendedTriggered": true,
  "ascendedTriggerReason": "手动要求按最有效方式处理",
  "memoryPriority": 0.0,
  "retrievalCount": 2,
  "lastRetrievedAt": "2026-04-21T08:10:00Z",
  "hitCount": 1,
  "lastHitAt": "2026-04-21T08:12:00Z",
  "originalPrompt": "用户原始问题",
  "originalReply": "你的原始回答",
  "correctionFeedback": "用户的纠错说明",
  "followupCorrections": [
    "用户的后续纠错 1",
    "用户的后续纠错 2"
  ],
  "finalReply": "你的最终正确回答"
}
```

## note 条目额外字段

当 `entryType = "note"` 时，推荐额外补这些字段：

```json
{
  "entryType": "note",
  "title": "新增记事本时记得同步缓存记忆",
  "summary": "记事本不是错题，但同样要回写项目记忆和全局记忆。",
  "userConfirmed": true,
  "noteReason": "这是长期有效的实现约束，不应该只停留在聊天里。",
  "noteContent": [
    "记事本记录主动注意事项，不要求它一定是错题"
  ],
  "noteActionItems": [
    "归档 note 后刷新 project/global memory",
    "consolidate 时一起参与遗忘整理"
  ],
  "noteContext": "用户要求增加记事本功能，并要求和错题集共用缓存记忆机制。"
}
```

## 最低要求

### mistake

至少包含：

1. `entryType`
2. `title`
3. `summary`
4. `userConfirmed`
5. `scopeDecision`
6. `scopeReasoning`
7. `rules`
8. `confirmedUnderstanding`
9. `originalPrompt`
10. `correctionFeedback`
11. `finalReply`

如果 archive 命令传入 `--runtime-state-file`，并且 runtime state 里已有 `case_id`，payload 必须提供相同的 `caseId`，否则不得归档。

### note

至少包含：

1. `entryType`
2. `title`
3. `summary`
4. `userConfirmed`
5. `scopeDecision`
6. `scopeReasoning`
7. `rules`
8. `confirmedUnderstanding`
9. `noteReason`
10. `noteContent`

## 单条 Markdown 结构

### mistake

```markdown
# 标题

- entry_type: mistake
- archived_at: ...
- host: ...
- scope: ...

## 错误总结
...

## 这次到底错在哪里
- ...

## 以后必须遵守
- ...

## 已经纠正并吃透的点
- ...

## 下次开始前自检
- ...

## 飞升模式记录
- ...

## 飞升模式检索来源
- ...

## 原始问题
...

## 用户纠错反馈
...

## 最终正确回答
...
```

### note

```markdown
# 标题

- entry_type: note
- archived_at: ...
- host: ...
- scope: ...

## 事项总结
...

## 为什么值得记录
...

## 需要注意
- ...

## 建议行动
- ...

## 来源上下文
...

## 已经确认的稳定规则
- ...

## 已经吃透的点
- ...
```

## catalog.json 建议保留的字段

为了支撑缓存式记忆和遗忘整理，`state/catalog.json` 至少要保留：

1. `caseId`
2. `entryType`
3. `title`
4. `relativePath`
5. `archivedAt`
6. `scopeDecision`
7. `userConfirmed`
8. `summary`
9. `rules`
10. `confirmedUnderstanding`
11. `projectMemoryDelta`
12. `globalMemoryDelta`
13. `noteContent`
14. `noteActionItems`
15. `retrievalCount`
16. `lastRetrievedAt`
17. `hitCount`
18. `lastHitAt`
19. `memoryPriority`

## 记忆缓存状态

为了让“记忆不是无限增长的长文，而是会整理、会遗忘的缓存”，每个 store 还应该维护：

1. `state/memory_state.json`

推荐包含：

1. `updatedAt`
2. `memoryThreshold`
3. `staleAfterDays`
4. `reason`
5. `activeEntries`
6. `deferredEntries`

其中：

1. `activeEntries`
   - 当前仍在缓存里的高价值条目
2. `deferredEntries`
   - 因为“过旧、低命中、低优先级”而暂时退出缓存的条目

## 记忆写法原则

项目记忆和全局记忆都不是“第二份详细归档”，而是缓存层。

写法上要遵守：

1. 只写高密度、可执行、未来值得再次注入的内容
2. 优先写稳定规则和主动注意事项
3. 达到阈值后，保留高命中、高检索、最近仍活跃的内容
4. 对长期没有命中的条目执行“暂时遗忘”，但不要删除详细条目

## 编码完整性

归档前必须保证 payload 没有在传输层损坏：

1. 不得包含连续四个以上 ASCII 问号。
2. 不得包含 `U+FFFD` replacement character。
3. 不得包含私用区字符。
4. Windows / PowerShell / Codex `shell_command` 场景中，不要直接把中文 payload 写进命令文本；使用 UTF-8 `--payload-file`，或使用 ASCII `\u` 转义 JSON。

CLI 会在写入前拒绝疑似乱码 payload，防止 `PROJECT_MEMORY.md`、`GLOBAL_MEMORY.md`、`failures/` 和 `notes/` 被污染。

## 推荐 CLI

```bash
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-file payload.json
python scripts/mistakebook_cli.py query --host codex --project-root . --scope both --text "<当前任务>" --limit 3
python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<当前任务>"
python scripts/mistakebook_cli.py touch --host codex --project-root . --scope both --case-id <case-id> --kind hit
python scripts/mistakebook_cli.py consolidate --host codex --project-root . --scope both
python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval
```

`query`、`context --query` 和 `scholar` 都会返回 `evidencePacket`。它至少包含 `shouldInject`、`confidence`、`matchedCaseIds`、`whyMatched`、`riskOfFalsePositive` 和 `retrievalMethod`，用于防止低置信误注入。
