# architecture/perf — 性能实验证据归档（archive，非生效规范）

> **本目录是 evidence/archive 性质**：存放已关闭性能实验线的 benchmark 方法资产与证据报告。它**不是生效架构规范，不构成 ADR**，与 `architecture/decisions/` 的 ADR 体系没有任何状态关系；任何规范引用请以 ADR 与 `ARCHITECTURE.md` 为准，勿引用本目录。目录内 Python 文件是归档的 benchmark 脚本（不参与 pytest/black/ruff/mypy 门禁，不属生产代码）。

## 内容

- `P2-PERF-01a-evidence.md` — N1（`_expand_edges` NumPy 向量化实验）完整证据：SHA 链、门禁、benchmark before/after、oracle 方法、结论与局限。
- `bench_caegraph_edges.py` — benchmark 脚本（方法资产，归档副本；运行时以 `/tmp` 副本执行，不入仓库运行）。
- `P2-PERF-02-reassessment.md` — P2-PERF-02 三条件重估证据与 PM 裁决（GO 02a）：First E2E / N1 / cProfile 三组证据、GmshLoader tottime 分层归因、02a-1/2/3 批次与 memory-bounded 约束、迁自 ROADMAP 的约束记录。
- `reassess_loader_profile.py` — GmshLoader cProfile 归因 reproduction artifact（仅经 `GmshLoader()(path)` public entry 运行；非生产代码）。

## benchmark 使用方法

```bash
# 1. 导出目标代码树（禁止信任就地检出）
git archive <tip-sha> | tar -x -C /tmp/rev-<name>

# 2. 运行（第一个参数是目标树根目录；脚本会把 <root>/src 前插到 sys.path，
#    并打印实际 imported builder 路径——防止环境 editable 安装劫持到其他 checkout）
python /tmp/bench_caegraph_edges.py /tmp/rev-<name> [repeats]
```

输出分项：candidate generation（旧算法 replica = 顺序循环 + set；新算法 replica = 向量化 gather + canonicalize + filter）、dedup+sort（旧 = `sorted(set)`；新 = int64 key `np.unique`）、`_expand_edges` total（被测树的真实实现）、builder total、观察项（`validate()` / `to_pyg_data` / peak memory，tracemalloc）。

## oracle 等价测试方法

`tests/graph/test_edge_expand_equivalence.py` 范式：在 tests 内维护一份纯 Python reference oracle（历史顺序语义），对同一 Mesh 输入断言 new == oracle；覆盖 empty / 各 CellType / 同 topo_dim 的 2D 与 3D mixed / 非连续存储 / 全退化输入 / 反转节点序 / 随机标签置换 / deterministic ordering。该范式可复用于后续任何性能重构（含未来 P2-PERF-02a 若重启）。

## 局限声明

N1 全部结果来自 synthetic 结构网格 benchmark，仅证明局部热路径的可行加速；**不足以单独授权宏观 NumPy 重构**。P2-PERF-02 重估结论、批次路线与约束见 `P2-PERF-02-reassessment.md`。
