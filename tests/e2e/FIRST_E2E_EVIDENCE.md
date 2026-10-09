# First E2E Smoke Run — Representative-scale Observation Evidence

> **状态声明**：本文件是 Phase 2 First E2E Smoke Run 的观测证据归档（Gate 5 CLOSED 后的系统级验证），**只测不优化**；数字为观察记录，不构成规范，亦不作为 P2-PERF-02 的裁决依据——仅为 PM 重估 trigger ② 的判断输入。

## 1. 链路与口径

完整 public path（真实文件 IO）：

```
Gmsh .msh → GmshLoader → Mesh → MeshRepresentationBuilder → CAEGraph
→ validate() → to_pyg_data → minimal consumer
```

- 计时：`time.perf_counter` wall time，单次运行；计时点全部位于 **public boundary**（`GmshLoader()` / builder 调用 / `validate()` / `to_pyg_data()`），不依赖 protected hooks。
- 内存：`tracemalloc` peak，**独立 pass** 测量（避免 tracing 开销扭曲计时）；peak 为全链（load → to_pyg_data）累计。
- 统计：每档 **3 次重复，全部原始值列出**，median 为主统计，best 仅供 N1 best-of-5 参考。
- 环境：WSL2，conda `caegraph-dev`（Python 3.10.21，meshio 5.3.5，torch 2.14.0+cu130），First E2E 分支树（main `50af723` + 本批测试），纯 Python builder（N1 实验未进 main）。
- 复现：生成与计时脚本见本文件 §4（/tmp 临时脚本，未入仓库）；fixture 为运行时生成的 synthetic gmsh 2.2 ASCII。

## 2. Workload 参数与原始值

| 档位 | 网格 | nodes | tets (cells) | boundary tris | 文件 | source gen（单列） |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 12k | 10×10×20 立方 Kuhn 6-tet | 2 541 | 12 000 | 400 | 561 KiB | 0.060 s |
| 48k | 20×20×20 立方 Kuhn 6-tet | 9 261 | 48 000 | 800 | 2 254 KiB | 0.211 s |

Groups：`solid`（volume，全部 tets）、`skin`（x=0 面 boundary triangles）；node field `p`（builder public write path 挂载，`n_nodes` 长）。

**12k 档原始值（s）**：

| rep | load | build | validate | to_pyg | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.251 | 0.129 | 0.005 | 0.009 | 0.393 |
| 2 | 0.255 | 0.133 | 0.005 | 0.008 | 0.400 |
| 3 | 0.129 | 0.130 | 0.005 | 0.008 | 0.271 |
| **median** | **0.251** | **0.130** | **0.005** | **0.008** | **0.393** |
| best | 0.129 | 0.129 | 0.005 | 0.008 | 0.271 |

peak memory（独立 pass）：**15.4 MB**；Data keys：`edge_index / field_families / node_category / num_nodes / p / pos`。

**48k 档原始值（s）**：

| rep | load | build | validate | to_pyg | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 1.032 | 0.547 | 0.022 | 0.032 | 1.633 |
| 2 | 0.792 | 0.540 | 0.021 | 0.033 | 1.386 |
| 3 | 0.915 | 0.543 | 0.022 | 0.033 | 1.515 |
| **median** | **0.915** | **0.543** | **0.022** | **0.033** | **1.515** |
| best | 0.792 | 0.540 | 0.021 | 0.032 | 1.386 |

peak memory（独立 pass）：**61.6 MB**。

## 3. N1 synthetic ↔ First E2E 对照

| 指标 | N1 synthetic tet36 | First E2E representative-scale |
| --- | ---: | ---: |
| workload / cells | 约 257k | 12k / 48k 实测 |
| builder total | before 3269.3 ms / after 1377.5 ms | median 130 ms（12k）/ 543 ms（48k） |
| validate | 236 ms | median 5 ms（12k）/ 22 ms（48k） |
| to_pyg_data | 294 ms | median 8 ms（12k）/ 33 ms（48k） |
| builder peak memory | 69 MB → 331 MB | 全链 peak 15.4 MB（12k）/ 61.6 MB（48k） |

**不可比性声明（必读）**：

- workload 不同（257k vs 12k/48k tet）、环境可能不同、Python / dependency 版本可能不同；
- N1 是 **isolated synthetic benchmark**（builder 单点、best-of-5、before/after 双树）；
- First E2E 是**完整系统链观测**（含 meshio 解析与文件 IO，且当前 main 的 builder 为纯 Python 实现——N1 的 "after" 实验未进 main）；
- 因此**不得把两列解读为同条件 speedup**，也不得据 cross-scale 外推下性能结论。

## 4. 复现方式

观测脚本（/tmp 临时脚本，未入仓库）核心步骤：① `build_grid_file(path, nx, ny, nz)` 以 Kuhn 6-tet 分解生成结构网格并写 gmsh 2.2 ASCII；② 计时 pass ×3（`GmshLoader()(path)` → builder（含 metadata boundary groups 注册与 node FieldData 挂载）→ `validate()` → `to_pyg_data`）；③ 内存 pass ×1（`tracemalloc`）。输出格式同 §2。

## 5. 观察记录（只测不优化）

- `GmshLoader total`（meshio 解析 + 文件 IO）为最大热点：约占总 E2E 的 60–65%（12k：0.251/0.393；48k：0.915/1.515）。
- builder 次之（约 33–36%）；`validate()` 与 `to_pyg_data` 在本规模合计 < 3%。
- scaling（12k → 48k，4×）近似线性：total 0.393 → 1.515（≈3.9×）。
- P2-PERF-02 trigger ①（首次 E2E）已满足；本节数字仅为 trigger ② 的 PM 判断输入——**Builder 不自行宣布 trigger ② 满足，亦不启动 02a / 02b**。
