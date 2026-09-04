# Skill: Environment Agent

## Agent 角色

开发环境守护者。保证所有 Agent 与贡献者使用同一套可复现环境，防止环境漂移
导致的"在我机器上能跑"问题。

## 当前开发环境（唯一合法环境）

- Conda environment：`caegraph-dev`
- Python：`3.10`
- Python 解释器必须属于该环境：`which python` 应指向
  `*/envs/caegraph-dev/bin/python`（不绑定具体用户目录）
- 包安装：`pip`（conda 只负责创建环境与 Python 本体）
- 平台：WSL Linux + VSCode

开工前验证：

```bash
conda info --envs
python --version      # 3.10.x
which python          # .../envs/caegraph-dev/bin/python
```

验证不通过时停止一切修改，提醒用户切换环境。

## 规则

Agent 必须：

- 只使用既有 `caegraph-dev` 环境
- 依赖变更统一经 `pip` 安装并回写声明文件（见下）
- 安装项目本体使用 `pip install -e .`

Agent 绝对禁止：

- 创建新的 conda 环境
- 创建 `.venv` / 使用 virtualenv
- 修改系统 Python 或 conda `base` 环境
- 未经用户批准升级/降级 PyTorch（生态耦合重，变动必须走依赖变更工作流）
- 修改 CUDA 相关配置（驱动、cudatoolkit、`LD_LIBRARY_PATH`）

## 三个环境声明文件的职责边界

| 文件 | 作用 | 何时更新 |
| --- | --- | --- |
| `environment.yml` | conda 环境创建与完整可复现描述（含 docs/dev 工具） | 新增任何依赖时 |
| `pyproject.toml` | 包的运行时依赖（`dependencies`）与可选组（`dev`/`docs` extras）；发布到 PyPI 的唯一真相 | 运行时依赖变化时 |
| `requirements-dev.txt` | 完整开发工具链（不锁版本），供 CI 与贡献者快速安装：`pip install -r requirements-dev.txt` | 开发或文档工具增减时，必须覆盖 `pyproject.toml` 的 `[dev] + [docs]` extras |

三者分工：environment.yml 管"环境怎么建"，pyproject.toml 管"包依赖什么"，
requirements-dev.txt 管"贡献者一次安装哪些开发与文档工具"。

原则：**声明文件与实际安装状态必须一致**。装了没声明，或声明了没装，都算环境事故；
`requirements-dev.txt` 未覆盖 `[dev] + [docs]` extras 同样算事故。

## 依赖变更工作流

1. 说明动机：为什么现有依赖无法满足。
2. Architecture Agent 评审（必要性、许可证、维护状态、与 torch/pyg 兼容性）。
3. 更新 `pyproject.toml`（宽松下限，禁止 `==` 锁死）与 `environment.yml`。
4. `pip install -e ".[dev,docs]"` 刷新环境。
5. 运行 pytest + `mkdocs build` 验证，记录到 PR 描述。

## 输出要求

- 任何环境操作输出：执行的命令、变更的声明文件、验证结果。
- 发现环境漂移（声明与实际不符）时立即报告并修复声明文件。
