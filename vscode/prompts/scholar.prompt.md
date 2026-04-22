---
agent: 'agent'
description: "在开始新任务前运行学霸模式预检，只在高置信命中时注入一行历史提醒。"
---

# Scholar Mode

在正式回答前先执行：

`python scripts/mistakebook_cli.py scholar --host vscode --project-root . --scope both --text "<当前任务>"`

执行规则：

1. 只有 `shouldInject = true` 时，才在正式回答前输出一行 `message`。
2. 如果 `shouldInject = false`，保持静默，直接正常回答。
3. 如果当前已经进入纠错闭环、记事本归档或 `Ascended Mode`，不要运行 `scholar`。
4. `scholar` 负责答前避错，不替代 `Ascended Mode` 的失败升级处理。
5. 需要长期关闭或开启时，分别执行：
   - `python scripts/mistakebook_cli.py config --scholar off`
   - `python scripts/mistakebook_cli.py config --scholar on`
