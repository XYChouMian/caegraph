# ADR-002: UML 双体系（Design UML / Generated UML）

- 编号：ADR-002
- 标题：维护手工 Design UML 与工具生成 Generated UML 两套图，以差异审查保证设计-实现一致
- 日期：2026-09-03
- 状态：accepted
- 关联：Phase 0；`architecture/UML_GUIDE.md`；Architecture Agent SKILL

## 背景

AI Agent 为主的开发模式容易"代码先行、设计后补"。需要一种机制让"计划设计"
与"代码真实状态"的差异持续可见、可审查。

## 决策

- Design UML：`architecture/design/*.puml`，由 Architecture Agent 手工维护，
  结构变更前先改它。
- Generated UML：`diagrams/generated/`，仅由工具（如 `pyreverse`）从源码生成，
  禁止手工编辑。
- 两套图的差异即结构性技术债，Architecture Agent 定期审查并逐项处置
  （整改代码 / 演进设计并记录 ADR）。

## 备选方案

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 只保留生成图 | 否决 | 生成图描述现状，无法承载"计划中的抽象"，失去设计评审锚点 |
| 只保留手写图 | 否决 | 与代码必然漂移且不可验证 |
| 双体系（采纳） | 采纳 | 意图与事实分离，差异可见、可问责 |

## 影响

- 涉及结构的 PR 必须同时更新 Design UML 并再生成 Generated UML。
- Reviewer 增加手工编辑生成图的检查项。
