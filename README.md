# Mistakebook Skill

错题集 / 记事本 Skill。它的目标不是单纯“认错”，而是把 Agent 的纠错、长期注意事项、项目记忆、全局记忆和飞升模式检索，变成一套真正可落地的工作流。

![](docs/assets/825b6024898386ec7ccef3496b3efe26.jpg)

## 这次版本的核心升级

当前版本已经从“单一错题集”升级成统一模型：

1. 支持两类条目
   - `mistake`：已经完成纠错、值得复盘的错误案例
   - `note`：不一定是错误，但值得长期保留的主动事项
2. 每次归档都会刷新
   - 项目记忆
   - 全局记忆
3. 记忆不是流水账，而是缓存
   - 初期可以接近全量保留
   - 达到阈值后开始整理和暂时遗忘
   - 详细条目仍保留在 `failures/` 和 `notes/`
4. 飞升模式不再只看错题
   - 还会检索记事本
   - 检索记忆缓存状态
   - 检索当前真实文件、真实输出、真实文档

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

## 仓库结构

```text
.
├─ .claude-plugin/              # Claude 风格插件元数据
├─ .codex/                      # Codex 安装说明
├─ codex/mistakebook/           # Codex 精简版 Skill
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
  - Codex 精简版协议
- [scripts/mistakebook_cli.py](./scripts/mistakebook_cli.py)
  - 初始化、归档、命中、整理、上下文导出 CLI
- [commands/mistakebook.md](./commands/mistakebook.md)
  - `/mistakebook` 统一入口
- [commands/notebook.md](./commands/notebook.md)
  - 记事本手动入口
- [commands/ascended.md](./commands/ascended.md)
  - 飞升模式手动入口

## 存储结构

默认每个 store 至少包含：

```text
mistakebook/
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

其中：

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
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload '{"entryType":"note","title":"...","summary":"..."}'
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-stdin
```

归档输入三选一：

1. `--payload-file`
2. `--payload`
3. `--payload-stdin`

支持的条目类型：

1. `entryType = mistake`
2. `entryType = note`

推荐在 Codex 中优先使用 `--payload-stdin`，这样不需要额外写临时 JSON 文件。

#### `mistake` 最小模板

```json
{
  "entryType": "mistake",
  "title": "一句话标题",
  "summary": "一句话总结",
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
@'
{
  "entryType": "note",
  "title": "新增事项要同步刷新记忆",
  "summary": "记事本条目归档后要同步更新 memory。",
  "scopeDecision": "project",
  "scopeReasoning": ["这是当前项目内的实现约束"],
  "rules": ["新增 note 后同步刷新 memory"],
  "confirmedUnderstanding": ["记事本和错题都属于统一记忆体系"],
  "noteReason": "这是长期有效的实现约束",
  "noteContent": ["归档 note 后同步刷新项目记忆"]
}
'@ | python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-stdin
```

### 3. 记录命中或检索

```bash
python scripts/mistakebook_cli.py touch --host codex --project-root . --scope both --case-id <case-id> --kind hit
python scripts/mistakebook_cli.py touch --host codex --project-root . --scope both --case-id <case-id> --kind retrieval
```

### 4. 重写缓存记忆

```bash
python scripts/mistakebook_cli.py consolidate --host codex --project-root . --scope both
```

### 5. 导出飞升模式上下文

```bash
python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval
```

### 6. 查看状态

```bash
python scripts/mistakebook_cli.py status --host codex --project-root . --scope both
```

### 7. 自动识别开关

```bash
python scripts/mistakebook_cli.py config --auto-detect on
python scripts/mistakebook_cli.py config --auto-detect off
```

### 8. 评估触发规则

```bash
python scripts/eval_triggers.py
```

这会直接读取 `hooks/hooks.json` 里的 `UserPromptSubmit` matcher，并对 `evals/trigger-prompts/` 下的样本做回归检查。只要有任一样本不符合预期，脚本就会以非 `0` 退出码结束。

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

常用入口：

1. `$mistakebook`
2. `/prompts:mistakebook`
3. `/prompts:notebook`（如果宿主加载了该 prompt）
4. `/ascended`

### Claude 风格宿主

主要依赖：

1. `.claude-plugin/plugin.json`
2. `commands/mistakebook.md`
3. `commands/notebook.md`
4. `commands/ascended.md`
5. `hooks/hooks.json`

### VSCode Copilot

主要依赖：

1. [vscode/copilot-instructions.md](./vscode/copilot-instructions.md)
2. [vscode/instructions/mistakebook.instructions.md](./vscode/instructions/mistakebook.instructions.md)
3. [vscode/prompts/mistakebook.prompt.md](./vscode/prompts/mistakebook.prompt.md)
4. [vscode/prompts/notebook.prompt.md](./vscode/prompts/notebook.prompt.md)
5. [vscode/prompts/ascended.prompt.md](./vscode/prompts/ascended.prompt.md)

## 当前已经实现

当前仓库已经具备：

1. `mistake` / `note` 双条目模型
2. 项目级 / 全局级双层存储
3. 项目记忆 / 全局记忆缓存
4. 命中 / 检索统计
5. `consolidate` 缓存式记忆重写
6. 飞升模式上下文导出
7. 多宿主协议镜像

## 后续还可以继续增强

这个版本已经能真实使用，但还有几个方向可继续演进：

1. 增加更细粒度的自动 scope 推断
2. 增加更完整的 `evals` 回归 runner
3. 增加更细的命中概率模型
4. 增加多轮 case 版本演进视图
5. 为更多宿主补适配层

## 关于 `reference_code/`

`reference_code/` 只是本地参考材料，不属于这个 Skill 项目的正式发布内容。

仓库的 `.gitignore` 已经把它排除掉，避免把参考仓库一并提交进去。
