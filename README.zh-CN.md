# CAEGraph

[English](README.md) | 简体中文

面向 PyG 生态的 CAE → Physics AI 工作流框架。

CAEGraph 打通 **CAE 数据 → canonical 图表示 → GNN 训练 → 跨离散神经仿真 → 实验数据同化**。它将异构 CAE 数据源规范化为 **CAEGraph**——graph-native 的 canonical 领域表示（ADR-015），并通过 backend adapter 对接学习后端（当前为 PyTorch Geometric），保持工程真值与框架无关。

> **状态：Pre-Alpha（Phase 2 — CAE 数据管线，进行中）。** Phase 0（地基）与 Phase 1（核心词汇：`BaseObject`、注册表、共享枚举、日志）已完成。架构基线为 ADR-015~019（CAEGraph 为 canonical 领域表示；topology subsystem、构造、后端适配、领域组成与实体/关系模型契约）。Coding gate 1–3 与 mesh representation builder 已落地：CAEGraph 领域核心（`CAEGraph`、`Field`、boundary 词汇）、topology subsystem（`Mesh`、`CellType`）以及带 NodeCategory 推导的 node-graph 构造（`caegraph.graph.MeshRepresentationBuilder`）。其余数据带（loaders、backend adapter、transforms、dataset）实现中；GNN 训练能力仍为规划功能。

## 功能（规划中）

- **CAE 数据带** — CAEGraph canonical 表示，含 topology（cell-based 的 Mesh）、Field 与 boundary 词汇；loaders、geometry 服务、表示构造（mesh / grid / particles）、backend adapter（PyG）、transforms 与 datasets
- **Physics AI 工具** — physics 损失、观测同化与 CAE 感知的训练工作流组件，不取代用户自己的训练循环
- **神经仿真** — 预训练模型跨离散运行、场重建与 VTK 写回
- 基于 [PyTorch](https://pytorch.org) 与 [PyTorch Geometric](https://pyg.org) 构建，不引入替代性 graph backend、Trainer 或 solver 抽象

## 安装

CAEGraph 要求 Python 3.10 或更高版本。规范开发环境使用 Python 3.10，CI 同时验证 Python 3.11 兼容性。

```bash
pip install -e .
```

开发环境（文档、测试、lint）：

```bash
pip install -e ".[dev,docs]"
```

## 快速开始

```python
import caegraph

print(caegraph.__version__)
```

## 项目结构

```
caegraph/
├── src/caegraph/        # 源码（src-layout）
├── tests/               # pytest 测试套件
├── docs/                # MkDocs 文档站
├── architecture/        # 架构规范 + Design UML
├── diagrams/generated/  # 由代码生成的 UML
├── .agent/skills/       # agent 开发标准
└── .github/workflows/   # CI
```

## 开发原则

每一次贡献必须保持七者一致：

```
Code ⇔ Architecture ⇔ UML ⇔ Documentation ⇔ Testing ⇔ Environment ⇔ Release
```

详见 [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)。

## 许可证

Apache License 2.0 —— 见 [LICENSE](LICENSE)。
