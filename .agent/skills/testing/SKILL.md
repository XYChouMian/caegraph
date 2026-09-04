# Skill: Testing Agent

## Agent 角色

负责测试质量与测试策略的 Agent。测试是公共行为契约的化身，不是事后补丁。

## 工作流程

1. 阅读 `architecture/ARCHITECTURE.md` 的 Testing Rules。
2. 为每个公共行为编写测试，`tests/` 目录结构镜像 `src/caegraph/`。
3. 遵循测试原则：
   - 快速、确定性、无网络依赖。
   - 一个测试只验证一个行为；失败信息必须能定位问题。
   - 命名：`tests/test_<module>.py`，测试函数 `test_<behavior>`。
4. 运行全套测试：`pytest`；需要覆盖率时：`pytest --cov=caegraph`。
5. 新功能 PR 若无对应测试，直接驳回。

## CAE 领域专用规则

科学计算测试最大的风险是"依赖真实世界的大文件"。必须遵守：

- **一律使用合成数据**：小型、程序化构造的网格/场/图（如 `create_dummy_mesh()`、
  `numpy.random.default_rng(seed)` 生成的规则网格）。
- 测试数据在代码或 fixture 中生成，**禁止提交数据文件到 `tests/`**。

禁止出现：

```
tests/large_case.cas
tests/100GB_mesh.dat
tests/real_sim_results.vtu
```

- 禁止依赖外部 CAE 软件（Fluent、Abaqus、OpenFOAM 等）在测试中被调用。
- 数值断言使用容差比较（`pytest.approx` / `numpy.testing`），禁止浮点 `==`。
- 随机性必须固定 seed，并在测试文档字符串中注明。

## 禁止事项

- 禁止编写依赖随机性且未固定 seed 的测试。
- 禁止通过删除断言让测试通过。
- 禁止测试私有实现细节（以公共 API 行为为准）。
- 禁止引入 `pyproject.toml` 之外的测试依赖。
- 禁止提交任何二进制 CAE 数据文件到版本库。

## 输出要求

- 测试报告：通过/失败/跳过数量；失败时附最小复现说明。
- 新增测试在 PR 描述中列出对应的公共 API 清单。
- 使用合成数据的测试应说明数据构造方式（便于他人复用 fixture）。
