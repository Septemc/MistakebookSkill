# Mistakebook Skill 存储与保存机制说明

- 项目名称：Mistakebook Skill
- 作者：Septemc
- 文档日期：2026-04-20
- 文档目的：回答“安装 Skill 后，错题集保存在哪里、项目记忆保存在哪里、全局内容保存在哪里、它们到底是怎么保存的”

## 1. 先给结论

Mistakebook Skill 采用的是”文件系统落盘”方案，不是数据库方案。

也就是说，安装完成后，错题集和记忆都会被保存成真实目录、真实 Markdown 文件、真实 JSON 文件。

最重要的 3 条结论是：

1. **所有 Agent 工具（Codex、Claude Code、VSCode）共享统一存储路径**
   - 项目级：`<project>/.mistakebook/`
   - 全局级：`~/.mistakebook/`
2. 只有用户明确确认”纠错完成”后，Agent 才应该真正归档并写盘
   - 在确认之前，处于纠错闭环中，不应该提前把案例写进错题集
3. 如果从旧版迁移，运行 `python scripts/mistakebook_cli.py migrate --host codex --project-root .` 自动迁移

## 2. 保存位置总表

**所有 Agent 工具共享统一存储路径：**

### 2.1 项目级保存位置

| 宿主 | 项目级根目录 | 错题集目录 | 记忆目录 |
| --- | --- | --- | --- |
| **所有** | `<project>/.mistakebook/` | `<project>/.mistakebook/failures/` | `<project>/.mistakebook/memory/` |

### 2.2 全局级保存位置

| 宿主 | 全局级根目录 | 错题集目录 | 记忆目录 |
| --- | --- | --- | --- |
| **所有** | `~/.mistakebook/` | `~/.mistakebook/failures/` | `~/.mistakebook/memory/` |

### 2.3 从旧版迁移

旧版路径（已废弃）：
- `.codex/mistakebook/`、`.claude/mistakebook/`、`.vscode/mistakebook/`
- `~/.codex/mistakebook/`、`~/.claude/mistakebook/`、`~/.vscode/mistakebook/`

运行迁移命令自动合并到统一路径：
```bash
python scripts/mistakebook_cli.py migrate --host codex --project-root .
```

### 2.4 共享配置与运行时状态位置

这些不是“错题案例正文”，但和保存机制密切相关：

| 类型 | 默认路径 | 作用 |
| --- | --- | --- |
| 自动识别配置 | `~/.mistakebook/config.json` | 保存 `auto_detect` 开关 |
| 运行时 checkpoint | `~/.mistakebook/runtime-journal.md` | 在上下文压缩或会话恢复时保存当前纠错 case 的运行态 |

所有 Agent 工具（Codex、Claude Code、VSCode）现在共享统一的 `.mistakebook/` 目录，不再按宿主分目录保存。

## 3. 以你当前 Windows 环境举例

如果当前用户目录是 `C:\Users\Septem`，项目目录是：

```text
F:\_WorkSpace\Projects\MistakebookSkill
```

那么默认路径会是下面这样（所有宿主统一）：

### 3.1 所有宿主通用路径

项目级：

```text
F:\_WorkSpace\Projects\MistakebookSkill\.mistakebook\
```

全局级：

```text
C:\Users\Septem\.mistakebook\
```

### 3.2 共享配置和运行时状态

```text
C:\Users\Septem\.mistakebook\config.json
C:\Users\Septem\.mistakebook\runtime-journal.md
```

## 4. 每个保存目录里到底有什么

每个 store 的最小结构是：

```text
mistakebook/
├─ failures/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ memory/
│  ├─ PROJECT_MEMORY.md    # 仅项目级 store 使用
│  └─ GLOBAL_MEMORY.md     # 仅全局级 store 使用
└─ state/
   └─ catalog.json
```

但这里有一个容易误解的点：

1. 项目级 store 并不是同时维护 `PROJECT_MEMORY.md` 和 `GLOBAL_MEMORY.md`
   - 项目级 store 只会创建 `PROJECT_MEMORY.md`
2. 全局级 store 也不是同时维护两份
   - 全局级 store 只会创建 `GLOBAL_MEMORY.md`

也就是说，真实落盘行为是：

### 4.1 项目级 store

```text
<project>/<host-root>/mistakebook/
├─ failures/
│  ├─ INDEX.md
│  └─ 20260420T120000Z_某个案例.md
├─ memory/
│  └─ PROJECT_MEMORY.md
└─ state/
   └─ catalog.json
```

### 4.2 全局级 store

```text
<user-home>/<host-root>/mistakebook/
├─ failures/
│  ├─ INDEX.md
│  └─ 20260420T120000Z_某个案例.md
├─ memory/
│  └─ GLOBAL_MEMORY.md
└─ state/
   └─ catalog.json
```

## 5. 各类文件分别保存什么

### 5.1 `failures/INDEX.md`

这个文件是“错题目录页”。

作用：

1. 列出当前 store 下已经归档过多少案例
2. 记录更新时间
3. 给每条错题一个可读目录入口

它不是原始数据源，但便于人类查阅。

### 5.2 `failures/<timestamp>_<slug>.md`

这是单条详细错题案例正文，也是最核心的归档文件。

里面通常会写：

1. 标题
2. archived_at
3. host
4. session / trace / case_id
5. scope
6. 错误总结
7. 这次到底错在哪里
8. 以后必须遵守
9. 已经纠正并吃透的点
10. 原始问题
11. 原始回答
12. 用户纠错反馈
13. 最终正确回答
14. 项目记忆增量
15. 全局记忆增量

这份 Markdown 是“详细错题集”的本体。

### 5.3 `memory/PROJECT_MEMORY.md`

这是项目记忆。

它应该只保留：

1. 当前项目稳定约束
2. 当前项目高风险误区
3. 已经在本项目里验证过的最佳实践

它不应该变成聊天流水账。

### 5.4 `memory/GLOBAL_MEMORY.md`

这是全局记忆。

它应该只保留：

1. 跨项目通用规则
2. 通用验证纪律
3. 通用沟通纪律
4. 通用纠错纪律

它不应该保留项目私有路径、仓库私有术语、过细的实现细节。

### 5.5 `state/catalog.json`

这是机器可读索引。

脚本会在这里保存每个案例的摘要元信息，例如：

1. `caseId`
2. `title`
3. `fileName`
4. `archivedAt`
5. `scopeDecision`
6. `keywords`
7. `summary`

相比 `INDEX.md`，它更适合程序继续读取和排序。

## 6. 它是“什么时候”保存的

这件事非常关键。

### 6.1 不是什么时候都保存

Mistakebook Skill 不是每轮一出错就立刻写盘。

按当前协议，正确时机是：

1. 用户指出错误
2. Agent 进入纠错闭环
3. Agent 持续修正
4. 用户明确确认“可以了 / 已完成 / 归档吧 / 写入错题集”
5. 这时才进入正式归档

也就是说：

`没有用户确认，就不应该把这次案例正式写入错题集。`

### 6.2 会提前保存什么

如果对话很长，发生上下文压缩，当前实现允许把运行态暂存到：

```text
~/.mistakebook/runtime-journal.md
```

这个文件不是正式归档案例，而是“中断恢复用的检查点”。

它用于保存：

1. 当前状态
2. 当前模式是否 ascended
3. case_id
4. rejection_count
5. correction_attempt_count
6. 原始问题摘要
7. 当前纠错链摘要
8. 下一步该做什么

所以要区分两类保存：

1. `runtime-journal.md`
   - 暂存运行态
   - 用于恢复
   - 不是正式错题集条目
2. `failures/*.md`
   - 正式归档案例
   - 用于长期记忆沉淀

## 7. 它到底“怎么保存”

当前仓库里，最真实的保存逻辑由：

```text
scripts/mistakebook_cli.py
```

负责。

保存可以分成两步看。

### 7.1 第一步：初始化目录 `bootstrap`

命令形态：

```bash
python scripts/mistakebook_cli.py bootstrap --host codex --project-root .
```

这个命令会做什么：

1. 根据 `--host` 计算项目级和全局级根目录
2. 创建：
   - `failures/`
   - `memory/`
   - `state/`
3. 如果文件不存在，就初始化：
   - `failures/INDEX.md`
   - `memory/PROJECT_MEMORY.md` 或 `memory/GLOBAL_MEMORY.md`
   - `state/catalog.json`

也就是说，`bootstrap` 是“搭好空目录 + 种下模板文件”。

### 7.2 第二步：正式归档 `archive`

命令形态：

```bash
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-file payload.json
```

这个命令会做什么：

1. 读取归档 payload
2. 检查必要字段是否存在
3. 看 `scopeDecision` 是：
   - `project`
   - `global`
   - `both`
4. 根据 `scopeDecision` 决定写哪个 store
5. 生成单条错题 Markdown
6. 更新 `catalog.json`
7. 重写 `INDEX.md`
8. 重写记忆文件

所以真正的保存动作，不是“随便 append 一行”，而是一整套：

1. 写正文
2. 更新索引
3. 更新机器索引
4. 更新记忆

## 8. `scopeDecision` 决定写到哪里

项目里不是所有错误都要同时写到项目级和全局级。

### 8.1 `project`

只写项目级。

适用于：

1. 当前项目目录结构
2. 当前项目业务规则
3. 当前项目代码约定
4. 当前项目构建/测试/部署流程

例如：

1. 把这个仓库的路径规则理解错了
2. 忽略了本项目已有约定
3. 错读当前项目接口契约

### 8.2 `global`

只写全局级。

适用于：

1. 通用验证失误
2. 通用事实核对缺失
3. 通用沟通误读
4. 通用推理偏差

例如：

1. 没有先读真实文件就下结论
2. 没有跑验证就说修好了
3. 把用户纠错误当成普通补充需求

### 8.3 `both`

同时写项目级和全局级。

适用于：

1. 这个案例在当前项目中值得保留具体复盘
2. 同时还能抽出一条可跨项目复用的稳定规则

所以最终写盘目标是：

1. `project`
   - 只写项目 store
2. `global`
   - 只写全局 store
3. `both`
   - 项目 store 和全局 store 都写

## 9. 记忆是怎么保存和刷新的

这一部分很多人会误会成“只保存错题，不保存记忆”，但当前设计不是这样。

### 9.1 每次归档都更新记忆

按 Skill 规则和脚本逻辑：

1. 每写入一个案例
2. 同时也会更新相应的记忆文件

也就是说：

1. 写项目级案例时
   - 会更新 `PROJECT_MEMORY.md`
2. 写全局级案例时
   - 会更新 `GLOBAL_MEMORY.md`
3. 如果是 `both`
   - 两边都更新

### 9.2 记忆内容来源有两种

#### 方式 A：payload 显式提供

如果 payload 中带了：

1. `projectMemoryMarkdown`
2. `globalMemoryMarkdown`

脚本会直接把这两段内容写入对应记忆文件。

这意味着：

1. 上层 Agent 可以自己先总结出更好的记忆文本
2. CLI 负责忠实落盘

#### 方式 B：脚本自动回填

如果 payload 没有显式提供记忆正文，脚本会走 fallback 逻辑，自动根据这些字段生成记忆：

1. `rules`
2. `confirmedUnderstanding`
3. `whatWentWrong`
4. `preventionChecklist`

然后生成一份简化记忆文档。

所以当前真实行为是：

1. 优先使用 Agent 已经总结好的记忆 Markdown
2. 如果没给，就由脚本自动生成兜底版

### 9.3 当前脚本会不会自动做 full rollup

这里要特别说明一下“协议”和“当前实现”的区别。

协议层要求：

1. 同主题累计 3 次以上
2. 某个索引新增 5 条
3. 超过 14 天

就应该做更彻底的记忆整理。

但是当前 `scripts/mistakebook_cli.py` 的真实实现是：

1. 每次 archive 都会更新记忆
2. 当案例数达到 5 的倍数时，会返回 `full_rollup_recommended: true`
3. 但脚本本身目前没有单独的 `consolidate` 子命令实现真正的全量重写

所以当前状态更准确地说是：

1. “常规刷新”已经实现
2. “彻底整理”还主要停留在协议约定和推荐信号层

## 10. 错题条目文件名是怎么命名的

脚本会按下面规则生成文件名：

```text
<UTC时间戳>_<标题slug>.md
```

例如：

```text
20260420T090501Z_没有先读真实文件就下结论.md
```

这里的规则是：

1. 时间戳使用 UTC
2. 标题会经过 slugify
3. 非法字符会被替换或压缩
4. 超过长度会截断

这样做的好处是：

1. 文件名稳定可读
2. 大体按时间排序
3. 能直接从文件名看出主题

## 11. `catalog.json` 和 `INDEX.md` 的区别

这两个文件容易看起来重复，但其实职责不同。

### 11.1 `INDEX.md`

偏向人类阅读：

1. 可以直接打开浏览
2. 能看到条目清单
3. 更适合作为手工查看目录页

### 11.2 `catalog.json`

偏向程序读取：

1. 更适合脚本做排序、过滤、去重
2. 可以稳定读取元信息
3. 方便以后做检索或二次加工

所以它们不是二选一，而是“人读一个、程序读一个”。

## 12. 实际保存流程示意

### 12.1 普通项目级保存

```text
用户纠错
-> Agent 进入错题集闭环
-> 用户明确确认完成
-> 生成 payload，scopeDecision=project
-> bootstrap 确保目录存在
-> archive 写入项目级 failures/*.md
-> 更新项目级 failures/INDEX.md
-> 更新项目级 state/catalog.json
-> 更新项目级 memory/PROJECT_MEMORY.md
```

### 12.2 全局级保存

```text
用户纠错
-> Agent 进入错题集闭环
-> 用户明确确认完成
-> 生成 payload，scopeDecision=global
-> bootstrap 确保目录存在
-> archive 写入全局级 failures/*.md
-> 更新全局级 failures/INDEX.md
-> 更新全局级 state/catalog.json
-> 更新全局级 memory/GLOBAL_MEMORY.md
```

### 12.3 同时保存项目级和全局级

```text
用户纠错
-> Agent 进入错题集闭环
-> 用户明确确认完成
-> 生成 payload，scopeDecision=both
-> bootstrap 确保两边目录存在
-> 分别写项目级案例和全局级案例
-> 分别更新两边索引和记忆
```

## 13. 你真正需要记住的几个路径

如果你平时只想快速知道”去哪里看”，那记下面这些就够了。

### 13.1 看项目错题

去当前项目下面找：

- `.mistakebook/failures/`

### 13.2 看项目记忆

去当前项目下面找：

- `.mistakebook/memory/PROJECT_MEMORY.md`

### 13.3 看全局错题

去用户目录下面找：

- `~/.mistakebook/failures/`

### 13.4 看全局记忆

去用户目录下面找：

- `~/.mistakebook/memory/GLOBAL_MEMORY.md`

### 13.5 看自动识别开关和恢复状态

去：

1. `~/.mistakebook/config.json`
2. `~/.mistakebook/runtime-journal.md`

## 14. 当前项目关于“怎么保存”的最终判断

如果把当前仓库的真实行为压缩成一句话，可以这样说：

`Mistakebook Skill 会在用户明确确认纠错完成后，根据 scopeDecision 把案例写成 Markdown 条目，并同步更新 INDEX、catalog.json 和项目/全局记忆；项目级内容写到项目根目录下，全局级内容写到用户目录下，共享配置和 checkpoint 则写到 ~/.mistakebook。`

## 15. 相关文件

如果你后面要继续追源码，优先看这几个：

1. `scripts/mistakebook_cli.py`
2. `skills/mistakebook/references/storage-and-scope.md`
3. `skills/mistakebook/references/archive-schema.md`
4. `skills/mistakebook/SKILL.md`
5. `README.md`
