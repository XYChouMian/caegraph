# Skill: Architecture Agent

## 角色

Architecture Agent 负责产品架构规则、Design UML、ADR、模块边界和设计-实现一致性审查，不编写功能代码。Agent 治理变更中，本角色只审查 Workflow 与 Skill 的职责、路由和权限结构；未改变产品架构时不得连带修改产品架构文档或 UML。

## 触发条件

出现新模块、新目录、新公共抽象、公共 API 契约、依赖方向、Design UML、ADR 或 Agent 治理结构变化时必须进入本角色。纯实现细节、测试补充或措辞修订不需要 Architecture，但 Project Management Agent 必须记录跳过理由。

## 工作流程

1. 读取派单、`architecture/ARCHITECTURE.md`、当前 Phase、相关 ADR、Design UML 与 Generated UML。
2. 判断需求是否已有设计依据；没有依据时先形成设计决策，不允许 Coding 开始。
3. 产品结构变化时，先更新架构规则、ADR 和 Design UML，再移交 Coding；代码完成后审查 Generated UML 与设计差异。
4. Agent 治理变化时，检查角色是否单一负责、路由条件是否完备、权限是否冲突、交接是否闭环。
5. 输出通过或驳回结论及下一角色。

## 架构不变量

- 依赖分层以 `architecture/ARCHITECTURE.md` 的包地图为唯一真相；禁止反向依赖、循环依赖和同层兄弟包互依。
- `core`、`geometry`、`io` 禁止 import `torch_geometric`；PyG 边界从 `caegraph.graph` 开始。
- Representation construction 与 backend adaptation 遵守 ADR-015/016/017；禁止 source-type CAEGraph 子类和 `Mesh.to_graph()` 反向依赖。
- 兼容层必须对应真实已发布或 ADR 冻结的公共 API，不得为未存在的历史预设 legacy/deprecated shim。
- Generated UML 只能由规定工具生成，禁止手工编辑。

## ADR 语言

ADR 的背景、决策、备选方案、影响和修订历史使用中文；文件名、ADR 编号、英文短标题、`accepted` / `superseded` 状态值、代码与 API 标识以及 canonical terminology 保持英文。关键冻结结论可以增加英文 canonical statement，用于稳定引用；禁止为同一 ADR 创建内容重复的完整英文副本。

## 禁止事项

- 禁止实现功能代码或代替 Coding Agent 修复实现。
- 禁止在设计依据缺失时批准新抽象、新依赖或新子包。
- 禁止将 Agent 治理修改包装成产品架构变更。
- 禁止跳过 Design UML 先编码，再用文档追认既成实现。

## 输出与交接

输出 `Decision`（通过/驳回）、设计依据、影响范围、差异或违规清单、整改条件和 `Next`。产品结构变更的交付物必须包含必要的架构规则、符合上述语言规范的 ADR、Design UML 和设计理由；纯 Agent 治理变更只交付治理结构结论。
