# ADR-013: meshio 作为外部 IO 引擎

- 编号：ADR-013
- 标题：io 层**暂定**采用 meshio 作为外部 IO 引擎（gmsh 首发、VTK 写回），
  主依赖、懒加载、类型不渗出公共 API；**不冻结，引擎在读取钩子后面
  可整体替换**（换用触发条件见决策第 6 条）
- 日期：2026-09-06（同日返工：由冻结改为暂定，见决策第 6 条）
- 状态：accepted（provisional——暂定采用，非冻结选型）
- 关联：ADR-008（定位冻结）、ADR-012（物理组语义契约）、Phase 2、
  Design UML `class_diagram.puml`（MeshLoader/MeshWriter）

## 背景（Context）

Phase 2 要求 gmsh 首发（.msh 物理组 → 区域体系，ADR-012）与 VTK 写回
（ParaView 生态）。候选路径：gmsh 官方 SDK、meshio、自研解析器。这是
依赖选型 + 定位声明双决策，需 Architecture 评审后经依赖变更工作流落地
（ADR-003 声明文件纪律）。

## 决策（Decision）

1. **采用 meshio** 作为 `caegraph.io` 的共享外部 IO 引擎：
   - 读端：.msh（含 `field_data` 物理组名↔tag 映射、cell physical tags）；
   - 写端：VTK 系格式（覆盖 Phase 2 写回与 Phase 4 预测场导出）；
   - 未来 Fluent / Abaqus / OpenFOAM 等格式经同一 core registry 接入，
     meshio 提供多格式底座。
2. **定位声明（不随引擎更替而变）**：无论当前引擎是什么，它都是
   **external IO engine**（io 层实现细节）——
   - 不是 CAEGraph 的 Mesh 领域抽象（domain truth 在 `caegraph.core`）；
   - 不是 solver interface / trainer / 图后端替代（不触发 ADR-008 冻结
     条款）；
   - 引入它不构成 solver 抽象化，仅为 io 层的格式编解码引擎。
3. **类型不渗出**：公共 API 的加载入口返回 `caegraph.core.Mesh`，
   meshio 类型（`meshio.Mesh` 等）不得出现在公共签名、返回值或 core 层；
   仅限 `caegraph.io` 内部使用。
4. **依赖安置**：进入 `pyproject.toml` 主 `dependencies`（宽松下限
   `meshio>=5.3`，禁止 `==` 锁死），同步 `environment.yml`；
   loader 内**懒 import**（注册时不触发导入，调用时才加载），保持无
   IO 需求场景的导入轻量。
5. 加载器之间互不硬依赖（Phase 2 规则不变）：各格式 loader 独立注册于
   core registry，共享 meshio 引擎不构成 loader 间耦合。
6. **暂定不冻结（provisional）**：ADR-012 的管线抽象使 IO 引擎只在
   `_read` 钩子后面，替换成本被管线隔离。meshio 是当前较优解而非
   最终裁决，出现以下任一情况时提请新 ADR 复评换用：
   - 接入 meshio 支持不佳的格式（解析缺陷/信息丢失/性能不可接受）；
   - 上游维护停滞与格式跟进失效；
   - Phase 2 收尾复评（gmsh 读取 + VTK 写回双端实战检验后）。

## 备选方案（Options considered）

| 方案 | 结论 | 原因 |
| --- | --- | --- |
| gmsh 官方 SDK | 否决 | wheel 重（~100MB 捆绑二进制）；仅服务 gmsh 单格式；读写两端覆盖不如 meshio 经济 |
| meshio（本决策） | 采纳 | 轻量（numpy 系）；读 .msh + 写 VTK 双端一次覆盖；未来格式扩展契合 ADR-008 跨软件定位 |
| 自研 .msh/VTK 解析器 | 否决 | 重复造轮子；msh 4.x 二进制解析维护成本高；格式清单扩张不可持续 |
| meshio 放 optional extra `[io]` | 否决（本轮） | 读网格是 CAE 框架核心能力，默认安装应可用；懒 import 已控制无关场景成本；未来如需瘦身可经新 ADR 调整 |

## 影响（Consequences）

- 依赖变更走 Environment 工作流：`pyproject.toml` + `environment.yml`
  + `pip install -e ".[dev,docs]"` + CI 验证；`requirements-dev.txt`
  不变（非开发工具）。
- `io/gmsh.py` 为 meshio 的消费者：执行 ADR-012 的维度分类契约，
  产出 Region 体系对象；IO 不做任何物理语义推断。
- core / geometry 层永不 import meshio（与 PyG 边界同构的引擎边界）。
- VTK writer（本切片后续）复用同一引擎，无需二次选型。
- 风险：meshio 对 .msh 新版本格式的跟进节奏——缓解：fixture 固定
  msh 2.2 ASCII（测试确定性），运行时以宽松下限跟踪上游。
