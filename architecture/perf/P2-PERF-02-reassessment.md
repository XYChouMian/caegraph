# P2-PERF-02 Reassessment — 证据归档（archive / evidence，非生效规范）

> **状态声明**：本文件是 P2-PERF-02 三条件重估的证据归档（First E2E 之后的只读性能归因），**不是 ADR，不构成任何生效架构规范**，与 `architecture/decisions/` 的 ADR 体系无状态关系。它记录 PM 的 02a 启动裁决与其证据链；02a 的实现约束以 PM 派单为准。同目录 `reassess_loader_profile.py` 为 reproduction artifact（非生产代码）。

## 1. 三组证据的环境与方法

| 证据 | 环境 | 方法 |
| --- | --- | --- |
| **A. First E2E**（48k：total 1.515 s / loader 0.915 s / build 0.543 s / validate 0.022 s / to_pyg 0.033 s） | WSL2，caegraph-dev（Python 3.10.21，meshio 5.3.5，torch 2.14.0+cu130） | 完整系统链 wall time（`time.perf_counter`），计时点全部位于 public boundary；12k/48k 两档 ×3，median 为主（`tests/e2e/FIRST_E2E_EVIDENCE.md`） |
| **B. N1**（`_expand_edges` 4.3–10.1×、builder total ≈2.4×、peak 69→331 MB） | 同上 | isolated synthetic benchmark（builder 单点、best-of-5、before/after 双树；`P2-PERF-01a-evidence.md`） |
| **C. cProfile 归因**（本文件 §2–§3） | 同上；profiler 采集与 wall time 非同一统计口径，仅用于相对耗时归因 | 48k workload，warm 一次后 `cProfile` 唯一公共入口 `GmshLoader()(path)`；protected hooks 仅被 profiler 观察内部调用栈，未被脚本直接调用 |

## 2. cProfile 归因（tottime self-time 分层；桶总和 = 100% of 0.915 s，无重复累计）

归因口径：**tottime（self time）分层聚合**——self time 天然不计入子调用，桶总和恰为 profiled CPU 总量；父子 inclusive cumtime 仅并列展示供调用树阅读，**绝不求和入桶**，杜绝 nested cumtime 重复累计（桶占比 ≤100%，实测恰 100%）。

| 桶 | self-time | 占比 |
| --- | ---: | ---: |
| **canonical construction**（`io/base.py _build_topology` + `Mesh.__init__` / `canonical_facet_nodes` 等） | 0.452 s | **49.4%** |
| meshio parse（外部引擎，self） | 0.167 s | 18.2% |
| python runtime / builtins / other（dict.setdefault 768k 次、list.append 487k 次、str.split、readline 等——大部分服务于前两桶的逐元素循环，但缺少 per-caller 强归属证据，作未强归属成本保留） | 0.166 s | 18.2% |
| **caegraph io normalization**（`gmsh.py` 连接性逐节点 int 转换等） | 0.105 s | **11.5%** |
| Mesh.validate（self；两次调用：构造期 BaseObject 生命周期 + 管线步骤④显式；inclusive cumtime 合计 0.125 s） | 0.023 s | 2.6% |
| numpy C ops | 0.002 s | 0.2% |
| **TOTAL** | **0.915 s** | 100.0% |

**直接可归属合计**：canonical construction（49.4%）+ normalization（11.5%）≈ **60.9%**——这是有 per-caller 证据支撑的 CAEGraph 自有 Python 成本下限。

**cumtime 调用树对照（inclusive，只读、从未求和）**：`__call__` 0.915 → `_build_topology` 0.518（self 0.286，单点最大）→ `Mesh.__init__` 0.077；`_load_source` 0.220 → meshio `read` 0.220（`_read_cells_ascii` 0.170）；`_normalize_source` 0.107；`validate`×2 0.125。

## 3. 归因争议记录

分析过程中曾使用「**65–75% 自有 Python**」的宽口径表述（把部分 builtins/runtime 成本按调用意图并入自有路径）。复核后认定其中部分 builtins 缺少 per-caller 归属证据，故正式主张**收缩为 60.9%**（仅保留有直接归属证据的两桶）；builtins/runtime 的 18.2% 作为未强归属成本单列保留。两种口径均支持 GO（见 §5），因此不为该争议追加测量。

## 4. meshio 外部解析与 CAEGraph 自有路径的区分

- **外部（meshio，provisional engine，ADR-013）**：`meshio.parse` self 18.2% / inclusive 24.0%——属外部引擎实现，不在 CAEGraph 优化范围内；引擎替换触发条件见 ADR-013 决策 6。
- **自有（CAEGraph Python）**：normalization 11.5% + canonical construction 49.4% ≈ **60.9% 直接可归属**，另有部分未强归属 builtins 服务于这些路径——逐元素 Python 循环（每实体连接性转换、face_cells 逐 face 节点集匹配、builder candidate 生成）是真实的自有成本主体。

## 5. 三条件重估与 PM 最终裁决

| 条件 | 评估 |
| --- | --- |
| ① 首次 E2E 成功 | 满足（388 passed；全链语义验证 + 12k/48k 两档观测） |
| ② 真实 workload 证明 Python-container / canonical construction 路径为值得处理的瓶颈 | 满足（§2：60.9% 直接可归属自有成本；N1 已在同型循环证明 4.3–10.1× 向量化空间；validate / to_pyg_data 被证明非瓶颈） |
| ③ Gate 6 未扩张，低成本重构窗口仍开 | 满足（transforms / dataset 仍空；First E2E consumer 仅依赖 public tensor ops） |

**PM 最终裁决**：`GO P2-PERF-02a — internal, non-BREAKING, memory-bounded`

- **02a-1**（P0）：loader `_build_topology`——canonical assembly 逐元素循环（facet 候选匹配 / face_cells 邻接构建）NumPy-first 向量化；
- **02a-2**：builder `_expand_edges`（N1 已证 4.3–10.1×；oracle 等价测试纪律沿 N1 先行）；
- **02a-3**：normalization 连接性转换——**仅在 02a-2 后 re-profile 仍证明其显著时授权**；
- **02b**（public ndarray contract）：继续独立 HOLD；
- **不属于 02a**：meshio 外部引擎、validate contract（管线步骤④为 ADR-012 契约）、`to_pyg_data`、Gate 6；
- **memory-bounded 约束**：实现须在 12k / 48k / 257k 三档报告 tracemalloc peak 并对照 pre-02a 基线，**峰值 > 2× 基线即否决（与速度无关）**；优先 chunked / streaming，禁止整候选数组无界物化（N1 331 MB 根因）；
- **non-BREAKING**：public contracts（`CAEGraph.edges` tuple、accessor 视图、`Mesh` 只读面、`GmshLoader.__call__` 签名）零变化；oracle 等价纪律扩展至 02a-1。

## 6. 与 N1 evidence 的关系

本文件与 `P2-PERF-01a-evidence.md` 平行：N1 记录 builder 单点实验（未进 main），本文件记录 First E2E 后的全链归因与 02a 裁决；两者均为 evidence archive，**不是 ADR**，不得作为规范依据引用。

## 7. 迁移约束记录（2026-10-10，自 ROADMAP Phase 2 小节收敛迁入）

以下内容原存放于 `ROADMAP.md` Performance line（已按 strategy-layer 精简原则收缩），约束效力不变、落点改为本归档：

- **三条件重估 trigger 原文**（GO 裁决的历史依据；「all three must hold」）：① first E2E succeeded with a trustworthy behavioral baseline；② a representative real-scale workload demonstrates a perceptible time or memory bottleneck in the current Python-container paths（synthetic benchmarks alone do not satisfy this）；③ downstream（Gate 6 / Dataset / Transforms）has not yet come to depend on the concrete container representation。否则维持 HOLD；re-evaluation may happen after each gate but must never block the critical path。
- **02a 完整范围枚举**（internal NumPy-first representation，in principle without requiring a BREAKING public API）：`_edges` ndarray、`_facet_cells` CSR、builder vectorization、relation normalization / validation vectorization、Mesh hot-path vectorization。§5 的 02a-1/2/3 批次为其执行切分。
- **02b 独立性**：public ndarray contract（`CAEGraph.edges`、`facet_adjacent_cells` 及其他 public numerical collections）为 independent decision；**not starting 02b is a legal final outcome**；ADR-025 未创建，重构窗口重开时从届时 latest main + E2E / workload 证据起草。
- **存储表示依赖禁令（HOLD 期间纪律，02a 落地前持续有效）**：新代码必须只依赖语义与 public APIs——永不依赖 `_edges` / `_facet_cells` 等存储表示。
