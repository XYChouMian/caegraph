# P2-PERF-01a — N1 实验证据归档（archive / evidence，非生效规范）

> **状态声明**：本文件是 P2-PERF-01a（N1）实验线关闭时的证据归档，**不是 ADR，不构成任何生效架构规范**，与 `architecture/decisions/` 的 ADR 体系无状态关系，不得作为规范依据引用。N1 为**实验性性能验证**：其实现在 `perf/numpy-*` 分支上完成并合并到实验 integration 分支，**未进入 `main`，未来不作为 implementation baseline**。归档后实验分支已按 PM 裁决删除（不留 tag / patch / 可达性），本文与其同目录的 benchmark 脚本是该实验仅存的正式成果。

## 1. 任务与前置核验

- 任务：`MeshRepresentationBuilder._expand_edges` NumPy 向量化（candidate generation / canonicalization / dedup / ordering），领域语义与 public contract 不变。
- 派单时 main = `721e256`；开工核验：`git log --oneline 721e256..8f3c647` 共 4 个提交（`a8b5700` 治理约束、`43e4050` 图示命名对齐、`e5f8343` / `8f3c647` 两个合并），`git merge-base --is-ancestor e5f8343 8f3c647` exit 0。
- **base 区间取证**：`a8b5700 arch(agent): constrain ADR content scope` 仅改 `.agent/` 3 个 SKILL（+9/−1）；`8f3c647` 为合并 `e5f8343`（gate 5 batch 1 命名对齐）与 `a8b5700` 的 merge commit。区间内无 `src/` 生产语义变更。

## 2. SHA 链

| 角色 | SHA |
| --- | --- |
| main（开工 / 合入时，未移动） | `8f3c647` |
| child base = integration base | `8f3c647` |
| child `perf/numpy-edge-expand` tip | `a7087a9`（`perf(graph): vectorize _expand_edges candidate generation and dedup`） |
| integration `perf/numpy-main` merge | `b4065cb`（`--no-ff`，`merge: numpy edge expansion (P2-PERF-01a)`） |
| benchmark before 基准树 | `/tmp/rev-perf-base`（`git archive 8f3c647` 导出，sha256 逐文件对齐） |

## 3. 九项门禁结果（合入前，全部通过）

1. 全量 pytest：base 实测 baseline **357 passed** → child **373 passed**（+16 = 新增 oracle 等价测试数，漂移可解释）；integration 合并后复验 373 passed。
2. `mkdocs build --strict`：通过（`--site-dir /tmp`）。
3. `black --check src tests` / `ruff check src tests` / `mypy src`（30 files）：全部通过（black 初检两文件需重排，已格式化后复检通过）。
4. oracle 等价测试 16/16。
5. benchmark before/after（见 §4）。
6. `git diff --check`：clean。
7. diff scope audit：仅 `src/caegraph/graph/builder.py` + 新测试文件。
8. Gate 5 零触碰：`git diff main --name-only -- src/caegraph/io docs architecture/decisions diagrams pyproject.toml requirements-dev.txt environment.yml .agent` = **0 文件**（当时 main 尚无 io 实现）。
9. public contract unchanged：`CAEGraph.edges` tuple 契约与 builder 返回类型相关既有测试零改动且全绿。

## 4. benchmark（synthetic，/tmp 脚本，方法见同目录 README）

环境：WSL2，caegraph-dev（Python 3.10.21），best-of-5。before 树 = `8f3c647` archive 导出；after 树 = child worktree。两轮均打印 imported builder 路径取证（防 editable 安装劫持——环境 editable 指向 `caegraph-opencode/src`，已用 pytest `pythonpath=["src"]` 与显式 `sys.path` 双重规避）。

| metric (`_expand_edges`) | before | after | speedup |
| --- | ---: | ---: | ---: |
| tet 12³（8.0k cells） | 68.7 ms | 6.8 ms | 10.1× |
| tet 24³（73k cells） | 694.0 ms | 85.9 ms | 8.1× |
| tet 36³（257k cells） | 2603.4 ms | 609.2 ms | 4.3× |
| tri 120×120（28.8k cells） | 166.4 ms | 22.7 ms | 7.3× |
| mixed 120×120（21.6k cells） | 132.8 ms | 16.2 ms | 8.2× |
| builder total（tet 36³） | 3269.3 ms | 1377.5 ms | 2.4× |

分项（tet 36³）：candidate generation 2433→87 ms；dedup+sort 230→167 ms。

观察项（未优化、如实记录）：`validate()` 236 ms / `to_pyg_data` 294 ms（tet36）；**peak memory 上升**（tet36 builder 69 MB → 331 MB，物化候选数组所致）。

去重选型：`np.unique(axis=0)`（void 行排序）在 tet36 需 1990 ms，是初版瓶颈；int64 key（`u*n_nodes+v`）165.9 ms，与 `np.unique(axis=0)`、lexsort 两方案结果逐元素比对一致后采用；溢出边界：key < n_nodes²，n_nodes < 2³¹ 时 key < 2⁶²，安全，超界回退 axis=0。

## 5. oracle 等价测试方法与覆盖

`tests/graph/test_edge_expand_equivalence.py`（16 例）：纯 Python reference oracle 表达历史顺序语义（canonical `(min,max)`、退化对丢弃、全局去重、字典序），逐例断言 new == oracle。覆盖：empty（`n_cells==0` 守卫，duck-type 桩——Mesh 层禁止零 cell 表）、LINE2（含反向对）、TRI3 / QUAD4 / TET4 / PYR5 / WEDGE6 / HEX8、2D mixed（TRI3+QUAD4 共享边，同 topo_dim）、3D mixed（TET4+PYR5+WEDGE6+HEX8，同 topo_dim）、共享 face 重复候选去重、同类型 cell 非连续存储、候选全退化安全返回 `()`、节点序反转（仅 new==oracle）、deterministic ordering + 无双向重复、5 组 seeded 随机标签置换、12×12 网格。既有 public expectation 测试零改动。

## 6. 结论与局限

- **结论**：`_expand_edges` 热路径向量化在 synthetic 负载上取得 4.3–10.1× 局部加速、builder total 约 2.4×；语义等价与 public contract 不变均由测试与 diff 取证支撑。
- **局限**：① 全部负载为 synthetic 结构网格，不代表真实 CAE 规模与形态；② peak memory 恶化未解决；③ 加速仅覆盖 builder 单点，`validate()` / `to_pyg_data` / Mesh 内部热点未动；④ 因此 **synthetic 结果不足以单独授权宏观 NumPy 重构**——P2-PERF-02 已转入 HOLD，重启条件见 `ROADMAP.md` Phase 2 小节（首次 E2E + 真实规模 workload 证据 + 下游未大规模依赖具体 container 表示，三者同时满足）。
- 后续候选（仅备案，未启动）：P2-PERF-02a（内部 NumPy-first 表示，原则上不 BREAKING）、P2-PERF-02b（public ndarray 契约，独立决策）。
