# 教程

暂无教程——CAEGraph 处于 Phase 2（CAE 数据管线）。

规划的教程系列（跟随实现阶段推出）：

1. 将 CAE 数据加载为 `Mesh`
2. 用 representation builder 将 `Mesh` 构造为 `CAEGraph`（canonical 领域表示，ADR-015/016）
3. 用 backend adapter 将 `CAEGraph` 转换为 PyG `Data`（ADR-017）
4. 构建带变换与划分的 `CAEDataset`
5. 训练第一个 GNN 代理模型
6. 加入物理信息损失
