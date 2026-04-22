# Codex Skill Chip Entry Design

## Background

`mistakebook` 当前在 Codex 里同时暴露了两类入口：

1. skill 入口
   - `$mistakebook`
2. prompt 入口
   - `/prompts:mistakebook`
   - `/prompts:notebook`
   - `/prompts:ascended`
   - `/prompts:scholar`

用户反馈集中在 Codex 的 prompt 入口体验：当使用 `/prompts:ascended` 时，输入框会直接展开整段 prompt 正文，观感明显差于 `$pua` 这类 skill chip 入口。

当前问题不是单个 prompt 文案太长，而是 Codex 对 skill 和 prompt 的 UI 表现不同：

1. skill 入口会被渲染成可视化 chip
2. prompt 入口会把正文插入输入框

因此，单独缩短 `commands/ascended.md` 无法从根因上解决观感问题。

## Goals

1. 在 Codex 中为 `ascended`、`notebook`、`scholar` 提供 skill-chip 风格入口
2. 保留现有 `/prompts:*` 兼容入口，避免破坏已有使用方式
3. 将 Codex 文档和安装说明改为优先推荐 skill 入口，而不是 prompt 入口
4. 为新的 Codex skill 入口补充基础回归测试

## Non-Goals

1. 不改变 Claude 风格宿主对 `commands/*.md` 的依赖方式
2. 不移除现有 `/prompts:*` 文件
3. 不在这次改动里重构 `mistakebook_cli.py` 的业务逻辑
4. 不在这次改动里设计新的 UI 组件或修改 Codex 客户端行为

## Current State

### Codex

Codex 当前只安装了一个 skill 目录：

1. `codex/mistakebook/`

其余能力通过 `commands/*.md` 复制到 `~/.codex/prompts/` 暴露给 `/prompts:*`。

### Claude-style Hosts

Claude 风格宿主直接依赖：

1. `.claude-plugin/plugin.json`
2. `commands/*.md`
3. `hooks/hooks.json`

因此 `commands/*.md` 仍然必须保留。

## Options Considered

### Option A: 仅缩短 prompt 文案

优点：

1. 改动最小

缺点：

1. 仍然是 prompt 注入，不会变成 chip
2. 只能缓解，不能解决体验问题

### Option B: 删除 `/prompts:*`，只保留 `$mistakebook`

优点：

1. 入口最统一

缺点：

1. 破坏兼容性
2. 用户已经形成 `/prompts:*` 使用习惯
3. README 和安装说明已有相关入口文档

### Option C: 新增 Codex skill 包装入口，同时保留 `/prompts:*`

优点：

1. 从根因上让 Codex 获得 chip 体验
2. 不破坏已有 prompt 入口
3. 可渐进迁移文档和用户习惯

缺点：

1. 需要维护一组 Codex 专用 skill 包装层

### Recommendation

采用 Option C。

## Proposed Design

### 1. 新增 Codex skill 包装层

在 `codex/` 下新增独立 skill 目录：

1. `codex/ascended/`
2. `codex/notebook/`
3. `codex/scholar/`

每个目录包含：

1. `SKILL.md`
2. `agents/openai.yaml`

这些 skill 的职责不是复制整套底层实现，而是作为 Codex 专用入口包装层：

1. `ascended`
   - 进入 `mistakebook` 的飞升模式
2. `notebook`
   - 进入 `mistakebook` 的 `note` 流程
3. `scholar`
   - 进入轻量预检流程

### 2. 保留 `codex/mistakebook/` 作为总入口

`codex/mistakebook/` 继续保留，用作：

1. 总 skill
2. 自动触发或手动总入口

新增 skill 不替代 `mistakebook`，而是提供更细粒度、可选中的 Codex 入口。

### 3. 保留 `commands/*.md` 兼容入口

继续保留：

1. `commands/mistakebook.md`
2. `commands/ascended.md`
3. `commands/notebook.md`
4. `commands/scholar.md`

原因：

1. Claude 风格宿主仍然依赖这些文件
2. Codex 现有 `/prompts:*` 入口不能直接删除

但在 Codex 文档中，`/prompts:*` 将降级为兼容入口，而非主入口。

### 4. 更新安装与使用文档

需要更新：

1. `.codex/INSTALL.md`
2. `README.md`

文档策略：

1. 优先展示 Codex skill 入口
2. 明确 `/prompts:*` 为兼容入口
3. 明确推荐用户优先使用 skill chip

示例表述方向：

1. 推荐：`$mistakebook`、`$ascended`、`$notebook`、`$scholar`
2. 兼容：`/prompts:mistakebook`、`/prompts:ascended`、`/prompts:notebook`、`/prompts:scholar`

### 5. 安装落点调整

Codex 安装说明需要从“只链接一个 skill”改成“安装多个 skill 目录”。

也就是说，安装时不再只创建：

1. `~/.codex/skills/mistakebook`

还需要创建：

1. `~/.codex/skills/ascended`
2. `~/.codex/skills/notebook`
3. `~/.codex/skills/scholar`

prompt 复制仍保留，但不再是默认推荐方式。

### 6. 测试范围

新增或扩展测试，覆盖：

1. Codex skill 包装目录存在
2. 各包装 skill 的 `openai.yaml` 存在且声明合理
3. README / 安装说明包含新的 Codex skill 用法
4. 现有 Claude 集成测试不回归

优先在宿主集成测试层验证入口存在，不把测试绑定到 Codex 客户端私有 UI 细节。

## File Impact

### New Files

1. `codex/ascended/SKILL.md`
2. `codex/ascended/agents/openai.yaml`
3. `codex/notebook/SKILL.md`
4. `codex/notebook/agents/openai.yaml`
5. `codex/scholar/SKILL.md`
6. `codex/scholar/agents/openai.yaml`

### Updated Files

1. `.codex/INSTALL.md`
2. `README.md`
3. `tests/test_host_integration.py`

### Deferred

如编码清理会影响本次改动可读性，可顺手处理：

1. `codex/mistakebook/SKILL.md` 末尾的编码污染段落

但该项不是本次入口改造的主目标。

## Acceptance Criteria

1. Codex 中存在可被安装的 `ascended`、`notebook`、`scholar` skill 目录
2. 文档明确把 skill 作为 Codex 主入口
3. 现有 `commands/*.md` 仍然保留
4. 回归测试通过

## Risks

1. 如果 Codex 仅支持特定 skill 命名规则，新 skill 名称可能需要微调
2. 文档若仍强调 `/prompts:*`，用户会继续走旧入口，问题表面上仍然存在
3. 若安装脚本或用户手工安装只链接 `mistakebook`，新增 skill 不会自动出现

## Rollout

1. 先落地 skill 包装目录和测试
2. 再更新安装说明和 README
3. 本地重新安装 Codex develop 版本验证入口是否被发现
