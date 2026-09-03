# CAEGraph

**面向 CAE 数据的图计算框架（PyG 风格）。**

CAEGraph 将 CAE 数据结构、网格表示、图表示、数据集与 GNN /
物理信息（physics-informed）学习模型连接为一个整体。

```
CAE 数据 → 网格 → 图 → 数据集 → 模型 → 训练/推理 → 可视化
```

!!! note "项目状态"

    CAEGraph 处于 **Phase 0（基础建设）**。包骨架、架构规范、UML 体系、
    文档与 CI 已就绪，尚未实现任何 CAE/GNN 算法——页面描述的均为规划结构。

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
