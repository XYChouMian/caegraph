# CAEGraph

**连接 CAE 仿真与 Physics AI 的工作流框架。**

CAEGraph 将工程真源转换为 PyG 原生图表示，支持面向工程问题的 GNN 训练、
新网格神经仿真以及实验数据同化。

```
CAE 数据 → 图表示 → GNN 训练 → 新网格神经仿真 → 实验数据同化
```

!!! note "项目状态"

    CAEGraph 已进入 **Phase 1（核心数据结构）**。Phase 0 的包骨架、架构规范、
    UML 体系、文档与 CI 已完成；核心共享抽象正在实现中，CAE/GNN 算法仍为规划功能。

## 快速开始

```bash
pip install -e .
```

```python
import caegraph
print(caegraph.__version__)
```

## 下一步

- [架构总览](architecture/overview.md)
- [API 参考](api/index.md)
- [教程](tutorials/index.md)
- [示例](examples/index.md)
