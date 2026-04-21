# Storage And Scope

## 默认目录布局

### 项目级

1. Codex
   - `<project>/.codex/mistakebook/failures/`
   - `<project>/.codex/mistakebook/notes/`
   - `<project>/.codex/mistakebook/memory/`
   - `<project>/.codex/mistakebook/state/`
2. Claude
   - `<project>/.claude/mistakebook/failures/`
   - `<project>/.claude/mistakebook/notes/`
   - `<project>/.claude/mistakebook/memory/`
   - `<project>/.claude/mistakebook/state/`
3. VSCode
   - `<project>/.vscode/mistakebook/failures/`
   - `<project>/.vscode/mistakebook/notes/`
   - `<project>/.vscode/mistakebook/memory/`
   - `<project>/.vscode/mistakebook/state/`
4. Generic
   - `<project>/.mistakebook/failures/`
   - `<project>/.mistakebook/notes/`
   - `<project>/.mistakebook/memory/`
   - `<project>/.mistakebook/state/`

### 全局级

1. Codex
   - `~/.codex/mistakebook/failures/`
   - `~/.codex/mistakebook/notes/`
   - `~/.codex/mistakebook/memory/`
   - `~/.codex/mistakebook/state/`
2. Claude
   - `~/.claude/mistakebook/failures/`
   - `~/.claude/mistakebook/notes/`
   - `~/.claude/mistakebook/memory/`
   - `~/.claude/mistakebook/state/`
3. VSCode
   - `~/.vscode/mistakebook/failures/`
   - `~/.vscode/mistakebook/notes/`
   - `~/.vscode/mistakebook/memory/`
   - `~/.vscode/mistakebook/state/`
4. Generic
   - `~/.mistakebook/failures/`
   - `~/.mistakebook/notes/`
   - `~/.mistakebook/memory/`
   - `~/.mistakebook/state/`

如果宿主不允许写这些默认位置，可以显式指定一个可写的全局根目录。

## 每个 store 的最小文件

1. `failures/INDEX.md`
2. `notes/INDEX.md`
3. `memory/PROJECT_MEMORY.md` 或 `memory/GLOBAL_MEMORY.md`
4. `state/catalog.json`
5. `state/memory_state.json`

## scopeDecision 判断规则

### `project`

适用于：

1. 项目目录结构
2. 项目专有命名
3. 项目业务规则
4. 项目构建/测试/部署流程
5. 某仓库内特殊约束

### `global`

适用于：

1. 通用验证缺失
2. 通用事实核对缺失
3. 通用沟通误读
4. 通用推理偏差
5. 通用工程坏习惯

### `both`

满足下面两个条件时使用：

1. 这个条目在当前项目里有详细复盘或长期注意价值
2. 同时还能抽出稳定、可泛化、跨项目可复用的规则

## 条目类型

### `mistake`

适用于：

1. 已经发生的错误
2. 已经完成纠错的失败案例
3. 需要复盘“为什么错”的内容

### `note`

适用于：

1. 不是错误，但值得长期保留的注意事项
2. 会反复影响后续工作方式的操作约束
3. 主动记录的提醒、边界、协作习惯

## 记忆写法

### 项目记忆

项目记忆应该保留：

1. 当前项目稳定约束
2. 当前项目主动注意事项
3. 当前项目高风险误区
4. 已经验证过的最佳实践

### 全局记忆

全局记忆应该保留：

1. 跨项目通用规则
2. 通用验证纪律
3. 通用沟通纪律
4. 通用主动注意事项

## 记忆是缓存，不是仓库全文索引

项目记忆和全局记忆都应视作缓存层：

1. 初期条目还少时，可以几乎全量保留
2. 一旦超过阈值，就不再机械累加
3. 要开始按“命中 / 检索 / 新旧程度 / 优先级”筛选
4. 详细条目永远在 `failures/` 和 `notes/` 里
5. 缓存层只保留高价值、短而准的摘要

## 命中与遗忘

推荐维护两类统计：

1. `retrievalCount`
   - 被飞升模式或其他上下文收集流程读取了多少次
2. `hitCount`
   - 被实际证明“仍然值得保留在缓存里”的命中次数

推荐策略：

1. 高命中 + 最近仍活跃
   - 优先保留在缓存
2. 低命中 + 长期没有再次检索
   - 进入 `deferredEntries`
3. 只是暂时遗忘
   - 不删除详细条目，只是暂时移出记忆缓存

## 每次归档都要更新记忆

推荐做法：

1. 把当前条目写成详细 Markdown
2. 同步更新 `state/catalog.json`
3. 自动刷新 `memory/*.md`
4. 如果条目量和噪声开始上升，再执行一次 `consolidate`

## full rollup / consolidate 触发条件

遇到下列情况时，除了普通刷新，还要做一次集中整理：

1. 同一主题累计 3 个条目以上
2. 某个 store 累计新增 5 个条目
3. 距上次集中整理超过 14 天
4. 记忆内容已经明显超过阈值

`consolidate` 的目标不是增加字数，而是：

1. 合并重复项
2. 去掉失效项
3. 提升高命中条目的可见度
4. 让长期低命中条目暂时退出缓存
5. 让记忆文件保持短、真、可执行
