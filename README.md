# Mistakebook Skill

错题集.Skill。我已经刷了几万道练习题，我已经总结了海量的错题，我现在什么都不缺了！ / I have done tens of thousands of practice problems, and I have summarized a vast amount of wrong answers. Now, I am invincible.

![](docs/assets/825b6024898386ec7ccef3496b3efe26.jpg)

目标是把用户纠错过程进行沉淀：

1. 可归档的详细案例
2. 可复用的项目级经验
3. 可泛化的全局级规则
4. 未来可再次回注给 Agent 的精炼记忆
5. 在多次纠错仍失败时自动升级的 Ascended 神级模式

仓库主要内容如下：

1. 通用核心 Skill
2. Codex 适配
3. Claude 风格 plugin / hook 适配
4. VSCode Copilot 指令 / prompt 适配
5. 本地归档 CLI
6. 触发词回归样例
7. Ascended 神级模式协议

## 它解决什么问题

普通 Agent 在被用户纠正时，最常见的问题不是“认错”，而是：

1. 这轮改完，下轮又犯同类错误
2. 用户纠错只停留在聊天记录，不能沉淀成结构化记忆
3. 已经被纠正多次了，Agent 还是在浅层修补
4. 没有区分“项目特有经验”和“跨项目通用规则”
5. 没有把“已经吃透了什么”单独沉淀出来

`Mistakebook Skill` 的目标，就是把这些纠错过程变成真正的记忆资产。

## 核心能力

### 1. 自动识别纠错状态

当用户说出下面这类话时，Skill 会把当前对话视为“纠错闭环”而不是普通继续对话：

- `你这里错了`
- `这不对`
- `重新改`
- `我来纠正你`
- `你又犯同样的错`
- `还没改对`
- `启动错题集`
- `/mistakebook`

### 2. 固定纠错闭环

一旦进入纠错模式，Agent 必须先展示固定激活文案：

`【我发现这道题做错了，我接下来会进行纠错，并根据你的纠错信息，持续纠错直到完成，然后写入我的错题集】`

之后每一轮纠错结束，如果用户还没有明确确认完成，都必须在结尾继续追问：

`我当前有没有把问题吃透，有没有纠正错误，如果没有的话，麻烦你再教我一遍，好不好？（如果我已经完成了纠错，也请你告知我一声，我可以把错题写入我的错题集）`

### 3. 只在用户明确确认后归档

只有当用户明确表达下面这类意思时，才允许归档：

- `可以了`
- `这次对了`
- `归档吧`
- `写入错题集`
- `完成纠错`

这一步是整个设计里最关键的约束之一：不允许 Agent 自作主张地把“未真正纠正完成”的内容提前写入错题集。

### 4. 项目级 / 全局级双层记忆

每次归档都要做 scope 判断：

- `project`
  - 属于当前仓库、当前业务、当前项目流程的经验
- `global`
  - 属于跨项目通用的工程习惯、验证纪律、沟通纪律、推理纪律
- `both`
  - 当前案例既值得在项目内保留完整复盘，也能抽出可跨项目复用的稳定规则

### 5. 每次归档都刷新精炼记忆

归档不是只写一篇详细 Markdown。

它还会同步更新：

- 项目记忆
- 全局记忆

记忆必须保持短、真、可执行，不允许退化成聊天流水账。

### 6. Ascended 神级模式

当普通纠错已经进行了两次以上，用户仍然认为 Agent 没有改对，或者用户明确要求：

- `你需要根据你见过最有效的方法来处理这个问题`
- `/ascended`

Skill 会升级到 `Ascended Mode`。

进入神级模式时，Agent 必须先输出固定回复语：

`我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！`

进入后不再停留在浅层修补，而是要全面检索：

1. 项目级错题集
2. 项目级记忆
3. 全局级错题集
4. 全局级记忆
5. 当前仓库中和问题相关的真实文件、真实输出、真实文档
6. 当前 case 的完整用户纠错链

然后：

1. 先解释前几次纠错为什么仍然失败
2. 再选择当前最有效的一种处理方式
3. 继续留在纠错闭环中，直到用户明确确认完成

## 设计原则

这个项目吸收了 Storydex 错题集能力和多宿主 Skill 分发结构的优点，但做了几个明确增强：

1. 从“项目级纠错归档”扩展成“项目级 + 全局级”双层记忆
2. 把固定激活文案、固定追问文案、固定神级回复文案都写成硬约束
3. 提供本地 CLI，避免只停留在 Prompt 设计层
4. 为多宿主准备统一核心 Skill，再分别适配 Codex / Claude / VSCode
5. 增加 `evals/trigger-prompts`，方便回归测试误触发和漏触发
6. 引入 Ascended 神级模式，让多次纠错失败后的处理从“继续修补”升级为“全面检索 + 深度分析 + 选最强方案”

## 仓库结构

```text
.
├─ .claude-plugin/              # Claude 风格插件元数据
├─ .codex/                      # Codex 安装说明
├─ codex/mistakebook/           # Codex 精简版 Skill
├─ commands/                    # 手动命令入口
├─ evals/                       # 触发词回归样例
├─ hooks/                       # Claude 风格自动触发 / restore hooks
├─ scripts/                     # 归档与初始化 CLI
├─ skills/mistakebook/          # 通用核心 Skill
├─ vscode/                      # VSCode Copilot 适配
├─ plugin.json                  # 顶层插件包元数据
└─ README.md
```

### 关键文件

- [skills/mistakebook/SKILL.md](./skills/mistakebook/SKILL.md)
  - 通用核心行为协议
- [skills/mistakebook/references/activation-patterns.md](./skills/mistakebook/references/activation-patterns.md)
  - 触发 / 不触发规则
- [skills/mistakebook/references/storage-and-scope.md](./skills/mistakebook/references/storage-and-scope.md)
  - 项目级 / 全局级存储与 scope 判断
- [skills/mistakebook/references/archive-schema.md](./skills/mistakebook/references/archive-schema.md)
  - 归档 JSON 和 Markdown 结构
- [skills/mistakebook/references/ascended-mode.md](./skills/mistakebook/references/ascended-mode.md)
  - Ascended 神级模式协议
- [codex/mistakebook/SKILL.md](./codex/mistakebook/SKILL.md)
  - Codex 精简版协议
- [scripts/mistakebook_cli.py](./scripts/mistakebook_cli.py)
  - 本地初始化、归档和配置 CLI
- [hooks/hooks.json](./hooks/hooks.json)
  - 自动触发、Ascended 升级与上下文压缩前 checkpoint 规则
- [hooks/correction-trigger.sh](./hooks/correction-trigger.sh)
  - 普通纠错闭环触发提示
- [hooks/ascended-trigger.sh](./hooks/ascended-trigger.sh)
  - 神级模式触发提示
- [commands/mistakebook.md](./commands/mistakebook.md)
  - `/mistakebook` 命令路由
- [commands/ascended.md](./commands/ascended.md)
  - `/ascended` 神级模式入口

## 安装与接入

### Codex

Codex 安装说明见 [`.codex/INSTALL.md`](./.codex/INSTALL.md)。

安装后主要触发方式有三种：

1. 自动触发
   - 通过 `SKILL.md` 的 description 匹配纠错短语
2. 手动触发错题集
   - `$mistakebook`
   - `/prompts:mistakebook`
3. 手动触发神级模式
   - `/ascended`
   - `你需要根据你见过最有效的方法来处理这个问题`

### Claude 风格宿主

Claude 风格适配分成三层：

1. `.claude-plugin/plugin.json`
   - 插件元数据
2. `commands/mistakebook.md`
   - 手动命令入口
   - 含 `ascended` 路由
3. `hooks/hooks.json`
   - 自动识别用户纠错
   - 自动 / 手动升级到 Ascended Mode
   - 上下文压缩前 checkpoint
   - 会话恢复时 restore

### VSCode Copilot

VSCode 适配文件位于：

1. [vscode/copilot-instructions.md](./vscode/copilot-instructions.md)
2. [vscode/instructions/mistakebook.instructions.md](./vscode/instructions/mistakebook.instructions.md)
3. [vscode/prompts/mistakebook.prompt.md](./vscode/prompts/mistakebook.prompt.md)
4. [vscode/prompts/ascended.prompt.md](./vscode/prompts/ascended.prompt.md)

## 运行时存储

### 项目级目录

默认按宿主分别写入：

- Codex: `<project>/.codex/mistakebook/`
- Claude: `<project>/.claude/mistakebook/`
- VSCode: `<project>/.vscode/mistakebook/`
- Generic: `<project>/.mistakebook/`

### 全局级目录

默认按宿主分别写入：

- Codex: `~/.codex/mistakebook/`
- Claude: `~/.claude/mistakebook/`
- VSCode: `~/.vscode/mistakebook/`
- Generic: `~/.mistakebook/`

### 每个 store 的最小结构

```text
mistakebook/
├─ failures/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ memory/
│  ├─ PROJECT_MEMORY.md
│  └─ GLOBAL_MEMORY.md
└─ state/
   └─ catalog.json
```

## CLI 用法

本地脚本入口是 [scripts/mistakebook_cli.py](./scripts/mistakebook_cli.py)。

### 1. 初始化目录

```bash
python scripts/mistakebook_cli.py bootstrap --host codex --project-root .
```

可选参数：

- `--host codex|claude|vscode|generic`
- `--scope project|global|both`
- `--global-root <path>`

### 2. 归档案例

```bash
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-file payload.json
```

payload 至少需要包含：

- `title`
- `summary`
- `rules`
- `confirmedUnderstanding`
- `scopeDecision`
- `scopeReasoning`
- `correctionAttemptCount`
- `ascendedTriggered`
- `ascendedTriggerReason`
- `originalPrompt`
- `originalReply`
- `correctionFeedback`
- `finalReply`

推荐额外补充：

- `knowledgeSourcesReviewed`
- `whatWentWrong`
- `preventionChecklist`
- `projectMemoryMarkdown`
- `globalMemoryMarkdown`

### 3. 开关自动识别

```bash
python scripts/mistakebook_cli.py config --auto-detect on
python scripts/mistakebook_cli.py config --auto-detect off
```

配置写入：

- `~/.mistakebook/config.json`

## 推荐工作流

### 场景 1：自动进入纠错模式

1. 用户指出回答错误
2. Skill 自动触发
3. Agent 输出固定激活文案
4. Agent 按反馈修正
5. 每轮结尾固定追问
6. 用户明确确认完成
7. Agent 归档案例并刷新记忆

### 场景 2：手动启动错题集

1. 用户输入 `/mistakebook`
2. 进入核心 Skill
3. 开始纠错闭环
4. 完成后归档

### 场景 3：自动升级到神级模式

1. 用户已经让 Agent 改了两次或以上
2. 用户仍然明确表示“不对 / 还是错 / 没理解”
3. Agent 自动进入 Ascended Mode
4. Agent 输出固定神级回复语
5. 全面检索项目级 / 全局级知识
6. 解释前几次纠错为什么失败
7. 选择当前最有效的方法重新处理

### 场景 4：手动启动神级模式

1. 用户输入 `/ascended`
2. 或者用户说：`你需要根据你见过最有效的方法来处理这个问题`
3. Agent 输出神级模式固定回复语
4. 全面检索项目级 / 全局级知识
5. 解释前几次纠错为什么失败
6. 选择最有效的方法重新处理

### 场景 5：长对话 / 上下文压缩

1. `PreCompact` hook 把运行态写入 `~/.mistakebook/runtime-journal.md`
2. `SessionStart` hook 在会话恢复时提醒读取 checkpoint
3. Agent 恢复原来的纠错案例，而不是新开一条错题
4. 如果当时已经进入 Ascended Mode，也要一并恢复

## 触发回归测试

样例位于：

- [evals/trigger-prompts/should-trigger.txt](./evals/trigger-prompts/should-trigger.txt)
- [evals/trigger-prompts/should-trigger-ascended.txt](./evals/trigger-prompts/should-trigger-ascended.txt)
- [evals/trigger-prompts/should-not-trigger.txt](./evals/trigger-prompts/should-not-trigger.txt)

它们的作用是帮助你持续校验：

1. 哪些说法应该进入错题集模式
2. 哪些说法应该直接进入 Ascended 模式
3. 哪些说法不应该误触发

后续如果你继续扩展 matcher，建议优先先补 `evals/` 再改 hook / description。

## 已实现内容

当前仓库已经具备：

1. 通用核心 Skill 协议
2. Codex 精简版 Skill
3. Claude 风格 hooks 与命令路由
4. VSCode Copilot 指令与 prompt
5. 本地 CLI 归档工具
6. 项目级 / 全局级双层记忆目录约定
7. 触发词回归样例
8. Ascended 神级模式协议与手动入口

## 后续还可以继续增强的方向

这个版本已经能真实使用，但还有一些可继续迭代的方向：

1. 把 `consolidate` 做成真正可执行的记忆重写逻辑
2. 增加更完整的自动 scope 推断策略
3. 增加多轮纠错同 case 的版本演进机制
4. 增加对更多宿主的适配
5. 增加更自动化的 eval runner
6. 把 Ascended Mode 的知识检索过程进一步做成可验证的自动化流程

## 关于 `reference_code/`

`reference_code/` 只是本地参考材料，不属于这个 Skill 项目的正式发布内容。

因此仓库的 `.gitignore` 已经明确把它排除掉，避免把参考仓库一并提交进去。
