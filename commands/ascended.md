---
description: "进入错题集 / 记事本 Skill 的飞升模式（Ascended Mode）。触发语：/ascended，或“你需要根据你见过最有效的方法来处理这个问题”。"
---

立刻进入 `mistakebook` 的飞升模式（Ascended Mode），并严格执行以下步骤：

1. 先输出固定回复语：
   `我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！`
2. 全面检索项目级错题集、项目级记事本、项目级记忆、项目级缓存状态
3. 全面检索全局级错题集、全局级记事本、全局级记忆、全局级缓存状态
4. 核对当前仓库中与问题直接相关的真实文件、真实输出、真实文档
5. 如果存在 `scripts/mistakebook_cli.py`，优先执行：
   `python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval`
6. 说明为什么前面的处理仍然失败
7. 选择一个当前最有效的方案来重新处理
8. 如果用户还没有确认完成，仍然保持在闭环中，并继续按需要追问“错题集 / 记事本”收录
