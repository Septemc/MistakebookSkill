# Installing Mistakebook Skill for Codex

通过 Codex 原生 `~/.codex/skills/` 自动发现安装“错题集 / 记事本 Skill”。

## 功能

- 自动识别”你这里错了 / 还没改对 / 我来纠正你”这类纠错场景
- 支持”写入记事本 / 记一下这个事项”这类长期事项记录场景
- 首次进入纠错模式时输出固定激活文案
- 在用户确认后，归档到项目级和全局级错题集或记事本
- 每次归档都刷新缓存式项目记忆和全局记忆
- 为 Codex 提供更适合输入框体验的 skill-chip 入口
- 所有 Agent 工具共享统一存储路径（`<project>/.mistakebook/` 和 `~/.mistakebook/`）

## 安装

### macOS / Linux

```bash
git clone <your-repo-url> ~/.codex/mistakebook
mkdir -p ~/.codex/skills ~/.codex/prompts

ln -s ~/.codex/mistakebook/codex/mistakebook ~/.codex/skills/mistakebook
ln -s ~/.codex/mistakebook/codex/ascended ~/.codex/skills/ascended
ln -s ~/.codex/mistakebook/codex/notebook ~/.codex/skills/notebook
ln -s ~/.codex/mistakebook/codex/scholar ~/.codex/skills/scholar

ln -s ~/.codex/mistakebook/commands/mistakebook.md ~/.codex/prompts/mistakebook.md
ln -s ~/.codex/mistakebook/commands/ascended.md ~/.codex/prompts/ascended.md
ln -s ~/.codex/mistakebook/commands/notebook.md ~/.codex/prompts/notebook.md
ln -s ~/.codex/mistakebook/commands/scholar.md ~/.codex/prompts/scholar.md
```

### Windows (PowerShell)

```powershell
git clone <your-repo-url> "$env:USERPROFILE\\.codex\\mistakebook"
New-Item -ItemType Directory -Force "$env:USERPROFILE\\.codex\\skills" | Out-Null
New-Item -ItemType Directory -Force "$env:USERPROFILE\\.codex\\prompts" | Out-Null

cmd /c mklink /J "$env:USERPROFILE\\.codex\\skills\\mistakebook" "$env:USERPROFILE\\.codex\\mistakebook\\codex\\mistakebook"
cmd /c mklink /J "$env:USERPROFILE\\.codex\\skills\\ascended" "$env:USERPROFILE\\.codex\\mistakebook\\codex\\ascended"
cmd /c mklink /J "$env:USERPROFILE\\.codex\\skills\\notebook" "$env:USERPROFILE\\.codex\\mistakebook\\codex\\notebook"
cmd /c mklink /J "$env:USERPROFILE\\.codex\\skills\\scholar" "$env:USERPROFILE\\.codex\\mistakebook\\codex\\scholar"

cmd /c mklink /H "$env:USERPROFILE\\.codex\\prompts\\mistakebook.md" "$env:USERPROFILE\\.codex\\mistakebook\\commands\\mistakebook.md"
cmd /c mklink /H "$env:USERPROFILE\\.codex\\prompts\\ascended.md" "$env:USERPROFILE\\.codex\\mistakebook\\commands\\ascended.md"
cmd /c mklink /H "$env:USERPROFILE\\.codex\\prompts\\notebook.md" "$env:USERPROFILE\\.codex\\mistakebook\\commands\\notebook.md"
cmd /c mklink /H "$env:USERPROFILE\\.codex\\prompts\\scholar.md" "$env:USERPROFILE\\.codex\\mistakebook\\commands\\scholar.md"
```

## 推荐入口

在 Codex 中优先使用这些 skill-chip 入口：

- `$mistakebook`
- `$ascended`
- `$notebook`
- `$scholar`

这样可以避免把长 prompt 正文直接展开到输入框里。

## 兼容入口

如果你已经习惯 `/prompts:*`，这些入口仍然保留：

- `/prompts:mistakebook`
- `/prompts:ascended`
- `/prompts:notebook`
- `/prompts:scholar`

## 使用与触发规则

- `$mistakebook`
  - Codex 默认主入口。先选成 skill chip，再正常提问。
  - 进入后，用户纠错语会触发 `mistake` 闭环，记事项语会触发 `note` 候选流程。
  - 同一个案例被否定两次以上，或用户明确要求最强方法时，会升级到 `Ascended Mode`。
- `$ascended`
  - 手动强制进入飞升模式。
  - 适合当前问题已经失败多轮，需要直接全面检索项目级 / 全局级知识后再处理。
- `$notebook`
  - 手动进入 `note` 流程。
  - 适合先整理长期事项，再决定是否归档到记事本。
- `$scholar`
  - 新任务答前预检入口。
  - 只在 `shouldInject = true` 时注入一行历史提醒；如果当前已经进入 `mistake`、`note` 或 `Ascended Mode`，不要再运行它。
- `/prompts:*`
  - 兼容入口，语义和对应 skill 一样，但会把 prompt 正文展开到输入框。
  - 如果你想要 `$pua` 那样的 chip 体验，应该用 `$mistakebook`、`$ascended`、`$notebook`、`$scholar`，不要用 `/prompts:*`。

## 验证

在 Codex 中输入：

- `$mistakebook`
- `$ascended`
- `$notebook`
- `$scholar`
- `/prompts:mistakebook`
- `/prompts:ascended`

如果 Skill 已加载，后续当你输入“你这里错了”“重新改”“还没纠正好”等内容时，它会切换到纠错闭环；如果你输入“写入记事本”“记一下这个事项”等内容时，它会进入长期事项记录流程；如果你输入 `/ascended` 或手动要求它按照“见过最有效的方法”来处理，它会升级到飞升模式。

## 快速归档

如果当前仓库里有 `scripts/mistakebook_cli.py`，推荐优先用 stdin 归档：

```bash
cat <<'EOF' | python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-stdin
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
EOF
```

`archive` 现在支持三选一：

1. `--payload-file`
2. `--payload`
3. `--payload-stdin`

## 存储路径（统一）

所有 Agent 工具（Codex、Claude Code、VSCode、通用）共享统一的存储路径：

- 项目级存储：`<project>/.mistakebook/`
- 全局级存储：`~/.mistakebook/`

每个 store 里至少有：

- `failures/`
- `notes/`
- `memory/`
- `state/`

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
