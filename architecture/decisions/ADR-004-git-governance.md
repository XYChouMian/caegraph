# ADR-004: Git 作为所有 Agent 的基础工程能力

- 编号：ADR-004
- 标题：Git 作为共享工程能力，而非独立 Agent 角色
- 日期：2026-09-04
- 状态：accepted
- 关联：Phase 0；`.agent/WORKFLOW.md`；`.agent/skills/git/SKILL.md`

## 背景

CAEGraph 的 Agent 工作流覆盖需求、架构、编码、测试、文档、审查与发布，但此前
只有零散 Git 限制，没有统一的权限、分支、提交、PR、发布和紧急操作规范。这会
使角色边界与外部写操作的授权范围不清晰，也无法稳定利用 Git 追踪架构演化。

## 决策

- Git 是所有 Agent 必须遵守的基础工程能力，不新增独立执行角色。
- `.agent/skills/git/SKILL.md` 是 Git 操作规则的唯一详细来源；`AGENTS.md` 与
  `.agent/WORKFLOW.md` 强制引用它，各角色 Skill 不重复完整规则。
- Agent 可在已授权任务范围内检查仓库、创建本地任务分支、显式暂存和提交。
- merge、push、pull、fetch、tag、远程 PR/Issue/Release、历史改写与发布必须获得
  用户对具体操作的明确批准。
- `main` 保持稳定且禁止直接提交；所有变化通过具名任务分支与 Reviewer 审查。
- Git history 记录演化事实，ADR 记录决策理由，两者共同构成项目记忆。

## 备选方案

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 为 Git 设置独立执行 Agent | 否决 | Git 横跨所有角色，集中执行会割裂职责与上下文 |
| 只在各角色 Skill 分散写规则 | 否决 | 重复内容容易漂移，授权边界难以保持一致 |
| 共享 Git Skill + 顶层强制引用 | 采纳 | 单一规则来源，同时保留各角色职责边界 |

## 影响

- 所有 Agent 开始 Git 操作前必须读取并遵守 Git Skill。
- 用户仍控制所有远程、合入、tag、历史改写及发布操作的最终授权。
- 本决策不改变 Python 包结构、依赖分层、Design UML 或公共 API。
