---
name: mistakebook
description: "识别用户进入纠错、返工、指出错误、要求记录长期注意事项的场景，启动带人工确认的闭环；统一支持 `mistake` 与 `note` 两类条目，写入项目级和/或全局级错题集 / 记事本，并同步刷新缓存式项目记忆与全局记忆。若同一个案例被用户否定两次以上，或用户说“你需要根据你见过最有效的方法来处理这个问题”或输入“/ascended”，自动升级到飞升模式（Ascended Mode），全面检索项目级/全局级错题、记事本、记忆缓存和当前知识库后再处理。常见触发：'你这里错了'、'这不对'、'重新改'、'我来纠正你'、'还没改对'、'写入记事本'、'记一下这个事项'、'/mistakebook'、'/ascended'."
---

# 错题集 / 记事本 Skill

这个 Skill 不只负责“纠错归档”，还负责“主动事项沉淀”。

统一目标有四个：

1. 把用户纠错变成闭环
2. 把长期注意事项沉淀成记事本
3. 把项目记忆和全局记忆维护成缓存，而不是流水账
4. 在普通修补不够时，升级到飞升模式做全量检索和最强方案处理

## 启动后先做什么

加载本 Skill 后，立刻阅读以下文件：

1. `references/activation-patterns.md`
2. `references/storage-and-scope.md`
3. `references/archive-schema.md`
4. `references/ascended-mode.md`

不要等“按需发现”再读，这四个文件共同定义了触发、升级、归档、缓存和遗忘策略。

## 强制文案

### 进入纠错模式时

当你第一次明确判断“用户正在纠正我”时，必须先输出这句，逐字一致：

`<错题集.Skill>我接下来会进行纠错，并根据你的纠错信息，持续纠错直到完成，然后写入我的错题集。`

### 每轮纠错结束时

只要当前 `mistake` 案例还没有被用户明确确认完成，你的回复结尾都必须追加这句，逐字一致：

`我有没有吃透当前问题，是否成功纠正错误，如果没有的话，请你再教我一遍。（如果我已经完成了纠错，也请你告诉我一声，我可以把错题写入我的错题集）`

### 记事本追问句

只要当前回复里已经形成一个值得长期保留的主动事项，你的回复结尾都应该追加这句，逐字一致：

`如果这个事项值得长期注意，也可以告诉我“写入记事本”，我会把它归档到记事本并同步刷新记忆。`

### 飞升模式强制文案

当你进入 Ascended Mode 时，必须先输出这句，逐字一致：

`我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！`

## 条目类型

从现在开始，只维护两类归档条目：

1. `mistake`
   - 已经完成纠错、值得复盘的错误案例
2. `note`
   - 不一定是错误，但值得长期注意、主动记录的事项

## 状态机

把当前流程看成下面这些状态：

1. `disabled`
   - 当前没有进入闭环
2. `armed`
   - 已识别到纠错或记事需求
3. `pending_review`
   - 已给出当前修正或整理结果，等待用户确认
4. `followup_needed`
   - 用户要求继续修正或继续补充事项
5. `summarizing`
   - 用户明确确认，开始整理 payload
6. `archived`
   - 已经写入详细条目与缓存记忆

除此之外，还要维护：

1. `entry_type`
   - `mistake` 或 `note`
2. `mode`
   - `normal` 或 `ascended`

## 何时进入 mistake

满足任一条件就进入 `mistake`：

1. 用户明确说你错了、没改对、又犯同样错误
2. 用户开始逐条纠正你的表述、代码、方案或行为
3. 用户给出“按我说的改”“我来教你一遍”“重新做一版”的指令
4. 用户提到“错题集”“纠错模式”“归档这次错误”

## 何时进入 note

满足任一条件就进入 `note` 归档候选流程：

1. 用户明确说“写入记事本”
2. 用户说“记一下这个事项”
3. 用户明确指出“这不是错题，但要长期注意”
4. 你已经形成一个稳定、可执行、值得长期保留的注意事项

## 运行态

至少持续维护这些信息，直到归档完成：

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

如果发生上下文压缩，优先把这些信息 checkpoint 到 `~/.mistakebook/runtime-journal.md`。

## mistake 闭环

### 1. 进入

一旦确认是纠错场景：

1. 先输出激活句
2. 给出修正后的回答
3. 结尾追加固定纠错追问句
4. 如果这一轮还沉淀出一个长期有效事项，再追加记事本追问句

### 2. 用户说“还没改对”

你必须：

1. 把这次用户反馈并入同一个案例
2. 按反馈继续纠正，不要提前归档
3. 在本轮纠正结尾继续追加固定纠错追问句
4. `rejection_count += 1`
5. `correction_attempt_count += 1`

### 3. 自动升级到飞升模式

如果同一个 `mistake` 案例已经被用户明确否定两次或以上，就不要再以普通修补模式继续处理，而要自动升级到 Ascended Mode。

自动升级条件：

1. `rejection_count >= 2`
2. 同一个 case 已经明显进入“改了两次以上还是错”的状态

一旦自动升级：

1. 先输出飞升模式固定文案
2. 再全面检索项目级和全局级知识来源
3. 先分析为什么连续纠错仍失败
4. 再给出新的修正

## note 闭环

### 1. 进入

一旦确认是主动记录事项：

1. 先给出当前事项的整理结果
2. 明确说明为什么这条值得长期保留
3. 结尾追加记事本追问句

### 2. 未确认时

如果用户继续补充：

1. 把补充内容并入同一个 `note` 案例
2. 更新事项、行动项或边界说明
3. 不要提前归档

### 3. 完成信号

只有在用户明确确认后，才允许把当前事项归档为 `note`。

可视为显式确认的表达包括：

1. `写入记事本`
2. `记下来`
3. `长期保留这条`
4. `把这个事项存起来`
5. `这个以后都要注意`

## 手动进入飞升模式

下面任一情况都必须立刻进入 Ascended Mode：

1. 用户说：`你需要根据你见过最有效的方法来处理这个问题`
2. 用户输入：`/ascended`

手动触发优先级高于自动判断。收到后直接进入飞升模式，不需要等待下一轮。

## 飞升模式下必须检索的知识源

进入飞升模式后，必须尽量完整检索并使用这些来源：

1. 当前项目级错题集 `failures/`
2. 当前项目级记事本 `notes/`
3. 当前项目级记忆 `memory/PROJECT_MEMORY.md`
4. 当前项目级缓存状态 `state/memory_state.json`
5. 当前全局级错题集 `failures/`
6. 当前全局级记事本 `notes/`
7. 当前全局级记忆 `memory/GLOBAL_MEMORY.md`
8. 当前全局级缓存状态 `state/memory_state.json`
9. 当前仓库中与问题直接相关的真实文件、真实输出、真实文档
10. 当前 Skill 的规则文件与参考文档
11. 当前会话里已经累积的全部用户纠错链和事项链

不要只说“我会深度分析”，却不做真实检索。

## 飞升模式的输出纪律

进入飞升模式后，在给出新修正前，你至少需要做到：

1. 明确指出为什么前面几轮仍然失败
2. 明确说明你参考了哪些错题、记事本、记忆或真实文件
3. 明确选出当前最有效的一种处理方案
4. 优先基于真实文件和真实输出，而不是基于印象修补

## 归档流程

### 1. 先生成结构化 payload

使用 `references/archive-schema.md` 里的 schema 生成 payload。

至少要带上：

1. `entryType`
2. `title`
3. `summary`
4. `scopeDecision`
5. `scopeReasoning`
6. `rules`
7. `confirmedUnderstanding`

如果是 `mistake`，再补：

1. `originalPrompt`
2. `correctionFeedback`
3. `finalReply`

如果是 `note`，再补：

1. `noteReason`
2. `noteContent`
3. `noteActionItems`
4. `noteContext`

### 2. 优先使用脚本落盘

如果仓库内存在 `scripts/mistakebook_cli.py`，优先使用它：

```bash
python scripts/mistakebook_cli.py bootstrap --host codex --project-root .
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-file <temp-json>
```

### 3. 记录缓存命中

如果某条错题、记事本或记忆在后续被再次检索或再次证明有效，优先记录它的命中情况：

```bash
python scripts/mistakebook_cli.py touch --host codex --project-root . --scope both --case-id <case-id> --kind hit
```

### 4. 重写缓存记忆

如果条目已经开始变多，或者缓存需要遗忘整理，执行：

```bash
python scripts/mistakebook_cli.py consolidate --host codex --project-root . --scope both
```

### 5. 飞升模式导出上下文

如果你正在进入飞升模式，优先执行：

```bash
python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval
```

## 记忆不是流水账

项目记忆和全局记忆都属于缓存层，不是全文仓库。

它们必须满足：

1. 精简
2. 凝练
3. 真实
4. 可执行
5. 可遗忘

## 缓存与遗忘

默认策略：

1. 条目还少时，可以几乎全量保留
2. 达到阈值后，开始按 `hitCount`、`retrievalCount`、最近活跃时间和优先级筛选
3. 长期低命中、长期不再检索的内容，暂时退出缓存
4. 详细条目永远保留在 `failures/` 和 `notes/` 里

## 宿主与路径

默认目录：

1. 项目级
   - `failures/`
   - `notes/`
   - `memory/`
   - `state/`
2. 全局级
   - `failures/`
   - `notes/`
   - `memory/`
   - `state/`

如果宿主只能写 skill/plugin 目录，可以把全局根定向到宿主目录里的 `.data` 或 `.mistakebook` 子目录。

## 容易犯错的地方

1. 不要把“用户在讨论 bug”误判成“用户在纠正你”
2. 不要在用户还没确认前提前归档
3. 不要只记录“错在哪里”，也要记录“已经吃透了什么”
4. 不要让记忆变成流水账；记忆只保留高密度、可执行内容
5. 不要把“暂时遗忘”理解成“删除详细条目”
6. 不要进入飞升模式后只看缓存，不看详细错题和记事本
## Scholar Preflight

鍦ㄦ柊鐨勬櫘閫氫换鍔″紑濮嬪墠锛屽鏋滃綋鍓嶄笉鍦?`mistake` 绾犻敊闂幆銆?`note` 娴佺▼鎴?`ascended` 妯″紡閲岋紝鍏堣繍琛岃交閲忛妫€锛?

```bash
python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<当前任务>"
```

鎵ц瑙勫垯锛?

1. 鍙湁褰?`scholar` 杩斿洖 `shouldInject = true` 鏃讹紝鎵嶅湪姝ｅ紡鍥炵瓟鍓嶈緭鍑轰竴琛屽巻鍙叉彁閱?2. 濡傛灉杩斿洖 `shouldInject = false`锛屽繀椤婚潤榛橈紝涓嶈鎶?query 缁撴灉鍘熸牱灞曠ず缁欑敤鎴?3. 涓€鏃﹁繘鍏ョ籂閿欓棴鐜垨 Ascended Mode锛屽氨鍋滄杩愯 `scholar`
4. `scholar` 鐨勮亴璐ｆ槸鈥滃洖绛斿墠閬块敊鈥濓紝`ascended` 鐨勮亴璐ｆ槸鈥滃け璐ュ悗鍗囩骇澶勭疆鈥濓紝涓よ€呬笉鑳芥贩鍚堟垚鍚屼竴涓噸妯″紡
5. 濡傛灉鐢ㄦ埛璇?`scholar off` 或 `scholar on`锛屽彲浠ュ湪褰撳墠浼氳瘽涓存椂鍏抽棴鎴栨仮澶嶉妫€锛涘鏋滅敤鎴疯姹傞暱鏈熷叧闂垨寮€鍚紝鍐嶆墽琛岋細

```bash
python scripts/mistakebook_cli.py config --scholar off
python scripts/mistakebook_cli.py config --scholar on
```
