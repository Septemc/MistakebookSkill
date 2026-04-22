---
description: "错题集 / 记事本 Skill。/mistakebook [on|off|status|consolidate|ascended|note|任务描述]。识别用户纠错状态或主动记录事项，统一归档到项目/全局错题集与记事本，并刷新缓存式记忆；当普通修补不够时，升级到飞升模式（Ascended Mode）。"
argument-hint: "[on|off|status|consolidate|ascended|note|scholar-on|scholar-off|scholar-status]"
---

根据参数执行以下路由：

## 参数路由

- **无参数** 或任意任务描述
  - 加载 `mistakebook` 核心 skill，进入统一闭环
- **note**
  - 加载 `mistakebook` 核心 skill，按 `note` 条目模式处理当前事项
  - 先整理当前长期注意事项，再在结尾询问是否写入记事本
- **on**
  - 如果存在 `scripts/mistakebook_cli.py`，执行：
    - `python scripts/mistakebook_cli.py config --auto-detect on`
  - 输出确认：`> [Mistakebook ON] 已开启自动识别纠错 / 记事项景。`
- **off**
  - 如果存在 `scripts/mistakebook_cli.py`，执行：
    - `python scripts/mistakebook_cli.py config --auto-detect off`
  - 输出确认：`> [Mistakebook OFF] 已关闭自动识别纠错 / 记事项景。`
- **status**
  - 如果存在 `scripts/mistakebook_cli.py`，执行：
    - `python scripts/mistakebook_cli.py status --host codex --project-root . --scope both`
- **scholar-on**
  - 如果存在 `scripts/mistakebook_cli.py`，执行：
    - `python scripts/mistakebook_cli.py config --scholar on`
  - 输出确认：`> [Scholar ON] 已开启学霸模式预检。`
- **scholar-off**
  - 如果存在 `scripts/mistakebook_cli.py`，执行：
    - `python scripts/mistakebook_cli.py config --scholar off`
  - 输出确认：`> [Scholar OFF] 已关闭学霸模式预检。`
- **scholar-status**
  - 如果存在 `scripts/mistakebook_cli.py`，执行：
    - `python scripts/mistakebook_cli.py status --host codex --project-root . --scope both`
- **consolidate**
  - 如果存在 `scripts/mistakebook_cli.py`，执行：
    - `python scripts/mistakebook_cli.py consolidate --host codex --project-root . --scope both`
  - 重读当前项目和全局的错题、记事本、命中数据，重写项目记忆和全局记忆
- **ascended**
  - 立刻进入飞升模式（Ascended Mode）
  - 先输出固定飞升模式回复语
  - 全面检索项目级 / 全局级错题、记事本、记忆缓存和当前知识库后，再处理当前问题

## 执行规则

1. 当路由到核心 skill 时，严格遵循 `mistakebook` 的激活句、固定纠错追问句、记事本追问句、归档流程和记忆刷新规则
2. 用户没有明确确认前，禁止提前把当前案例归档为 `mistake` 或 `note`
3. `consolidate` 不是简单追加条目，而是重读相关条目后做去重、合并、压缩和暂时遗忘
4. `ascended` 不是普通继续修补，而是显式要求你调用当前已知最有效的方法，全面检索项目级 / 全局级知识来源后再给出方案
5. 对于新的普通任务，如果当前不在纠错闭环、`note` 流程或 `ascended` 流程里，且学霸模式未被关闭，先执行：
   `python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<当前任务>"`
6. 只有当 `scholar` 返回 `shouldInject = true` 时，才允许在正式回答前输出一行历史提醒；否则保持静默
7. 一旦进入纠错闭环或 Ascended Mode，就停止运行 `scholar`，不要让学霸模式和飞升模式争抢同一个时机
