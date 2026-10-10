# P2-PERF-02a-1 Phase 0 evidence — Source→Mesh characterization oracle + before baseline

> 性能实验证据（archive，非生效规范）。本目录性质见 `README.md`；规范以 ADR 与 `ARCHITECTURE.md` 为准。基线代码状态：`feature/perf-02a-1` 分支点 `main @ 631e2ef`（ADR-025 已 accepted，02a 实现未开始，`src/` 与 main 逐字节一致）。

- 测量日期：2026-10-10（系统时钟确认，22:30 CST）
- 边界：唯一公开入口 `GmshLoader()(path)` 调用开始 → `Mesh` 返回结束（含 pipeline 内部 `validate()`；dispatch §4 主验收口径）
- 环境：WSL2（Linux 5.15.167.4-microsoft-standard-WSL2）、AMD Ryzen 9 7950X（12 vCPU 可见）、conda `caegraph-dev`：Python 3.10.21 / NumPy 2.2.6 / meshio 5.3.5

## 1. Characterization oracle（`tests/io/test_gmsh_characterization.py`）

`old implementation == oracle` 证明：新模块 6/6 测试首跑通过（当前旧实现），且全量 pytest 见 §4。

覆盖清单（四 fixture，全部手推期望值、meshio gmsh 2.2 ASCII 运行时生成、仅走公开 API）：

| fixture | 覆盖 |
| --- | --- |
| dual-TET4（主） | cross-block canonical cell IDs、exact CSR（cells/offsets/types）、4 声明 facet canonical winding-free 序、`facet_cells`（interface `(0,1)` 双 owner + 外表面单 owner）、`domain_groups`/`boundary_source_groups` 精确 ID、并集 == `range(n_facets)`、`source_format`、dim-1 `axis` 组诊断（UserWarning + 排除 + 缺席）、winding 反转变体公开表全等 |
| dual-QUAD4 | QUAD4 边 facet namespace（LINE2 canonical）、interface 边 `facet_cells (0,1)`、topo_dim==2、groups |
| dual-HEX8 | HEX8 面 facet namespace（QUAD4 canonical，旋转+反转 lex-min）、共享面 interface `(0,1)`、groups |
| PYRA5+WEDGE6 | 同 topo_dim 混合 cell types、异构 `facet_types`（TRI3/QUAD4 混排）、两族 face-template 匹配、跨 facet 类型的单 boundary group |

覆盖审计结论（补充点 1）：现有 tests 已充分覆盖 TRI3 2D 精确语义、LINE2 winding、TET4 node-set 语义、dense-ID 不变量、lower-dim 诊断、拒绝行为与 meshio 隔离（`tests/io/test_gmsh_loader.py`、`tests/io/test_validation_representative.py`）——本批不重复；缺口为 QUAD4/PYR5/WEDGE6/HEX8 的 facet 表语义与 3D interface 精确冻结，由上表补齐。LINE2 作 1D topo 网格无需新增（1D 无可表示 facet namespace，POINT 不在词汇表，`celltype.py:127-131`；现有类型映射测试足够）。

未冻结（禁止 Phase 1 反向冻结，测试 docstring 已声明）：`_NormalizedSource`/`_SourceBlock`、内部容器/shape/layout、normalization 内部步骤、raw physical-tag 表示、warning 文本、mesh name 派生、声明非法 facet 时的 KeyError（记录在案的 backlog）。

## 2. 浮点 tolerance（提案，待 PM 放行后冻结）

- 实测：meshio gmsh22 写坐标格式为 `.16e`（`_gmsh22.py:265`）= 小数点后 16 位 + 前 1 位 = **17 位有效数字**，满足 float64 精确往返；binary-exact 与 π/1/3 等非二进制探针实测往返误差均为 **0.0**（2026-10-10，本环境）。
- loader 对坐标纯 pass-through（仅 2D→3D 零填充），无算术。
- 提案：`np.allclose(rtol=1e-15, atol=1e-15)` —— 纯保护带（实测误差 0.0，`.16e` 舍入上界 ~5e-16 的 ~2× 余量）。Phase 1 必须原样复用，不得放宽。

## 3. Before baseline（现场复测）

Workload：归档生成器 `build_grid_file` 逐字复刻（`reassess_loader_profile.py:38-80`），Kuhn 6-tet 单位网格、skin 三角形仅 x=0 面、gmsh 2.2 ASCII、`solid/skin` 组。257k 档为文件化 35³（46,656 nodes / 257,250 tets，与历史内存档同规模同拓扑，经 GmshLoader，PM 已裁决）。测量脚本：`baseline_loader_02a1.py`（树根参数 + import 路径打印防劫持；provenance 确认加载自本 worktree `src/`）。

md5 复现校验：48k `e0fa0c810716aabb0f718248770030bb` == 归档值（历史生成口径复现成立）；12k `064d414086d7847d15328cc38782e561`（size 575,398 B 与 First E2E 归档一致）；257k `1098f4a69d001e717aebb2b60be223d2`（新档，无历史参照）。

| 档 | runtime median（s） | min / max（s） | peak-RSS median（KB） | 各次 / max（KB） |
| --- | --- | --- | --- | --- |
| 12k | 0.144437 | 0.136439 / 0.146631 | 51,740 | 51,660 / 51,740 / 51,756；max 51,756 |
| 48k | 0.576584 | 0.546231 / 0.587335 | 102,740 | 102,740 / 102,604 / 102,868；max 102,868 |
| 257k | 3.573961 | 3.450022 / 3.634706 | 386,540 | 386,540 / 386,628 / 386,504；max 386,628 |

测量协议（Phase 1 必须完全同口径复用）：

- runtime：workload 文件先生成（不计时）→ 弃 1 次 warm-up → 6 次 `time.perf_counter` 计时（≥5，dispatch §4）→ median 主指标。
- peak-RSS：workload 生成在测量 subprocess 启动前完成；每档 3 个 fresh subprocess，子进程仅必要 import + `GmshLoader()(path) → Mesh`，报 `resource.getrusage(RUSAGE_SELF).ru_maxrss`（进程级，Linux KB，含解释器与 import 常驻；最小化 env 仅 `PYTHONPATH`）；median 主比较，各次与 max 同时呈报。

旧归档数字仅参考、不构成本批 baseline：First E2E 48k 链路总耗时 1.515 s（含 builder/graph/adapter，非 loader 单边界）、load 分量 0.915 s（2026-10-09，不同日条件）；N1 257k 为内存直构 builder 口径，与 loader 边界不可比。

## 4. 验证

- 新 oracle 模块：`pytest tests/io/test_gmsh_characterization.py` — 6 passed（2026-10-10）。
- 完整门禁（命中 `tests/`，git skill 验证矩阵，2026-10-10 全部通过）：`black --check src tests`（57 files unchanged）、`ruff check src tests`（All checks passed）、`mypy src`（Success: no issues found in 33 source files）、完整 `pytest`（**394 passed**, 1 个既有 torch FutureWarning）。
