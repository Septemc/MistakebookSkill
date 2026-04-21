---
agent: 'agent'
description: "激活错题集 / 记事本的飞升模式（Ascended Mode），全面检索项目/全局知识后再处理当前问题"
---

# Ascended Mode

立刻进入闭环的飞升模式，并执行下面的流程：

1. 先输出：
   `我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！`
2. 全面检索项目级错题集、项目级记事本、项目级记忆、项目级缓存状态
3. 全面检索全局级错题集、全局级记事本、全局级记忆、全局级缓存状态
4. 核对当前问题相关的真实文件、真实输出、真实文档
5. 如果仓库里存在 `scripts/mistakebook_cli.py`，优先执行：
   `python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval`
6. 解释为什么之前的处理仍然失败
7. 基于你见过最有效的方法重新处理当前问题
8. 如果我还没有确认完成，继续保持在闭环中，并按需要询问是否写入错题集或记事本
