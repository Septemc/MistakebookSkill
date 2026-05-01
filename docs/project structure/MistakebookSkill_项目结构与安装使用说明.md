# Mistakebook Skill 项目结构与安装使用说明

> 说明
>
> 自 2026-04-21 起，本项目已经升级为“错题集 + 记事本 + 缓存式记忆 + 飞升模式全量检索”的统一模型。
>
> 当前行为协议、目录结构、CLI 能力和宿主入口请优先以仓库根目录的 `README.md`、`skills/mistakebook/SKILL.md` 以及 `skills/mistakebook/references/` 下的文档为准。
>
> 本文档仍可作为结构参考，但如果与上述文件有冲突，请以上述文件为准。

- 项目名称：Mistakebook Skill
- 作者：Septemc
- 文档日期：2026-04-20
- 文档目的：解释本仓库中正式 Skill 项目的目录结构、每一个正式文件的作用、实际安装链路与运行链路

## 1. 说明范围

本说明文档默认把仓库内容分成 4 类：

1. 正式发布文件
   - 这些文件共同组成可安装、可运行、可分发的错题集 Skill 项目。
2. 宿主适配文件
   - 这些文件不改变核心能力，但负责把同一套能力接到 Codex、Claude、VSCode 等宿主上。
3. 本地参考资料
   - 这些文件用于设计、对照、原理追溯，不属于正式发布面。
4. 运行时产物
   - 这些文件通常是执行脚本或测试时自动生成的，不属于源码主体。

为了避免阅读时混淆，后文中的“每一个文件说明”，默认针对正式 Skill 项目文件展开；`reference_code/`、`docs/错题集能力/` 和 `scripts/__pycache__/` 会单独说明其定位，但不把它们当成正式发布入口。

## 2. 项目树状结构图

下面这份树状结构图以“正式项目 + 需要理解的辅助目录”为主，已经把 `reference_code/` 这种大型参考仓库折叠处理，便于你抓主干。

```text
MistakebookSkill/
├─ .claude-plugin/
│  ├─ marketplace.json
│  └─ plugin.json
├─ .codex/
│  └─ INSTALL.md
├─ codex/
│  └─ mistakebook/
│     ├─ SKILL.md
│     └─ agents/
│        └─ openai.yaml
├─ commands/
│  ├─ ascended.md
│  └─ mistakebook.md
├─ docs/
│  ├─ project structure/
│  │  └─ MistakebookSkill_项目结构与安装使用说明.md
│  └─ 错题集能力/
│     └─ Storydex_错题集能力原理说明_2026-04-19.md
├─ evals/
│  └─ trigger-prompts/
│     ├─ should-not-trigger.txt
│     ├─ should-trigger-ascended.txt
│     └─ should-trigger.txt
├─ hooks/
│  ├─ ascended-trigger.sh
│  ├─ correction-trigger.sh
│  ├─ hooks.json
│  └─ session-restore.sh
├─ scripts/
│  ├─ mistakebook_cli.py
│  └─ __pycache__/
│     └─ mistakebook_cli.cpython-313.pyc
├─ skills/
│  └─ mistakebook/
│     ├─ agents/
│     │  └─ openai.yaml
│     ├─ references/
│     │  ├─ activation-patterns.md
│     │  ├─ archive-schema.md
│     │  ├─ ascended-mode.md
│     │  └─ storage-and-scope.md
│     └─ SKILL.md
├─ vscode/
│  ├─ copilot-instructions.md
│  ├─ instructions/
│  │  └─ mistakebook.instructions.md
│  └─ prompts/
│     ├─ ascended.prompt.md
│     └─ mistakebook.prompt.md
├─ .gitignore
├─ plugin.json
├─ README.md
└─ reference_code/
   └─ pua-main/   (本地参考仓库，不属于正式发布内容)
```

## 3. 项目架构总览

从职责划分上看，这个仓库可以理解成 6 层：

1. 能力内核层
   - `skills/mistakebook/`
   - 定义错题集的核心协议、触发条件、归档规则、记忆规则、Ascended Mode 规则。
2. 宿主最小适配层
   - `codex/mistakebook/`
   - 为 Codex 提供更短、更直接的 Skill 入口。
3. 手动命令层
   - `commands/`
   - 提供 `/mistakebook` 与 `/ascended` 这类显式入口。
4. 自动触发层
   - `hooks/`
   - 让 Claude 风格宿主在用户输入时自动识别纠错状态、自动升级飞升模式、自动恢复上下文。
5. 落盘与归档层
   - `scripts/mistakebook_cli.py`
   - 负责初始化项目级/全局级错题目录、写索引、写单条错题、刷新记忆。
6. 宿主文档与界面元数据层
   - `.claude-plugin/`、`.codex/`、`vscode/`、`plugin.json`
   - 负责让不同宿主知道“这个 Skill 是什么、怎么装、怎么显示、怎么启用”。

## 4. 每一个文件的作用说明

### 4.1 根目录文件

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `.gitignore` | 定义不提交到版本库的本地目录与运行产物 | 当前明确排除了 `reference_code/`、`docs/错题集能力/`、各宿主运行时落盘目录、Python 缓存等内容，避免把参考仓库和测试产物一并提交。 |
| `plugin.json` | 仓库级插件包元数据 | 说明项目名、版本、描述、作者、关键字。它更像整个仓库的“包身份证”，不是某个单独宿主的专属配置。 |
| `README.md` | 项目总览说明书 | 面向阅读者解释项目目标、能力边界、关键目录、运行时目录、CLI 用法、推荐工作流，是仓库的总入口文档。 |

### 4.2 `.claude-plugin/`

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `.claude-plugin/plugin.json` | Claude 风格宿主的单插件元数据 | 告诉 Claude 风格宿主：这个插件叫 `mistakebook`，版本是多少，主要能力是什么。它是 Claude 侧识别单个插件的入口描述文件。 |
| `.claude-plugin/marketplace.json` | Claude 风格宿主的插件市场描述文件 | 把当前仓库包装成一个 marketplace，名字是 `mistakebook-skills`，里面声明了一个插件 `mistakebook`。如果你通过 marketplace 方式接入，这个文件就是对外清单。 |

### 4.3 `.codex/`

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `.codex/INSTALL.md` | Codex 安装说明 | 说明如何把本仓库克隆到 `~/.codex/` 下、如何建立 `skills` 与 `prompts` 的链接、如何做基础验证，以及 Codex 默认的项目级与全局级存储目录。 |

### 4.4 `codex/mistakebook/`

这是 Codex 专用的精简 Skill 目录。它和 `skills/mistakebook/` 的关系是：

1. `skills/mistakebook/` 是完整规范版。
2. `codex/mistakebook/` 是给 Codex 快速加载的精简版入口。

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `codex/mistakebook/SKILL.md` | Codex 专用的错题集 Skill 主文件 | 负责让 Codex 在最短上下文里理解：什么时候进入纠错模式、必须输出哪两句固定文案、什么时候升级到 Ascended Mode、用户确认后如何归档。 |
| `codex/mistakebook/agents/openai.yaml` | Codex/UI 展示元数据 | 定义显示名、短描述、默认提示词，以及是否允许隐式触发。它更偏 UI 和发现层，不是具体业务逻辑本体。 |

### 4.5 `commands/`

`commands/` 的定位不是存规则，而是存“手动入口”。

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `commands/mistakebook.md` | 手动进入错题集总入口 | 支持无参数进入错题集，也支持 `on`、`off`、`status`、`consolidate`、`ascended` 等路由。它相当于人工手动切换和运维入口。 |
| `commands/ascended.md` | 手动进入飞升模式（Ascended Mode）的快捷入口 | 这个文件只做一件事：把当前问题强制拉入飞升模式，并要求宿主先输出固定飞升模式回复语，再执行全量检索和深度分析。 |

### 4.6 `docs/`

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `docs/project structure/MistakebookSkill_项目结构与安装使用说明.md` | 当前这份项目结构文档 | 用来解释整个仓库怎么组成、每个文件干什么、怎么安装、怎么使用、运行链路是什么。 |
| `docs/错题集能力/Storydex_错题集能力原理说明_2026-04-19.md` | 原理来源文档 | 这是从 Storydex 抽取出来的错题集能力原理说明，主要提供设计思想、状态机、归档最小模型、回注逻辑来源。它更像设计依据，而不是直接部署文件。 |

### 4.7 `evals/trigger-prompts/`

这组文件的职责非常明确：做“触发回归样例”。

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `evals/trigger-prompts/should-trigger.txt` | 普通纠错触发样例集 | 收录“你这里错了”“重新改”“按我说的改”等应该进入错题集纠错闭环的表达。改 matcher 时应先看它。 |
| `evals/trigger-prompts/should-trigger-ascended.txt` | 飞升模式触发样例集 | 收录应该直接或很快进入 Ascended Mode 的表达，例如 `/ascended`、用户明确要求“按最有效的方法处理”。 |
| `evals/trigger-prompts/should-not-trigger.txt` | 误触发防线样例集 | 收录“程序报错了”“继续实现功能”“解释代码”等不应自动进入错题集闭环的表达，用来防止 matcher 过宽。 |

### 4.8 `hooks/`

这一层主要给 Claude 风格宿主使用。

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `hooks/hooks.json` | Claude 风格 Hook 注册表 | 把不同事件和不同脚本关联起来。这里定义了 `UserPromptSubmit`、`PreCompact`、`SessionStart` 三大事件分别做什么。 |
| `hooks/correction-trigger.sh` | 纠错模式自动触发脚本 | 当用户输入命中纠错 matcher 时，向宿主注入一段高优先级提示，强制要求激活错题集 Skill、输出固定激活句、维护 rejection 计数、必要时升级飞升模式。 |
| `hooks/ascended-trigger.sh` | 飞升模式自动触发脚本 | 当用户输入命中飞升模式 matcher 时，向宿主注入一段高优先级提示，要求立即进入 Ascended Mode、检索所有知识源、解释前几次纠错失败原因。 |
| `hooks/session-restore.sh` | 压缩后会话恢复脚本 | 在会话恢复时检查 `~/.mistakebook/runtime-journal.md` 是否存在且足够新，如果有，就提醒宿主继续同一个 case，而不是新开一个纠错案例。 |

#### `hooks/hooks.json` 的实际事件职责

1. `UserPromptSubmit`
   - 识别用户输入是不是在纠正 Agent。
   - 识别用户是否在显式触发 `/ascended`。
2. `PreCompact`
   - 在上下文压缩之前，要求宿主先把当前纠错状态写入 `~/.mistakebook/runtime-journal.md`。
3. `SessionStart`
   - 在新会话开始、resume、compact 恢复时尝试提醒读取 runtime journal。

### 4.9 `scripts/`

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `scripts/mistakebook_cli.py` | 本地错题集 CLI 主脚本 | 是整个项目里唯一真正执行“目录初始化、案例归档、记忆刷新、配置开关”的脚本入口。 |
| `scripts/__pycache__/mistakebook_cli.cpython-313.pyc` | Python 运行时缓存文件 | 这是解释器执行脚本后自动生成的字节码缓存，不属于源码设计本体，可以删除，也不应作为安装入口理解。 |

#### `scripts/mistakebook_cli.py` 内部能力拆分

这个脚本主要提供 3 个子命令：

1. `bootstrap`
   - 初始化项目级与全局级存储目录。
   - 自动创建 `failures/`、`memory/`、`state/` 与初始模板文件。
2. `archive`
   - 读取归档 payload。
   - 根据 `scopeDecision` 决定写入项目级、全局级或两者。
   - 生成单条错题 Markdown。
   - 更新 `INDEX.md` 与 `catalog.json`。
   - 刷新 `PROJECT_MEMORY.md` / `GLOBAL_MEMORY.md`。
3. `config`
   - 打开或关闭自动识别开关。
   - 把结果写入 `~/.mistakebook/config.json`。

#### `scripts/mistakebook_cli.py` 维护的目录约定

所有 Agent 工具共享统一的存储路径：

1. 项目级默认根目录：`.mistakebook`
2. 全局级默认根目录：`~/.mistakebook`

旧版路径（已废弃，会自动迁移到统一路径）：
- `.codex/mistakebook`、`.claude/mistakebook`、`.vscode/mistakebook`
- `~/.codex/mistakebook`、`~/.claude/mistakebook`、`~/.vscode/mistakebook`

### 4.10 `skills/mistakebook/`

这一层是整个项目最核心的能力定义层。

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `skills/mistakebook/SKILL.md` | 通用核心 Skill 主文件 | 规定触发条件、固定激活句、固定追问句、固定飞升模式回复语、状态机、归档条件、scope 判断、周期性 rollup 规则，是整个项目的最高级行为协议。 |
| `skills/mistakebook/agents/openai.yaml` | 通用 Skill 的 UI 元数据 | 决定技能显示名、短描述、默认引导提示词，以及是否支持隐式触发。 |
| `skills/mistakebook/references/activation-patterns.md` | 触发样式参考 | 说明哪些表达该触发错题集，哪些不该触发，哪些 follow-up 仍算同一个 case。 |
| `skills/mistakebook/references/archive-schema.md` | 归档结构参考 | 定义归档 JSON payload、单条 Markdown 结构、项目记忆/全局记忆模板以及写法原则。 |
| `skills/mistakebook/references/ascended-mode.md` | 飞升模式参考 | 定义 Ascended Mode 的含义、自动/手动触发条件、进入后必须检索的来源与最低输出要求。 |
| `skills/mistakebook/references/storage-and-scope.md` | 存储与作用域参考 | 规定项目级/全局级目录布局、`project/global/both` 的判断标准、记忆文件的写法边界。 |

#### `skills/mistakebook/SKILL.md` 为什么是核心文件

因为它同时定义了 5 件最重要的事：

1. 何时算“用户正在纠正我”。
2. 进入后必须说什么。
3. 用户没确认前必须一直追问什么。
4. 改了两次还不对时必须如何升级。
5. 完成后如何归档、写入错题和记忆。

如果你只读一个文件来理解本项目，优先读它。

### 4.11 `vscode/`

这一层是给 VSCode Copilot 或相似编辑器环境的适配层。

| 文件 | 作用 | 说明 |
| --- | --- | --- |
| `vscode/copilot-instructions.md` | VSCode 侧总说明 | 用更适合 Copilot 指令体系的方式浓缩错题集规则，告诉编辑器何时接管纠错流程。 |
| `vscode/instructions/mistakebook.instructions.md` | VSCode 侧详细指令文件 | 进一步细化触发样例、完成样例、Ascended Mode 规则、目录约定和最低归档内容。 |
| `vscode/prompts/mistakebook.prompt.md` | VSCode 侧手动启动错题集 Prompt | 当用户显式调用这个 prompt 时，它会要求宿主进入错题集闭环。 |
| `vscode/prompts/ascended.prompt.md` | VSCode 侧手动启动飞升模式 Prompt | 当用户显式调用这个 prompt 时，它会要求宿主立刻进入 Ascended Mode。 |

### 4.12 `reference_code/`

| 路径 | 作用 | 说明 |
| --- | --- | --- |
| `reference_code/pua-main/` | 本地结构参考仓库 | 这个目录用于参考多宿主 Skill/Plugin 的分发格式和组织方式，不是 Mistakebook Skill 的正式组成部分。`.gitignore` 已经明确将其排除。 |

## 5. 正式发布面与非发布面的边界

为了后续安装、分发、排障不混乱，建议你这样理解仓库边界：

### 5.1 正式发布面

这些目录和文件属于真正需要关心的安装面：

1. `skills/mistakebook/`
2. `codex/mistakebook/`
3. `commands/`
4. `hooks/`
5. `scripts/mistakebook_cli.py`
6. `.claude-plugin/`
7. `.codex/INSTALL.md`
8. `vscode/`
9. `plugin.json`
10. `README.md`

### 5.2 参考面

这些内容用于帮助设计和理解，但不属于正式分发：

1. `reference_code/pua-main/`
2. `docs/错题集能力/Storydex_错题集能力原理说明_2026-04-19.md`

### 5.3 运行时产物

这些内容是执行过程中可能产生的本地数据：

1. `scripts/__pycache__/`
2. `<project>/.mistakebook/`
3. `~/.mistakebook/`

## 6. Claude 的实际安装过程

下面这部分按“当前仓库设计意图 + 真实文件结构”来说明。

### 6.1 安装前提

如果你要在 Claude 风格宿主中安装本项目，至少要满足：

1. 宿主支持从插件市场或本地 marketplace 读取插件清单。
2. 宿主支持 `commands/` 和 `hooks/` 这类插件附带目录。
3. Windows 环境下要能执行 `bash`，因为 `hooks/hooks.json` 中调用的是：
   - `bash ${CLAUDE_PLUGIN_ROOT}/hooks/correction-trigger.sh`
   - `bash ${CLAUDE_PLUGIN_ROOT}/hooks/ascended-trigger.sh`
   - `bash ${CLAUDE_PLUGIN_ROOT}/hooks/session-restore.sh`

如果是 Windows，建议准备 Git Bash，并在 Claude 的环境变量里配置：

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "F:\\Program Files\\Git\\bin\\bash.exe"
  }
}
```

### 6.2 仓库准备

先把本仓库放到一个固定路径，例如：

```powershell
git clone <your-repo-url> "C:\Users\<用户名>\mistakebook-skill"
```

### 6.3 在 Claude 设置里登记 marketplace

在 `C:\Users\<用户名>\.claude\settings.json` 里，至少要保证两件事：

1. `extraKnownMarketplaces` 中有当前仓库来源。
2. `enabledPlugins` 中打开 `mistakebook@mistakebook-skills`。

一个最小可用示例可以写成：

```json
{
  "env": {
    "CLAUDE_CODE_GIT_BASH_PATH": "F:\\Program Files\\Git\\bin\\bash.exe",
    "USE_BUILTIN_RIPGREP": "0"
  },
  "enabledPlugins": {
    "mistakebook@mistakebook-skills": true
  },
  "extraKnownMarketplaces": {
    "mistakebook-skills": {
      "source": {
        "source": "git",
        "url": "<your-repo-url>"
      }
    }
  }
}
```

### 6.4 Claude 侧实际会读取哪些文件

Claude 风格宿主真正会关心的文件链路是：

1. `.claude-plugin/marketplace.json`
   - 先知道“市场名叫 `mistakebook-skills`，里面有一个插件 `mistakebook`”。
2. `.claude-plugin/plugin.json`
   - 再知道这个单插件的描述与关键词。
3. `commands/mistakebook.md`
   - 让用户可以手动启动错题集。
4. `commands/ascended.md`
   - 让用户可以手动启动飞升模式。
5. `hooks/hooks.json`
   - 让宿主在用户输入时自动匹配纠错关键词或神级触发关键词。
6. `hooks/*.sh`
   - 当命中 matcher 时注入强约束提示。
7. `skills/mistakebook/SKILL.md`
   - 被真正加载后，开始接管纠错协议本体。
8. `scripts/mistakebook_cli.py`
   - 在需要落盘时执行初始化、归档、记忆刷新。

### 6.5 Claude 侧的触发方式

实际使用时有 3 条入口：

1. 自动入口
   - 用户说“你这里错了”“还没改对”“按我说的改”等。
   - `hooks/hooks.json` 会匹配，然后调用 `correction-trigger.sh`。
2. 手动错题集入口
   - 用户输入 `/mistakebook` 或等价宿主命令。
   - `commands/mistakebook.md` 负责路由到核心 Skill。
3. 手动神级入口
   - 用户输入 `/ascended`，或者明确说“你需要根据你见过最有效的方法来处理这个问题”。
   - `ascended-trigger.sh` 或 `commands/ascended.md` 会把流程拉入飞升模式。

### 6.6 Claude 侧运行后会把数据写到哪里

所有 Agent 工具现在共享统一的存储路径：

1. 项目级目录
   - `<project>/.mistakebook/`
2. 全局级目录
   - `~/.mistakebook/`
3. 配置目录
   - `~/.mistakebook/config.json`
4. 会话恢复 journal
   - `~/.mistakebook/runtime-journal.md`

### 6.7 Claude 侧常见坑点

1. `settings.json` 必须是合法 JSON
   - 不能有尾逗号。
   - 这是最常见的安装失败原因之一。
2. Windows 下必须能执行 `bash`
   - 否则 `hooks/*.sh` 根本跑不起来。
3. Claude hooks 还依赖 `python3`
   - `correction-trigger.sh` 会用 `python3` 读取 `~/.mistakebook/config.json`。
   - 如果环境里只有 `python` 没有 `python3`，自动识别开关可能会读不到，行为会退回默认开启。
4. 仅仅启用 plugin 还不够
   - 还必须让 marketplace 和 plugin id 对应得上，也就是 `mistakebook@mistakebook-skills`。
5. 如果宿主没有实际加载 `hooks/`
   - 那自动识别纠错将失效，但手动 `/mistakebook` 仍然可以作为兜底入口。
6. `runtime-journal.md` 只恢复最近 24 小时内容
   - 超过 24 小时后，`session-restore.sh` 会静默退出。
   - 这意味着跨天继续同一 case 时，恢复能力可能不再生效。

## 7. Codex 的实际安装过程

Codex 的安装逻辑相对更直接，因为仓库已经给出了明确的 `.codex/INSTALL.md`。

### 7.1 安装目标

Codex 侧的目标是让 2 类内容被发现：

1. Skill 本体
   - `codex/mistakebook/`
2. Prompt/命令入口
   - `commands/mistakebook.md`

### 7.2 推荐安装目录

按照仓库说明，建议把整个仓库放在：

```text
~/.codex/mistakebook
```

Windows 下等价于：

```text
C:\Users\<用户名>\.codex\mistakebook
```

### 7.3 安装步骤

#### macOS / Linux

```bash
git clone <your-repo-url> ~/.codex/mistakebook
mkdir -p ~/.codex/skills ~/.codex/prompts
ln -s ~/.codex/mistakebook/codex/mistakebook ~/.codex/skills/mistakebook
ln -s ~/.codex/mistakebook/commands/mistakebook.md ~/.codex/prompts/mistakebook.md
```

#### Windows PowerShell

```powershell
git clone <your-repo-url> "$env:USERPROFILE\.codex\mistakebook"
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\prompts" | Out-Null
cmd /c mklink /J "$env:USERPROFILE\.codex\skills\mistakebook" "$env:USERPROFILE\.codex\mistakebook\codex\mistakebook"
cmd /c mklink /H "$env:USERPROFILE\.codex\prompts\mistakebook.md" "$env:USERPROFILE\.codex\mistakebook\commands\mistakebook.md"
```

### 7.4 Codex 侧实际会读取哪些文件

Codex 的主读取链路通常是：

1. `~/.codex/skills/mistakebook/SKILL.md`
   - 实际上链接到 `codex/mistakebook/SKILL.md`。
2. `~/.codex/skills/mistakebook/agents/openai.yaml`
   - 实际上链接到 `codex/mistakebook/agents/openai.yaml`。
3. `~/.codex/prompts/mistakebook.md`
   - 实际上链接到 `commands/mistakebook.md`。
4. 如果执行归档
   - 会调用仓库中的 `scripts/mistakebook_cli.py`。

### 7.5 Codex 侧触发方式

你可以用 4 类方式触发：

1. 自动触发
   - 通过 Skill description 匹配“你这里错了”“还没改对”“我来纠正你”等自然语言。
2. 手动启动错题集
   - `$mistakebook`
   - `/prompts:mistakebook`
3. 手动升级到飞升模式
   - 直接说：`你需要根据你见过最有效的方法来处理这个问题`
4. 通过错题集命令参数升级
   - `mistakebook ascended`
   - 因为 `commands/mistakebook.md` 内部已经支持 `ascended` 路由

### 7.6 Codex 侧运行后会把数据写到哪里

所有 Agent 工具共享统一的存储路径：

1. 项目级目录
   - `<project>/.mistakebook/`
2. 全局级目录
   - `~/.mistakebook/`
3. 通用配置
   - `~/.mistakebook/config.json`

### 7.7 Codex 侧验证方式

安装完后，可以按下面顺序验证：

1. 输入 `$mistakebook`
   - 看 Codex 是否能识别并加载错题集 Skill。
2. 输入一条纠错句
   - 例如：`你这里错了，重新改一版`
   - 看是否输出固定激活句。
3. 连续否定两次
   - 看是否自动进入 Ascended Mode。
4. 明确说“可以归档了”
   - 看是否开始走归档总结与写盘流程。

### 7.8 Codex 侧常见坑点

1. Windows 下的 `mklink /H` 只能创建同卷文件硬链接
   - 如果仓库目录和 `C:\Users\<用户名>\.codex\prompts` 不在同一个磁盘卷，硬链接可能失败。
   - 这种情况下更稳妥的做法是改用复制文件，或者换成同卷目录。
2. 需要有创建链接的权限
   - 某些 Windows 环境下，创建目录联接或硬链接需要管理员权限或开发者模式。
3. Codex 侧没有额外的 shell hooks
   - 自动触发主要依赖 Skill 描述和宿主原生发现机制。
   - 所以它不像 Claude 那样有独立的 `UserPromptSubmit` 拦截层。
4. `status`、`consolidate`、`archive` 的实际落地最终都依赖 `scripts/mistakebook_cli.py`
   - 也就是说，命令层负责“路由”，真正执行能力还是脚本层。

## 8. 运行闭环的真实执行过程

这一节是“从用户输入到落盘”的完整链路。

### 8.1 普通纠错闭环

1. 用户指出 Agent 错误
   - 例如：`你这里错了`
2. 宿主或 Skill 识别为纠错场景
3. Agent 输出固定激活句
4. Agent 按用户纠错信息重新修正
5. 回复结尾追加固定追问句
6. 如果用户仍不满意
   - 继续并入同一个 case
   - `rejection_count += 1`
7. 如果用户明确说“可以了”
   - 进入归档
8. 归档后写入：
   - `failures/INDEX.md`
   - 单条失败案例 Markdown
   - `memory/PROJECT_MEMORY.md`
   - `memory/GLOBAL_MEMORY.md`
   - `state/catalog.json`

### 8.2 Ascended Mode 闭环

1. 同一个 case 被否定两次以上
   - 或用户显式输入 `/ascended`
   - 或用户说“你需要根据你见过最有效的方法来处理这个问题”
2. Agent 先输出固定飞升模式回复语
3. Agent 检索：
   - 项目级错题
   - 项目级记忆
   - 全局级错题
   - 全局级记忆
   - 当前仓库真实文件
   - 当前 case 的纠错链
4. Agent 先解释为什么前几轮纠错仍失败
5. Agent 选一个当前最有效的方案重新处理
6. 用户未确认完成前
   - 仍然要保留在纠错闭环里
   - 仍然要继续固定追问句
7. 用户确认后
   - 再统一归档

### 8.3 上下文压缩与会话恢复

如果会话过长，当前项目还考虑了“中断后如何不断档”：

1. `PreCompact`
   - 把当前纠错状态写入 `~/.mistakebook/runtime-journal.md`
2. `SessionStart`
   - 检查这个 journal 是否存在且是否足够新
3. 如果存在
   - 提醒宿主恢复原来的 case 状态，而不是创建新 case

这说明本项目不只是“会纠错”，而是在设计上考虑了长会话、压缩、恢复这类真实使用场景。

## 9. 实际安装后，你应该如何使用

### 9.1 Claude 的使用习惯

更推荐：

1. 平时依赖自动识别
   - 直接说“你这里错了”“按我说的改”。
2. 当你想强制进入闭环时
   - 手动输入 `/mistakebook`。
3. 当你发现它已经改了两轮还不对时
   - 直接输入 `/ascended`
   - 或直接说“你需要根据你见过最有效的方法来处理这个问题”。

### 9.2 Codex 的使用习惯

更推荐：

1. 用 `$mistakebook` 或 `/prompts:mistakebook` 明确接管本次纠错。
2. 如果它还在浅层修补
   - 用自然语言触发飞升模式。
3. 完成后明确告诉它：
   - `可以了`
   - `归档吧`
   - `写入错题集`

### 9.3 用户在使用时最重要的一个原则

无论是 Claude 还是 Codex，这个项目都强调同一件事：

`只有用户明确确认“纠错完成”之后，Agent 才允许把内容写入错题集。`

这是整个 Skill 最核心的质量闸门。

## 10. 推荐阅读顺序

如果你是第一次接手这个项目，建议按下面顺序读：

1. `README.md`
   - 先知道项目做什么。
2. `skills/mistakebook/SKILL.md`
   - 再理解核心协议。
3. `skills/mistakebook/references/*.md`
   - 把触发、归档、作用域、飞升模式补齐。
4. `scripts/mistakebook_cli.py`
   - 理解真实落盘方式。
5. `commands/*.md`
   - 理解手动入口。
6. `hooks/*`
   - 理解自动触发与会话恢复。
7. `.codex/INSTALL.md` 与 `.claude-plugin/*`
   - 最后理解多宿主安装与接入。

## 11. 一句话总结整个项目

如果只用一句话概括本仓库，可以写成：

`Mistakebook Skill 是一个把“用户纠错”转化为“持续纠错闭环 + 项目级/全局级案例归档 + 精炼记忆刷新 + 多次失败后自动升级飞升模式”的多宿主 Skill 项目。`
