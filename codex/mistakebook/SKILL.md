---
name: mistakebook
description: "识别用户正在纠正你、要求返工、指出你重复犯错，或要求记录长期注意事项的场景，进入带人工确认的闭环。统一支持 `mistake` 与 `note` 两类条目，写入项目级和/或全局级错题集 / 记事本，并同步刷新缓存式记忆。如果同一个案例被用户否定两次以上，或用户说“你需要根据你见过最有效的方法来处理这个问题”或输入“/ascended”，自动升级到飞升模式（Ascended Mode），全面检索项目级/全局级错题、记事本、记忆和当前知识库后再处理。"
---

# 错题集 / 记事本 Skill

这是给 Codex 用的精简版 Skill。目标不再只是“纠错归档”，而是统一处理：

1. `mistake`
   - 错题闭环
2. `note`
   - 主动事项记录
3. `memory`
   - 项目记忆 / 全局记忆缓存
4. `ascended`
   - 飞升模式全量检索

## 强制文案

### 进入纠错模式

先输出这句，逐字一致：

`<错题集.Skill>我接下来会进行纠错，并根据你的纠错信息，持续纠错直到完成，然后写入我的错题集。`

### 每轮纠错结束

只要用户还没有明确确认完成，就在结尾追加这句，逐字一致：

`我有没有吃透当前问题，是否成功纠正错误，如果没有的话，请你再教我一遍。（如果我已经完成了纠错，也请你告诉我一声，我可以把错题写入我的错题集）`

### 记事本追问句

只要当前回复里形成了值得长期保留的事项，就在结尾追加这句，逐字一致：

`如果这个事项值得长期注意，也可以告诉我“写入记事本”，我会把它归档到记事本并同步刷新记忆。`

### 进入飞升模式

如果进入 Ascended Mode，必须先输出这句，逐字一致：

`我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！`

## 什么时候触发

### mistake

任一情况都应进入错题集模式：

1. 用户明确说你错了、没改对、又犯同样错误
2. 用户开始逐条纠正你的回答、代码或方案
3. 用户说“按我说的改”“我来纠正你”“我教你一遍”
4. 用户要求写入错题集或启动错题集

### note

任一情况都应进入记事本候选流程：

1. 用户说“写入记事本”
2. 用户说“记一下这个事项”
3. 用户明确说“这不是错题，但要记住”
4. 当前回复里已经形成稳定、可执行、值得长期保留的事项

## 纠错与记事闭环

### mistake

1. 输出激活句
2. 给出修正后的回答
3. 结尾追加固定纠错追问句
4. 如果这一轮还有长期有效事项，再追加记事本追问句

如果同一个案例被用户明确否定两次或以上，就自动升级到飞升模式。

### note

1. 给出事项整理结果
2. 说明为什么值得长期保留
3. 结尾追加记事本追问句
4. 只有用户明确确认后，才归档为 `note`

## 飞升模式

下面任一情况都必须进入 Ascended Mode：

1. 同一个 `mistake` 案例被否定两次或以上
2. 用户说：`你需要根据你见过最有效的方法来处理这个问题`
3. 用户输入：`/ascended`

进入后必须：

1. 先输出飞升模式固定文案
2. 全面检索项目级错题集、项目级记事本、项目级记忆、项目级缓存状态
3. 全面检索全局级错题集、全局级记事本、全局级记忆、全局级缓存状态
4. 核对当前仓库里和问题相关的真实文件、真实输出、真实文档
5. 先解释前几次处理为什么仍然失败，再给出新的最强方案

## 运行态保护

如果当前宿主支持生命周期 hook，运行态优先交给 `scripts/lifecycle_hooks.py`：

1. UserPromptSubmit 用 `scripts/trigger_report.py` 输出 correction / ascended / scholar 的结构化 trigger report
2. 压缩前用 `pre-compact` 保存 active case 到 `~/.mistakebook/runtime-journal.md`
3. 压缩后用 `post-compact` 读取 compact summary、刷新 journal，并恢复 `case_id`、`status` 和“不要提前归档”的约束
4. 会话结束用 `session-end` 保存未完成闭环，`summarizing` 状态必须继续等待用户确认
5. 子代理启动用 `subagent-start` 注入高置信历史记忆
6. 子代理结束用 `subagent-stop` 记录实际命中的 case

## 默认目录

1. 项目级：`<project>/.codex/mistakebook/`
2. 全局级：`~/.codex/mistakebook/`

每个 store 里至少有：

1. `failures/`
2. `notes/`
3. `memory/`
4. `state/`

## 优先用脚本

如果仓库里存在 `scripts/mistakebook_cli.py`，优先这样做：

```bash
python scripts/mistakebook_cli.py bootstrap --host codex --project-root .
python scripts/mistakebook_cli.py consolidate --host codex --project-root . --scope both
python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval
```

归档时三选一：

1. `--payload-file <file>`
2. `--payload '<json>'`
3. `--payload-stdin`

推荐优先使用 `--payload-stdin`，这样不需要先写临时 JSON 文件。

归档 payload 必须包含 `"userConfirmed": true`。这个字段表示用户已经明确确认当前纠错或记事项可以写入，CLI 会拒绝未确认 payload。

如果归档命令传入 `--runtime-state-file`，只能在 `status=summarizing` 时写入；当 runtime state 里已有 `case_id` 时，payload 必须提供相同的 `caseId`。

编码完整性要求：

1. 不要在 Windows / PowerShell / Codex `shell_command` 里把中文 payload 直接写进命令文本。
2. 优先用 UTF-8 `--payload-file`，或用 ASCII `\u` 转义 JSON 走 `--payload-stdin`。
3. CLI 会拒绝连续四个以上问号、`U+FFFD` replacement character、私用区字符；遇到 `payload contains likely encoding corruption` 时，重新生成 payload，不要归档。

### `mistake` 最小模板

```json
{
  "entryType": "mistake",
  "title": "一句话标题",
  "summary": "一句话总结",
  "userConfirmed": true,
  "scopeDecision": "project",
  "scopeReasoning": ["为什么归到这个 scope"],
  "rules": ["以后必须遵守什么"],
  "confirmedUnderstanding": ["这次已经吃透了什么"],
  "originalPrompt": "用户原始问题",
  "correctionFeedback": "用户的纠错反馈",
  "finalReply": "修正后的最终回答"
}
```

### `note` 最小模板

```json
{
  "entryType": "note",
  "title": "一句话标题",
  "summary": "一句话总结",
  "userConfirmed": true,
  "scopeDecision": "project",
  "scopeReasoning": ["为什么归到这个 scope"],
  "rules": ["以后必须注意什么"],
  "confirmedUnderstanding": ["这条事项为什么成立"],
  "noteReason": "为什么值得长期记录",
  "noteContent": ["这条事项的核心内容"]
}
```

### bash 示例

```bash
cat <<'EOF' | python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-stdin
{
  "entryType": "mistake",
  "title": "没有先读真实实现",
  "summary": "修改前没有先核对真实脚本实现。",
  "userConfirmed": true,
  "scopeDecision": "both",
  "scopeReasoning": ["当前项目里需要复盘", "这个规则跨项目也成立"],
  "rules": ["修改协议前先读真实实现"],
  "confirmedUnderstanding": ["协议更新必须先和真实实现对齐"],
  "originalPrompt": "用户要求更新文档",
  "correctionFeedback": "用户指出我没有先读代码",
  "finalReply": "已先核对脚本后再修正文档"
}
EOF
```

### PowerShell 示例

```powershell
$payload = '{"entryType":"note","title":"\u4e2d\u6587\u8bb0\u4e8b","summary":"\u901a\u8fc7 ASCII Unicode escape \u4f20\u8f93\u4e2d\u6587","userConfirmed":true,"scopeDecision":"project","scopeReasoning":["\u907f\u514d PowerShell \u4f20\u8f93\u5c42\u6539\u5199\u5b57\u7b26"],"rules":["Markdown \u5199\u5165\u5fc5\u987b\u4fdd\u6301 UTF-8"],"confirmedUnderstanding":["\u4e0d\u628a\u5df2\u7ecf\u53d8\u6210\u95ee\u53f7\u7684 payload \u5f52\u6863"],"noteReason":"\u9632\u6b62 PROJECT_MEMORY.md \u4e71\u7801","noteContent":["\u4f7f\u7528 UTF-8 \u6587\u4ef6\u6216 ASCII \\u JSON"]}'
$payload | python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-stdin
```

## 记忆原则

项目记忆和全局记忆是缓存，不是流水账。

默认策略：

1. 条目少时可以几乎全量保留
2. 达到阈值后按命中、检索、新旧程度筛选
3. 长期低命中内容暂时退出缓存
4. 详细条目永远保留在 `failures/` 和 `notes/`

## 行为评测

改动触发词、归档、检索、compact 恢复或宿主入口后，运行：

```bash
python scripts/eval_harness.py --root .
```

这会统一验证 trigger recall、trigger precision、archive contract、retrieval quality、compact recovery 和 cross-host matrix。

## 禁止事项

1. 未经用户确认，禁止归档
2. 不要只记录“错在哪里”，也要记录“已经吃透什么”
3. 不要把项目私有细节原样塞进全局记忆
4. 不要把暂时遗忘理解成删除详细条目
## Scholar Preflight

在新的普通任务开始前，如果当前不在 `mistake` 纠错闭环、`note` 流程或 `Ascended Mode` 里，先运行轻量预检：

```bash
python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<当前任务>"
```

只有当 `scholar` 返回 `shouldInject = true` 时，才在正式回答前输出一行历史提醒；如果返回 `shouldInject = false`，保持静默，不要展示 query 结果。判断时优先看 `evidencePacket` 里的 `confidence`、`whyMatched` 和 `riskOfFalsePositive`。进入纠错闭环、`note` 流程或 `ascended` 后，不要再运行 `scholar`。

如果用户说 `scholar off` / `scholar on`，可以关闭或恢复预检；长期配置使用：

```bash
python scripts/mistakebook_cli.py config --scholar off
python scripts/mistakebook_cli.py config --scholar on
```
