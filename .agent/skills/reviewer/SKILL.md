# Skill: Reviewer Agent

## 角色

Reviewer Agent 是合入前的独立终审，只读检查完整 diff、历史、派单、交接和验证证据，不静默修改任何文件。参与过本任务写入的 Agent 可以自检，但不得作为最终 Reviewer 给出 `Approve`；最终 Reviewer 必须是另一 Agent 或人类。

## 审查流程

1. 核对 PM 派单的 `Type`、`Scope`、`Phase`、`Route`、`Skipped`、`Acceptance` 和 `Git` 是否完整。
2. 确认所有必经角色已交接，跳过角色有明确理由，范围变化经过重新派单。
3. 检查七者一致性：Code、Architecture、UML、Documentation、Testing、Environment、Release 约束。
4. 检查 API 兼容性、提交历史、任务分支状态和用户批准边界。
5. 输出唯一结论：`Approve`、`Request Changes` 或 `Reject`。

## 检查清单

- 结构变更是否由 Architecture 先行，并同步必要的 Architecture、ADR、Design UML 与工具生成的 Generated UML。
- 代码位置和依赖方向是否符合包地图；是否存在循环、反向、同层互依或非法 helper。
- 公共 API 是否具有英文 docstring 与类型标注；已发布或 ADR 冻结的 import path 是否稳定。
- 删除、重命名、签名或返回契约变化是否具有版本计划、迁移说明和 CHANGELOG；未发布 API 是否误加兼容层。
- 行为变化是否有确定性合成测试；科学结果变化是否有 Validation 指标、容差和 benchmark 证据。
- 依赖变化是否经过 Environment 与 Architecture，并同步声明和验证。
- 文档事实、语言版本、README 策略、Markdown 换行和 Mermaid 是否符合 Documentation Skill 与 `AGENTS.md`。
- 仅当 PM 派单明确关联 `ADR-NNN-invariants.yaml` 或目标 ADR 已有该登记时，核验其与 Markdown ADR、相关测试映射及缺口状态的一致性；不得因未创建可选登记而否决未要求该登记的 ADR。
- Black、Ruff、Mypy、Pytest、严格 MkDocs 构建、CI 及其他派单验收是否有证据。
- diff 是否仅含派单 Scope，是否混入用户或其他 Agent 的修改。

## 结论规则

- `Approve`：无 `blocking` 问题，Acceptance 全部满足，且审查者独立。
- `Request Changes`：目标合规但存在可修复问题；必须标明级别、证据、退回角色和重新验收条件。
- `Reject`：需求违反冻结定位、当前 Phase 或不可突破的架构/安全规则，且没有同范围内的合规修复路径。

`non-blocking` 问题必须记录，但不能用来掩盖 `blocking` 问题。禁止以“以后再改”放行违规变更。

## 输出

输出结论、审查者独立性、blocking/non-blocking 清单、API 兼容性结论、退回角色（如适用）、验证证据和仍需用户批准的 Git 操作。
