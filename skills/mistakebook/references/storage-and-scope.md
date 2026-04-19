# Storage And Scope

## 默认目录布局

### 项目级

1. Codex
   - `<project>/.codex/mistakebook/failures/`
   - `<project>/.codex/mistakebook/memory/`
2. Claude
   - `<project>/.claude/mistakebook/failures/`
   - `<project>/.claude/mistakebook/memory/`
3. VSCode
   - `<project>/.vscode/mistakebook/failures/`
   - `<project>/.vscode/mistakebook/memory/`
4. Generic
   - `<project>/.mistakebook/failures/`
   - `<project>/.mistakebook/memory/`

### 全局级

1. Codex
   - `~/.codex/mistakebook/failures/`
   - `~/.codex/mistakebook/memory/`
2. Claude
   - `~/.claude/mistakebook/failures/`
   - `~/.claude/mistakebook/memory/`
3. VSCode
   - `~/.vscode/mistakebook/failures/`
   - `~/.vscode/mistakebook/memory/`
4. Generic
   - `~/.mistakebook/failures/`
   - `~/.mistakebook/memory/`

如果宿主不允许写这些默认位置，可以显式指定一个可写的全局根目录。

## 每个 store 的最小文件

1. `failures/INDEX.md`
2. `failures/<timestamp>_<slug>.md`
3. `memory/PROJECT_MEMORY.md` 或 `memory/GLOBAL_MEMORY.md`
4. `state/catalog.json`

## scopeDecision 判断规则

### `project`

适用于：

1. 项目目录结构
2. 项目专有命名
3. 项目业务规则
4. 项目构建/测试/部署流程
5. 某仓库内特殊约束

例子：

1. 把当前仓库的路径规则理解错了
2. 忽略团队已有的代码约定
3. 错读某个项目的接口契约

### `global`

适用于：

1. 通用验证缺失
2. 通用事实核对缺失
3. 通用沟通误读
4. 通用推理偏差
5. 通用工程坏习惯

例子：

1. 没有先读真实文件就下结论
2. 没跑验证就声称修好了
3. 把用户纠正当成补充需求，没有进入纠错闭环

### `both`

满足下面两个条件时使用：

1. 这个案例在当前项目里有详细复盘价值
2. 同时还能抽出稳定、可泛化、跨项目可复用的规则

`both` 不等于简单重复。项目级可以保留具体上下文；全局级要适度泛化，减少项目私有细节。

## 记忆写法

### 项目记忆

项目记忆应该保留：

1. 当前项目稳定约束
2. 当前项目高风险误区
3. 已经反复验证过的最佳实践

不要保留：

1. 完整对话原文
2. 临时情绪性表述
3. 一次性、不稳定、无法复用的细节

### 全局记忆

全局记忆应该保留：

1. 跨项目通用规则
2. 通用验证纪律
3. 通用沟通纪律
4. 通用纠错纪律

不要保留：

1. 仓库专有路径
2. 项目私有术语
3. 当前项目的局部实现细节

## 每次归档都要更新记忆

推荐做法：

1. 把当前案例写成详细条目
2. 同步刷新一份更短的记忆文档
3. 记忆文档只保留稳定、可执行、未来值得再次注入的要点

## full rollup 触发条件

遇到下列情况时，除了普通更新，还要做一次集中整理：

1. 同一主题累计 3 个案例以上
2. 某个索引累计新增 5 个案例
3. 距上次 full rollup 超过 14 天

full rollup 的目标不是增加字数，而是：

1. 合并重复项
2. 去掉失效项
3. 把相似错误抽象成稳定规则
4. 让记忆文档保持短、真、可执行
