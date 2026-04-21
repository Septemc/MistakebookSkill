# Installing Mistakebook Skill for Codex

通过 Codex 原生 `~/.codex/skills/` 自动发现安装“错题集 / 记事本 Skill”。

## 功能

- 自动识别“你这里错了 / 还没改对 / 我来纠正你”这类纠错场景
- 支持“写入记事本 / 记一下这个事项”这类长期事项记录场景
- 首次进入纠错模式时输出固定激活文案
- 在用户确认后，归档到项目级和全局级错题集或记事本
- 每次归档都刷新缓存式项目记忆和全局记忆

## 安装

### macOS / Linux

```bash
git clone <your-repo-url> ~/.codex/mistakebook
mkdir -p ~/.codex/skills ~/.codex/prompts
ln -s ~/.codex/mistakebook/codex/mistakebook ~/.codex/skills/mistakebook
ln -s ~/.codex/mistakebook/commands/mistakebook.md ~/.codex/prompts/mistakebook.md
```

### Windows (PowerShell)

```powershell
git clone <your-repo-url> "$env:USERPROFILE\\.codex\\mistakebook"
New-Item -ItemType Directory -Force "$env:USERPROFILE\\.codex\\skills" | Out-Null
New-Item -ItemType Directory -Force "$env:USERPROFILE\\.codex\\prompts" | Out-Null
cmd /c mklink /J "$env:USERPROFILE\\.codex\\skills\\mistakebook" "$env:USERPROFILE\\.codex\\mistakebook\\codex\\mistakebook"
cmd /c mklink /H "$env:USERPROFILE\\.codex\\prompts\\mistakebook.md" "$env:USERPROFILE\\.codex\\mistakebook\\commands\\mistakebook.md"
```

## 验证

在 Codex 中输入：

- `$mistakebook`
- `/prompts:mistakebook`
- `/prompts:mistakebook note`
- `/ascended`
- `你需要根据你见过最有效的方法来处理这个问题`

如果 Skill 已加载，后续当你输入“你这里错了”“重新改”“还没纠正好”等内容时，它会切换到纠错闭环；如果你输入“写入记事本”“记一下这个事项”等内容时，它会进入长期事项记录流程；如果你输入 `/ascended` 或手动要求它按照“见过最有效的方法”来处理，它会升级到飞升模式。

## 目录

- 项目级存储：`<project>/.codex/mistakebook/`
- 全局级存储：`~/.codex/mistakebook/`

每个 store 里至少有：

- `failures/`
- `notes/`
- `memory/`
- `state/`

如果宿主受限于只能写 skill 目录，也可以把全局根显式指定为 `~/.codex/skills/mistakebook/.data/`。
