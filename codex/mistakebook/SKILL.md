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

### `mistake` 最小模板

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

### `note` 最小模板

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

### bash 示例

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

### PowerShell 示例

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

## 记忆原则

项目记忆和全局记忆是缓存，不是流水账。

默认策略：

1. 条目少时可以几乎全量保留
2. 达到阈值后按命中、检索、新旧程度筛选
3. 长期低命中内容暂时退出缓存
4. 详细条目永远保留在 `failures/` 和 `notes/`

## 禁止事项

1. 未经用户确认，禁止归档
2. 不要只记录“错在哪里”，也要记录“已经吃透什么”
3. 不要把项目私有细节原样塞进全局记忆
4. 不要把暂时遗忘理解成删除详细条目
## Scholar Preflight

鍦ㄦ柊鐨勬櫘閫氫换鍔″紑濮嬪墠锛屽鏋滃綋鍓嶄笉鍦ㄧ籂閿欓棴鐜垨 Ascended Mode 閲岋紝鍏堣繍琛岋細

```bash
python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<当前任务>"
```

鍙湁褰?`shouldInject = true` 鏃讹紝鎵嶅湪姝ｅ紡鍥炵瓟鍓嶈緭鍑轰竴琛屽巻鍙叉彁閱掋€傚鏋滆繘鍏ョ籂閿欓棴鐜垨 `ascended`锛屽氨鍋滄杩愯 `scholar`锛屼笉瑕佽瀛︿緵妯″紡鍜岄鍗囨ā寮忔姠鍚屼竴涓椂鏈恒€?

濡傛灉鐢ㄦ埛璇?`scholar off` / `scholar on`锛屽彲浠ュ湪褰撳墠浼氳瘽涓存椂鍏抽棴鎴栨仮澶嶉妫€銆傚鏋滅敤鎴疯姹傞暱鏈熷叧闂垨寮€鍚紝鎵ц锛?

```bash
python scripts/mistakebook_cli.py config --scholar off
python scripts/mistakebook_cli.py config --scholar on
```
