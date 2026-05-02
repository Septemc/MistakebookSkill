<div align="center">

**中文** · [English](./README.en.md)

# 📝 MistakeBook Skill

#### 我已经刷了几万道练习题，我已经总结了海量的错题，我现在什么都不缺了! 
纠错闭环 + 飞升模式 + 缓存式记忆

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)

</div>

# Mistakebook Skill

> 我已经刷了几万道练习题，我已经总结了海量的错题，我现在什么都不缺了!

![](docs/assets/825b6024898386ec7ccef3496b3efe26.jpg)

---

## 📦 安装方式

在 Claude Code、Codex 等支持 Skill 的 Agent 里，直接说：

```
帮我安装 Mistakebook Skill：https://github.com/Septemc/MistakebookSkill.git
```

---

## 这个项目解决什么问题

普通 Agent 在被用户纠正时，常见问题不是“道歉不够诚恳”，而是：

1. 这轮改完，下轮又犯同类错误
2. 用户纠错只停留在聊天记录，不能沉淀成结构化经验
3. 已经被纠正多次了，Agent 还是在浅层修补
4. 没有区分“项目特有经验”和“跨项目通用规则”
5. 没有把“值得长期注意但不一定是错题”的事项沉淀下来
6. 记忆越积越长，最后没人敢再读，也没人知道该忘什么

`Mistakebook Skill` 的目标，就是把这些问题转化成真正的记忆资产。

## 核心能力

### 1. 统一闭环：错题 + 记事本

这个项目不再只处理错题，而是统一处理两种场景：

1. 用户在纠正你
   - 进入 `mistake` 闭环
2. 用户在要求你保留长期事项
   - 进入 `note` 闭环

### 2. 固定纠错闭环

一旦进入纠错模式，Agent 必须先输出固定激活文案：

`<错题集.Skill>我接下来会进行纠错，并根据你的纠错信息，持续纠错直到完成，然后写入我的错题集。`

之后每轮纠错结束，如果用户还没有明确确认完成，都必须在结尾继续追问：

`我有没有吃透当前问题，是否成功纠正错误，如果没有的话，请你再教我一遍。（如果我已经完成了纠错，也请你告诉我一声，我可以把错题写入我的错题集）`

### 3. 固定记事本追问句

只要当前回复里已经形成一个值得长期保留的事项，Agent 应该在结尾追加：

`如果这个事项值得长期注意，也可以告诉我“写入记事本”，我会把它归档到记事本并同步刷新记忆。`

### 4. 只在明确确认后归档

只有用户明确确认时，才允许归档：

1. 对 `mistake`
   - `可以了`
   - `这次对了`
   - `归档吧`
   - `写入错题集`
   - `完成纠错`
2. 对 `note`
   - `写入记事本`
   - `记下来`
   - `长期保留这条`

### 5. 记忆是缓存，不是全文仓库

每次写入 `mistake` 或 `note` 后，都会刷新：

1. 项目记忆
2. 全局记忆

这些记忆文件的定位是缓存层：

1. 只保留高密度、可执行、未来值得再次注入的内容
2. 达到阈值后，不再机械累加
3. 低命中、长期不再活跃的内容会暂时退出缓存
4. 详细条目仍保留在详细归档目录里

### 6. 飞升模式（Ascended Mode）

当普通纠错已经不够时，或者用户明确要求：

1. `你需要根据你见过最有效的方法来处理这个问题`
2. `/ascended`

Agent 会升级到飞升模式。

进入飞升模式时，Agent 必须先输出：

`我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！`

飞升模式会尽量完整地检索：

1. 项目级错题集
2. 项目级记事本
3. 项目级记忆
4. 项目级缓存状态
5. 全局级错题集
6. 全局级记事本
7. 全局级记忆
8. 全局级缓存状态
9. 当前仓库中和问题相关的真实文件、真实输出、真实文档
10. 当前 case 的完整纠错链 / 事项链

### 7. 学霸模式

当这是一个新的正常任务，而不是纠错、记事本归档或飞升场景时：

1. 先运行 `scholar`
2. 只在高置信命中历史案例时，给出一行历史提醒

Agent 会进入学霸模式预检。

进入学霸模式时，Agent 应优先执行：

`python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<当前任务>"`

学霸模式会尽量轻量地完成这些事情：

1. 检索项目级错题集
2. 检索项目级记事本
3. 检索项目级记忆
4. 检索全局级错题集
5. 检索全局级记事本
6. 检索全局级记忆
7. 按字段命中、SQLite FTS/BM25 和 memory score 对候选案例排序
8. 返回 `evidencePacket`，说明 `matchedCaseIds`、`whyMatched`、`confidence` 和 `riskOfFalsePositive`
9. 只返回最相关的高置信结果
10. 只在 `shouldInject = true` 时输出一行 `message`
11. 不写归档、不刷新 memory、也不增加 retrieval 记账

学霸模式和飞升模式的职责边界：

1. 学霸模式负责答前避错
2. 飞升模式负责失败后的升级处置
3. 一旦进入纠错闭环、记事本归档或 `Ascended Mode`，就必须停止运行学霸模式

## 仓库结构

```text
.
├─ .claude-plugin/              # Claude 风格插件元数据
├─ .codex/                      # Codex 安装说明
├─ codex/ascended/              # Codex 飞升模式 skill-chip 包装入口
├─ codex/mistakebook/           # Codex 主 skill-chip 入口
├─ codex/notebook/              # Codex 记事本 skill-chip 包装入口
├─ codex/scholar/               # Codex scholar skill-chip 包装入口
├─ commands/                    # 手动命令入口
├─ evals/                       # 触发词回归样例
├─ hooks/                       # Claude 风格自动触发 / restore hooks
├─ scripts/                     # 归档、缓存整理与上下文导出 CLI
├─ skills/mistakebook/          # 通用核心 Skill
├─ vscode/                      # VSCode Copilot 适配
├─ plugin.json                  # 顶层插件包元数据
└─ README.md
```

## 关键文件

- [skills/mistakebook/SKILL.md](./skills/mistakebook/SKILL.md)
  - 通用核心协议
- [skills/mistakebook/references/activation-patterns.md](./skills/mistakebook/references/activation-patterns.md)
  - 错题 / 记事本 / 飞升模式触发规则
- [skills/mistakebook/references/storage-and-scope.md](./skills/mistakebook/references/storage-and-scope.md)
  - `failures/`、`notes/`、`memory/`、`state/` 的布局与缓存策略
- [skills/mistakebook/references/archive-schema.md](./skills/mistakebook/references/archive-schema.md)
  - `mistake` / `note` 统一 schema
- [skills/mistakebook/references/ascended-mode.md](./skills/mistakebook/references/ascended-mode.md)
  - 飞升模式协议
- [codex/mistakebook/SKILL.md](./codex/mistakebook/SKILL.md)
  - Codex 主 skill-chip 协议
- [codex/ascended/SKILL.md](./codex/ascended/SKILL.md)
  - Codex 飞升模式 skill-chip 包装入口
- [codex/notebook/SKILL.md](./codex/notebook/SKILL.md)
  - Codex 记事本 skill-chip 包装入口
- [codex/scholar/SKILL.md](./codex/scholar/SKILL.md)
  - Codex scholar skill-chip 包装入口
- [scripts/mistakebook_cli.py](./scripts/mistakebook_cli.py)
  - 初始化、归档、命中、整理、上下文导出 CLI
- [scripts/lifecycle_hooks.py](./scripts/lifecycle_hooks.py)
  - PreCompact / PostCompact / SessionEnd / SubagentStart / SubagentStop 生命周期入口
- [scripts/trigger_report.py](./scripts/trigger_report.py)
  - UserPromptSubmit 的纠错、飞升、scholar 结构化 trigger report
- [scripts/eval_harness.py](./scripts/eval_harness.py)
  - 统一行为评测入口，覆盖触发、归档契约、检索质量、压缩恢复和跨宿主矩阵
- [commands/mistakebook.md](./commands/mistakebook.md)
  - `/mistakebook` 统一入口
- [commands/scholar.md](./commands/scholar.md)
  - 学霸模式手动入口
- [commands/notebook.md](./commands/notebook.md)
  - 记事本手动入口
- [commands/ascended.md](./commands/ascended.md)
  - 飞升模式手动入口
- [hooks/scholar-preflight-trigger.sh](./hooks/scholar-preflight-trigger.sh)
  - Claude 风格宿主的 scholar 轻量预检 hook
- [hooks/lifecycle-pre-compact.sh](./hooks/lifecycle-pre-compact.sh)
  - Claude 风格宿主的运行态 checkpoint hook；同目录还有 PostCompact、SessionEnd、SubagentStart、SubagentStop wrapper

## 存储结构

所有 Agent 工具（Codex、Claude Code、VSCode、通用）共享统一的存储路径：

- **项目级存储**：`<project>/.mistakebook/`
- **全局级存储**：`~/.mistakebook/`

每个 store 至少包含：

```text
.mistakebook/
├─ failures/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ notes/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ memory/
│  ├─ PROJECT_MEMORY.md
│  └─ GLOBAL_MEMORY.md
└─ state/
   ├─ catalog.json
   └─ memory_state.json
```

### 从旧路径迁移

如果你之前使用过旧版存储路径（`.codex/mistakebook/`、`.claude/mistakebook/`、`.vscode/mistakebook/`），运行以下命令自动迁移到统一路径：

```bash
python scripts/mistakebook_cli.py migrate --host codex --project-root .
```

迁移脚本会自动：
1. 扫描所有旧版目录
2. 合并 catalog（按 caseId 去重）
3. 移动 failures/notes 文件
4. 删除旧版目录

### 存储说明

1. `failures/`
   - 详细错题条目
2. `notes/`
   - 详细记事本条目
3. `memory/*.md`
   - 面向未来再次注入的缓存摘要
4. `state/catalog.json`
   - 统一索引
5. `state/memory_state.json`
   - 当前缓存和暂时遗忘候选的状态

## CLI 用法

本地脚本入口是 [scripts/mistakebook_cli.py](./scripts/mistakebook_cli.py)。

### 1. 初始化目录

```bash
python scripts/mistakebook_cli.py bootstrap --host codex --project-root .
```

### 2. 归档条目

```bash
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-file payload.json
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload '{"entryType":"note","title":"...","summary":"...","userConfirmed":true}'
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-stdin
python scripts/mistakebook_cli.py archive --host codex --project-root . --runtime-state-file path/to/runtime_state.json --payload-stdin
```

归档输入三选一：

1. `--payload-file`
2. `--payload`
3. `--payload-stdin`

支持的条目类型：

1. `entryType = mistake`
2. `entryType = note`

归档 payload 必须包含 `"userConfirmed": true`。这个字段表示当前条目已经得到用户明确确认，CLI 会拒绝未确认 payload，防止提前污染错题集或记事本。

如果同时传入 `--runtime-state-file`，CLI 只允许 `status=summarizing` 的状态进入归档；当 runtime state 里已有 `case_id` 时，payload 必须提供相同的 `caseId`。

推荐在 Codex 中优先使用 `--payload-stdin`，这样不需要额外写临时 JSON 文件。

编码安全约束：

1. 在 Windows / PowerShell / Codex `shell_command` 场景里，不要把中文 payload 直接塞进命令文本；如果传输层已经把中文变成连续问号，CLI 无法还原原文。
2. 优先使用 UTF-8 的 `--payload-file`，或者用 ASCII `\u` 转义 JSON 走 `--payload-stdin`。
3. CLI 会在归档前拒绝疑似乱码 payload，包括连续四个以上问号、`U+FFFD` replacement character、私用区字符，避免污染 `PROJECT_MEMORY.md`、`GLOBAL_MEMORY.md` 和详细条目。

#### `mistake` 最小模板

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

#### `note` 最小模板

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

#### bash 示例

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

#### PowerShell 示例

```powershell
$payload = '{"entryType":"note","title":"\u4e2d\u6587\u8bb0\u4e8b","summary":"\u901a\u8fc7 ASCII Unicode escape \u4f20\u8f93\u4e2d\u6587","userConfirmed":true,"scopeDecision":"project","scopeReasoning":["\u907f\u514d PowerShell \u4f20\u8f93\u5c42\u6539\u5199\u5b57\u7b26"],"rules":["Markdown \u5199\u5165\u5fc5\u987b\u4fdd\u6301 UTF-8"],"confirmedUnderstanding":["\u4e0d\u628a\u5df2\u7ecf\u53d8\u6210\u95ee\u53f7\u7684 payload \u5f52\u6863"],"noteReason":"\u9632\u6b62 PROJECT_MEMORY.md \u4e71\u7801","noteContent":["\u4f7f\u7528 UTF-8 \u6587\u4ef6\u6216 ASCII \\u JSON"]}'
$payload | python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-stdin
```

### 3. 统一检索接口

```bash
python scripts/mistakebook_cli.py query --host codex --project-root . --scope both --text "先读真实实现再改文档" --limit 3
```

`query` 会从 project / global 的 `catalog` 中找出与当前问题最相关的 Top-N 条目，先用字段命中和 SQLite FTS/BM25 做召回，再叠加现有 memory score 做排序。输出会包含 `evidencePacket`，用于解释是否应注入、置信度、命中的 case、命中原因和误注入风险；它是后续学霸模式和飞升模式裁剪的统一底座。

### 4. 记录命中或检索

```bash
python scripts/mistakebook_cli.py touch --host codex --project-root . --scope both --case-id <case-id> --kind hit
python scripts/mistakebook_cli.py touch --host codex --project-root . --scope both --case-id <case-id> --kind retrieval
```

### 5. 重写缓存记忆

```bash
python scripts/mistakebook_cli.py consolidate --host codex --project-root . --scope both
```

### 6. 导出飞升模式上下文

```bash
python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval
python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --query "先读真实实现再改文档" --limit 3 --mark-retrieval
```

### 7. 查看状态

```bash
python scripts/mistakebook_cli.py status --host codex --project-root . --scope both
```

### 8. 迁移旧存储

```bash
python scripts/mistakebook_cli.py migrate --host codex --project-root .
```

自动检测并迁移旧版存储路径（`.codex/mistakebook/`、`.claude/mistakebook/`、`.vscode/mistakebook/`）到统一的 `.mistakebook/` 目录。

### 9. 自动识别开关

```bash
python scripts/mistakebook_cli.py config --auto-detect on
python scripts/mistakebook_cli.py config --auto-detect off
```

### 10. 生命周期 hook 演练

```bash
python scripts/trigger_report.py correction
python scripts/trigger_report.py ascended
python scripts/trigger_report.py scholar-preflight
python scripts/lifecycle_hooks.py pre-compact --state-file ~/.mistakebook/runtime-state.json
python scripts/lifecycle_hooks.py post-compact --compact-summary-file compact-summary.md
python scripts/lifecycle_hooks.py session-end --state-file ~/.mistakebook/runtime-state.json
python scripts/lifecycle_hooks.py subagent-start --host codex --project-root . --scope both --task-text "<子任务>"
python scripts/lifecycle_hooks.py subagent-stop --host codex --project-root . --scope both --case-id <case-id> --kind hit
```

这些入口把宿主生命周期收束成结构化 JSON hook 输出：压缩前保存 `runtime-journal.md`，压缩后可读取 compact summary 并刷新 runtime journal，SessionEnd 保存未完成闭环，子代理启动前注入高置信项目记忆，子代理结束后回写命中统计。

### 11. 评估触发规则

```bash
python scripts/eval_triggers.py
```

这会直接读取 `hooks/hooks.json` 里的 `UserPromptSubmit` matcher，并对 `evals/trigger-prompts/` 下的样本做回归检查。只要有任一样本不符合预期，脚本就会以非 `0` 退出码结束。

### 12. 统一行为评测

```bash
python scripts/eval_harness.py --root .
python scripts/eval_harness.py --root . --json
python scripts/eval_harness.py --root . --suite retrieval_quality --json
```

`eval_harness.py` 会把关键行为收束成一份结构化报告：

1. `trigger_recall`
   - 该触发时是否触发，包括普通纠错和飞升触发
2. `trigger_precision`
   - 不该触发时是否保持沉默
3. `archive_contract`
   - 未确认 payload 是否被拒绝，`summarizing` 状态下的确认 payload 是否被接受
4. `retrieval_quality`
   - `query`、`scholar`、`context --query` 是否把正确 case 排在第一
5. `compact_recovery`
   - `PreCompact` / `PostCompact` 是否保留 active case 并刷新 runtime journal
6. `cross_host`
   - Codex、Claude 风格 hooks、VSCode 入口是否都保留必要协议连接

## 推荐工作流

### 场景 1：自动进入纠错模式

1. 用户指出回答错误
2. Skill 自动触发
3. Agent 输出固定激活文案
4. Agent 按反馈修正
5. 每轮结尾固定追问
6. 如果同时形成长期事项，再询问是否写入记事本
7. 用户明确确认完成
8. Agent 归档 `mistake` 并刷新记忆

### 场景 2：主动记录事项

1. 用户说“写入记事本”或“记一下这个事项”
2. Agent 先整理当前事项
3. Agent 说明为什么值得长期保留
4. Agent 追问是否写入记事本
5. 用户明确确认
6. Agent 归档 `note` 并刷新记忆

### 场景 3：自动升级到飞升模式

1. 用户已经让 Agent 改了两次或以上
2. 用户仍然明确表示“不对 / 还是错 / 没理解”
3. Agent 自动进入 Ascended Mode
4. Agent 输出固定飞升模式回复语
5. Agent 全量检索错题、记事本、记忆和当前知识库
6. 解释前几次为什么失败
7. 选择当前最有效的方法重新处理

### 场景 4：手动启动飞升模式

1. 用户输入 `/ascended`
2. 或者用户说：`你需要根据你见过最有效的方法来处理这个问题`
3. Agent 输出飞升模式固定回复语
4. Agent 检索项目级 / 全局级错题、记事本、记忆与真实文件
5. Agent 解释为什么之前失败
6. Agent 选择最有效的方法重新处理

## 适配层

### Codex

Codex 安装说明见 [`.codex/INSTALL.md`](./.codex/INSTALL.md)。

推荐入口：

1. `$mistakebook`
2. `$ascended`
3. `$notebook`
4. `$scholar`

这些入口会以 skill chip 形式出现在输入框里，不会把长 prompt 正文直接展开出来。

兼容入口：

1. `/prompts:mistakebook`
2. `/prompts:ascended`
3. `/prompts:notebook`
4. `/prompts:scholar`

使用与触发规则：

- `$mistakebook`
  - Codex 默认主入口。先把它作为 skill chip 加载，再正常提问。
  - 加载后，如果用户说“你这里错了”“还没改对”“按我说的改”“我来纠正你”，进入 `mistake` 闭环。
  - 加载后，如果用户说“写入记事本”“记一下这个事项”“这不是错题，但要记住”，进入 `note` 候选流程。
  - 同一个案例被明确否定两次以上，或用户明确要求“根据你见过最有效的方法来处理”，升级到 `Ascended Mode`。
- `$ascended`
  - 手动强制进入飞升模式，用于当前问题已经失败、返工多轮、或你想直接要求全量检索时。
  - 它不是普通新任务入口，而是最强处理入口。
- `$notebook`
  - 手动进入 `note` 流程，先整理长期事项，再等待用户确认是否写入记事本。
  - 没有明确确认前，不会归档。
- `$scholar`
  - 新任务答前预检入口，只适合 fresh normal task。
  - 它只在高置信命中历史经验时输出一行提醒；如果 `shouldInject = false`，就静默继续。
  - 如果当前已经处在 `mistake`、`note` 或 `Ascended Mode`，就不应该再运行它。
- `/prompts:*`
  - 兼容入口，语义和上面对应，但它是 prompt 文件，不是 skill chip。
  - 在 Codex 输入框里会展开 prompt 正文，因此不适合追求 `$pua` 那种紫色 chip 体验。

典型用法：

1. `$mistakebook 帮我看这个改动哪里不稳`
2. `$ascended 这个问题前面已经反复失败了，重新全面检索后再处理`
3. `$notebook 把这个长期约束整理一下`
4. `$scholar 帮我先做答前避错，再给方案`

### Claude 风格宿主

主要依赖：

1. `.claude-plugin/plugin.json`
2. `commands/mistakebook.md`
3. `commands/scholar.md`
4. `commands/notebook.md`
5. `commands/ascended.md`
6. `hooks/hooks.json`

### VSCode Copilot

主要依赖：

1. [vscode/copilot-instructions.md](./vscode/copilot-instructions.md)
2. [vscode/instructions/mistakebook.instructions.md](./vscode/instructions/mistakebook.instructions.md)
3. [vscode/prompts/mistakebook.prompt.md](./vscode/prompts/mistakebook.prompt.md)
4. [vscode/prompts/scholar.prompt.md](./vscode/prompts/scholar.prompt.md)
5. [vscode/prompts/notebook.prompt.md](./vscode/prompts/notebook.prompt.md)
6. [vscode/prompts/ascended.prompt.md](./vscode/prompts/ascended.prompt.md)

## 关于 `reference_code/`

`reference_code/` 只是本地参考材料，不属于这个 Skill 项目的正式发布内容。

仓库的 `.gitignore` 已经把它排除掉，避免把参考仓库一并提交进去。

## License

MIT License - 详见 [LICENSE](./LICENSE)
