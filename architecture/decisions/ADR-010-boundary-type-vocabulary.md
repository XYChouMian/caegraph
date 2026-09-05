# ADR-010: 边界条件词汇精化（数学类别 vs 软件命名）

- 编号：ADR-010
- 标题：BoundaryType 只收录数学边界类别（七值），软件专属命名归入
  BoundaryRegion 元数据；BoundarySpec 增补 paired_region 与 parameters
  设计槽位
- 日期：2026-09-06
- 状态：accepted
- 关联：ADR-007（D4 共享词汇）、ADR-008（跨软件抽象定位）、Phase 1、
  Phase 2、Design UML `class_diagram.puml`

## 背景（Context）

Phase 1 落地的 `BoundaryType` 仅有 DIRICHLET / NEUMANN / FREE 三值，
不足以覆盖 CFD/FEM 工作流中常见的数学边界类别（混合边界、周期配对、
对称面、多域耦合接口）。同时，CAE 软件教程中的 wall/inlet/outlet 等
命名属于工程/应用语义，与数学类别分属两个层次：同一个 "inlet" 在不同
问题中可能对应 Dirichlet 速度、Neumann 质量通量或压力约束。若把软件
命名收进枚举，枚举将随软件清单无限膨胀，且破坏 ADR-008 的跨软件
抽象定位。

## 决策（Decision）

1. `BoundaryType` 只收录**数学边界类别**，共七值：
   - `DIRICHLET`：规定值 u=g
   - `NEUMANN`：规定梯度/通量 du/dn=g
   - `ROBIN`：混合边界 a·u+b·du/dn=g
   - `PERIODIC`：配对区域约束
   - `SYMMETRY`：对称面约束
   - `INTERFACE`：耦合/接口约束（FSI、CHT、多域）
   - `NONE`：被跟踪但无主动约束的区域（取代原 `FREE`，语义不变、
     命名与"自由度/自由表面"歧义消除）
2. **禁止**收录软件专属命名（WALL、INLET、OUTLET、PRESSURE_INLET、
   VELOCITY_INLET、HEAT_FLUX 等）；它们属于 BoundaryRegion 元数据。
3. BoundarySpec（Phase 2 实现）在设计上增补两个槽位：
   - `paired_region: str | None`：PERIODIC 的配对区域
   - `parameters: Mapping[str, Any]`：ROBIN 等的通用参数容器
   （如 h、T_inf），不过度特化。
4. 职责链保持三层：BoundaryRegion（物理/几何位置）→ BoundarySpec
   （用户约束声明）→ BoundaryType（数学类别）。BoundaryType 仍是
   词汇枚举，不是求解器实现、软件适配器或完整边界条件引擎。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| 收录软件命名（WALL/INLET/…） | 否决 | 同名不同义（inlet 可为三种数学类别），枚举随软件清单膨胀，破坏跨软件抽象 |
| 自由字符串标签 | 否决 | 失去封闭词汇的序列化与校验保证，语义漂移不可检测 |
| 七个数学类别 + 区域元数据承载软件命名 | 采纳 | 类别封闭稳定，工程语义开放可扩展，两层职责清晰 |
| 保留 FREE 命名 | 否决 | 与"自由度/自由表面"存在歧义；NONE 与"无主动约束"语义精确对应 |

## 影响（Consequences）

- 公共 API：`BoundaryType.FREE` → `BoundaryType.NONE`（Phase 1 尚未
  发布，无兼容负担）；新增五值进入 `Unreleased`。
- Phase 2 的 BoundarySpec/GraphBuilder/GNN 输入编码以七类为准；
  NodeCategory 不受影响。
- 序列化值保持小写字符串（str-Enum），序列化面仅增不改。
- 本 ADR 不引入新包、不改变 PyG 集成与 Graph 设计（ADR-007/009 不变）。
