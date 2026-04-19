---
name: mistakebook
description: "识别用户进入纠错/返工/指出错误的场景，启动带人工确认的纠错闭环；在用户明确说“已完成、纠正好了、可以归档”后，把详细错题写入项目级和/或全局级错题集，并同步刷新精炼记忆。若同一个案例被用户否定两次以上，或用户说“你需要根据你见过最有效的方法来处理这个问题”或输入“/ascended”，自动升级到 Ascended 神级模式，全面检索项目级/全局级错题与记忆后再处理。匹配常见短语：'你这里错了'、'这不对'、'重新改'、'我来纠正你'、'你又犯同样的错'、'还没改对'、'没有吃透'、'我教你一遍'、'按我说的改'、'/mistakebook'、'/ascended'."
---

# 错题集 Skill

这个 Skill 负责把“用户正在纠正你”变成一个真正的闭环：

1. 识别纠错状态
2. 进入纠错模式
3. 持续根据用户反馈纠错
4. 等待用户明确确认“已经纠正完成”
5. 归档详细案例
6. 刷新项目级和全局级记忆

## 启动后先做什么

加载本 Skill 后，立刻阅读以下文件：

1. `references/activation-patterns.md`
2. `references/storage-and-scope.md`
3. `references/archive-schema.md`
4. `references/ascended-mode.md`

不要等“按需发现”再读，这四个文件共同定义了触发、升级、归档和记忆分层。

## 两句强制文案

### 进入纠错模式时

当你第一次明确判断“用户正在纠正我”时，必须先输出这句，逐字一致：

`【我发现这道题做错了，我接下来会进行纠错，并根据你的纠错信息，持续纠错直到完成，然后写入我的错题集】`

这句话只在**进入**纠错模式时展示一次。处于同一个纠错案例里时，不要每轮都重复。

### 每轮纠错结束时

只要当前案例还没有被用户明确确认“已完成”，你的回复结尾都必须追加这句，逐字一致：

`我当前有没有把问题吃透，有没有纠正错误，如果没有的话，麻烦你再教我一遍，好不好？（如果我已经完成了纠错，也请你告知我一声，我可以把错题写入我的错题集）`

如果用户已经明确确认“完成了 / 纠正好了 / 可以归档”，这句就不要再问，直接进入归档流程。

## 神级模式强制文案

当你进入 Ascended Mode 时，必须先输出这句，逐字一致：

`我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！`

这句只在真正进入 Ascended Mode 时展示一次。同一个 case 如果已经在神级模式中，不要重复刷屏。

## 状态机

把当前纠错流程看成下面 6 个状态：

1. `disabled`
   - 没有进入纠错模式
2. `armed`
   - 已经识别到用户正在纠错，本轮开始进入纠错流程
3. `pending_review`
   - 你已经给出纠正后的回答，等待用户告诉你“完成 / 未完成”
4. `followup_needed`
   - 用户认为还没纠正到位，继续根据追加反馈修正
5. `summarizing`
   - 用户明确说已经完成，开始整理归档 payload
6. `archived`
   - 已经把案例和记忆写入对应目录

除此之外，还要维护一个独立模式位：

1. `normal`
2. `ascended`

## 纠错循环协议

### 1. 何时视为进入纠错模式

满足任一条件就进入：

1. 用户明确说你错了、没改对、又犯同样错误
2. 用户开始逐条纠正你的表述、代码、方案或行为
3. 用户给出“按我说的改”“我来教你一遍”“重新做一版”的指令
4. 用户提到“错题集”“纠错模式”“归档这次错误”

详细触发样例看 `references/activation-patterns.md`。

### 2. 纠错模式下必须维护的运行态

至少持续维护这些信息，直到归档完成：

1. `case_id`
2. `host`
3. `project_root`
4. `original_prompt`
5. `original_reply`
6. `correction_feedback_chain`
7. `latest_fixed_reply`
8. `scope_guess`
9. `status`
10. `rejection_count`
11. `correction_attempt_count`
12. `ascended_mode`
13. `ascended_trigger_reason`
14. `knowledge_sources_reviewed`

如果发生上下文压缩，优先把这些信息 checkpoint 到 `~/.mistakebook/runtime-journal.md`。

### 3. 用户说“还没改对”时

你必须：

1. 把这次用户反馈并入同一个案例
2. 按反馈继续纠正，不要提前归档
3. 在本轮纠正结尾继续追加固定追问句
4. `rejection_count += 1`
5. `correction_attempt_count += 1`

### 3.1 自动升级到 Ascended Mode

如果同一个纠错案例已经被用户明确否定两次或以上，就不要再以“普通修补模式”继续处理，而要自动升级到 Ascended Mode。

自动升级条件：

1. `rejection_count >= 2`
2. 同一个 case 已经明显进入“改了两次以上还是错”的状态

一旦自动升级：

1. 先输出神级模式固定文案
2. 再全面检索项目级和全局级知识来源
3. 先分析为什么连续纠错仍失败
4. 再给出新的修正

### 3.2 手动进入 Ascended Mode

下面任一情况都必须立刻进入 Ascended Mode：

1. 用户说：`你需要根据你见过最有效的方法来处理这个问题`
2. 用户输入：`/ascended`

手动触发优先级高于自动判断。收到后直接进入神级模式，不需要等待下一轮。

### 3.3 Ascended Mode 下必须检索的知识源

进入神级模式后，必须尽量完整检索并使用这些来源：

1. 当前项目级错题集 `failures/`
2. 当前项目级记忆 `memory/PROJECT_MEMORY.md`
3. 当前全局级错题集 `failures/`
4. 当前全局级记忆 `memory/GLOBAL_MEMORY.md`
5. 当前仓库中与问题直接相关的真实文件、真实输出、真实文档
6. 当前 Skill 的规则文件与参考文档
7. 当前会话里已经累积的全部用户纠错链

不要只说“我会深度分析”，却不做真实检索。

### 3.4 Ascended Mode 的输出纪律

进入神级模式后，在给出新修正前，你至少需要做到：

1. 明确指出为什么前面两次或更多次纠错仍然失败
2. 明确说明你参考了哪些知识来源
3. 明确选出当前最有效的一种处理方案
4. 优先基于真实文件和真实输出，而不是基于印象修补

### 4. 用户说“已经完成”时

只有在用户明确确认后，才能归档。允许的明确信号包括：

1. “可以了”
2. “这次改对了”
3. “已经吃透了”
4. “可以写入错题集”
5. “归档吧”
6. “完成纠错”

一旦收到这类确认，立即进入归档流程，不再继续追问固定句。

## 项目级 vs 全局级

优先按照下面规则做判断：

1. `project`
   - 错误依赖当前仓库结构、业务语义、项目规则、项目路径、项目流程
2. `global`
   - 错误本质是通用工程习惯、通用沟通失误、通用验证缺失、通用推理偏差
3. `both`
   - 既有项目内具体案例价值，又能抽出稳定的跨项目通用规则

判断不清时，默认 `project`，但如果能清楚抽出一个稳定通用教训，再补一份 `global`。

更详细的判定和目录策略见 `references/storage-and-scope.md`。

## 归档流程

### 1. 先生成结构化 payload

使用 `references/archive-schema.md` 里的 JSON schema 生成 payload。至少包含：

1. `title`
2. `summary`
3. `rules`
4. `confirmedUnderstanding`
5. `scopeDecision`
6. `scopeReasoning`
7. `correctionAttemptCount`
8. `ascendedTriggered`
9. `ascendedTriggerReason`
10. `projectMemoryMarkdown`
11. `globalMemoryMarkdown`
12. `originalPrompt`
13. `originalReply`
14. `correctionFeedback`
15. `finalReply`

### 2. 优先使用脚本落盘

如果仓库内存在 `scripts/mistakebook_cli.py`，优先使用它：

1. 先执行 `bootstrap`
2. 再把 payload 写到临时 JSON 文件
3. 执行 `archive`

推荐命令形态：

```bash
python scripts/mistakebook_cli.py bootstrap --host codex --project-root .
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-file <temp-json>
```

如果当前宿主不是 Codex，把 `--host` 换成 `claude`、`vscode` 或 `generic`。

### 3. 如果脚本不存在

按 `references/storage-and-scope.md` 和 `references/archive-schema.md` 的格式手工写入：

1. `failures/INDEX.md`
2. 单条错题 Markdown
3. `memory/PROJECT_MEMORY.md`
4. `memory/GLOBAL_MEMORY.md`

### 4. 每次归档都要刷新记忆

项目记忆和全局记忆都必须满足：

1. 精简
2. 凝练
3. 真实
4. 可执行

不要把整段聊天原文复制进记忆。记忆应该只保留稳定规则、已吃透的点、以及下次必须先检查的高风险项。

### 5. 什么时候做“整理一遍”

如果出现下面任一条件，除了常规更新外，再做一次更彻底的 memory 重写：

1. 同主题错题累计 3 次以上
2. 某个 store 新增案例达到 5 条
3. 距上次 full rollup 已超过 14 天

full rollup 时，重新阅读最近相关案例，去重、合并、压缩，再重写记忆文件。

## 宿主与路径

默认目录：

1. Codex
   - 项目：`<project>/.codex/mistakebook/`
   - 全局：`~/.codex/mistakebook/`
2. Claude
   - 项目：`<project>/.claude/mistakebook/`
   - 全局：`~/.claude/mistakebook/`
3. VSCode
   - 项目：`<project>/.vscode/mistakebook/`
   - 全局：`~/.vscode/mistakebook/`
4. Generic
   - 项目：`<project>/.mistakebook/`
   - 全局：`~/.mistakebook/`

如果宿主只能写 skill/plugin 目录，可以把全局根定向到宿主目录里的 `.data` 或 `.mistakebook` 子目录。

## 容易犯错的地方

1. 不要把“用户在讨论 bug”误判成“用户在纠正你”
2. 不要在用户还没确认前提前归档
3. 不要只记录“错在哪里”，也要记录“现在已经理解对了什么”
4. 不要把项目细节原样塞进全局记忆；全局条目要做适度泛化
5. 不要让项目记忆变成流水账；记忆只保留高密度、可执行内容

## 交付时的最小确认

归档后，用 1 到 2 句话告诉用户：

1. 已归档到哪里
2. 这次更新了哪些记忆层

不要再继续追问固定句，也不要把完整 payload 原样抛给用户。
