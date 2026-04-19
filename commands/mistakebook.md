---
description: "错题集 Skill。/mistakebook [on|off|status|consolidate|ascended|任务描述]。识别用户纠错状态、进入纠错闭环、完成后归档到项目/全局错题集并刷新记忆；当用户反复纠正仍未完成时，或用户要求按最有效方法处理时，升级到 Ascended 神级模式。"
argument-hint: "[on|off|status|consolidate|ascended]"
---

根据参数执行以下路由：

## 参数路由

- **无参数** 或任意任务描述
  - 加载 `mistakebook` 核心 skill，进入错题集模式
- **on**
  - 如果存在 `scripts/mistakebook_cli.py`，执行：
    - `python scripts/mistakebook_cli.py config --auto-detect on`
  - 输出确认：`> [Mistakebook ON] 已开启自动识别纠错场景。`
- **off**
  - 如果存在 `scripts/mistakebook_cli.py`，执行：
    - `python scripts/mistakebook_cli.py config --auto-detect off`
  - 输出确认：`> [Mistakebook OFF] 已关闭自动识别纠错场景。`
- **status**
  - 读取 `~/.mistakebook/config.json` 与 `~/.mistakebook/runtime-journal.md`，汇报当前自动识别配置与最近 checkpoint
- **consolidate**
  - 读取当前项目和全局错题索引，重写项目记忆和全局记忆
- **ascended**
  - 立刻进入 Ascended 神级模式
  - 先输出固定神级回复语
  - 全面检索项目级 / 全局级错题与记忆后，再处理当前问题

## 执行规则

1. 当路由到核心 skill 时，严格遵循 `mistakebook` 的激活句、固定追问句、归档流程和记忆刷新规则
2. 用户没有明确确认“纠错完成”前，禁止归档
3. `consolidate` 不是简单追加条目，而是重读相关案例后做去重、合并和压缩
4. `ascended` 不是普通继续纠错，而是显式要求你调用当前已知最有效的方法，全面检索项目级 / 全局级知识来源后再给出方案
