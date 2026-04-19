# Archive Schema

## 归档 payload

推荐使用下面的 JSON 结构：

```json
{
  "schemaVersion": "1.0.0",
  "host": "codex",
  "agentId": "codex",
  "sessionId": "optional",
  "traceId": "optional",
  "caseId": "optional",
  "archivedAt": "2026-04-19T15:00:00Z",
  "title": "没有先读真实文件就下结论",
  "summary": "本次错误的核心是没有先核对真实文件，导致判断偏离实际代码。",
  "mistakeTypes": ["fact-check", "premature-assumption"],
  "severity": "medium",
  "correctionAttemptCount": 3,
  "ascendedTriggered": true,
  "ascendedTriggerReason": "同一个案例被用户连续否定两次后自动升级",
  "knowledgeSourcesReviewed": [
    "project_failures",
    "project_memory",
    "global_failures",
    "global_memory",
    "current_repo_files"
  ],
  "scopeDecision": "both",
  "scopeReasoning": [
    "这次案例发生在当前仓库的具体文件上，项目内有复盘价值",
    "但“先读真实文件再下结论”也是稳定的全局规则"
  ],
  "keywords": ["read-first", "fact-check", "source-of-truth"],
  "rules": [
    "在评价实现是否正确前，先读真实文件或真实输出",
    "用户开始纠正时，先进入纠错闭环，不要把纠正当作普通补充需求"
  ],
  "confirmedUnderstanding": [
    "我已经理解：事实来源必须优先于记忆和猜测",
    "我已经理解：用户确认完成前不能提前归档"
  ],
  "whatWentWrong": [
    "过早根据印象判断实现细节",
    "没有把用户纠正视为同一个持续案例"
  ],
  "preventionChecklist": [
    "先读真实文件",
    "先核对输出证据",
    "未获确认前不归档"
  ],
  "projectMemoryMarkdown": "# 项目记忆\n...",
  "globalMemoryMarkdown": "# 全局记忆\n...",
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

## 最低要求

下面字段最少要有：

1. `title`
2. `summary`
3. `rules`
4. `confirmedUnderstanding`
5. `scopeDecision`
6. `scopeReasoning`
7. `correctionAttemptCount`
8. `ascendedTriggered`
9. `ascendedTriggerReason`
10. `originalPrompt`
11. `originalReply`
12. `correctionFeedback`
13. `finalReply`

## 单条 Markdown 结构

推荐写成下面这种结构化 Markdown：

```markdown
# 标题

- archived_at: ...
- host: ...
- session: ...
- trace: ...
- scope: ...
- severity: ...
- correction_attempt_count: ...
- ascended_triggered: ...
- keywords: ...

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

## 归档范围判断
- ...

## 神级模式记录
- ...

## 神级模式检索来源
- ...

## 原始问题
...

## 原始回答
...

## 用户纠错反馈
...

## 追纠记录
1. ...

## 最终正确回答
...

## 项目记忆增量
- ...

## 全局记忆增量
- ...
```

## 记忆文档模板

### 项目记忆

```markdown
# 项目记忆

- updated_at: ...
- source_cases: ...

## 当前稳定规则
- ...

## 已经吃透
- ...

## 高风险提醒
- ...

## 最近一次刷新原因
- ...
```

### 全局记忆

```markdown
# 全局记忆

- updated_at: ...
- source_cases: ...

## 通用稳定规则
- ...

## 通用已吃透
- ...

## 通用高风险提醒
- ...

## 最近一次刷新原因
- ...
```

## 写法原则

1. 详细案例写全
2. 记忆摘要写短
3. 全局条目适度泛化
4. 只写已经确认、真实有效、未来值得再次注入的内容
