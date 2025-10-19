# 发布到 PyPI 指南

本指南说明如何将 `compute-god` 发布到 [PyPI](https://pypi.org/project/compute-god/) 与 [TestPyPI](https://test.pypi.org/project/compute-god/)。

## 先决条件

- 拥有 PyPI 与 TestPyPI 账号，并创建 **API Token**。
  - PyPI: 进入 `Account settings` → `API tokens` → 新建 *Scoped API token*，作用域至少包含项目 `compute-god`。
  - TestPyPI: 同上，生成对应的测试令牌。
- 本地已经安装 [uv](https://github.com/astral-sh/uv)（推荐）或任意兼容的 Python 3.11 环境。
- 仓库工作区干净（没有未提交的改动）。

> **提示**：使用 GitHub Actions 的 "trusted publishing" 无需把 PyPI 凭证存入仓库，只要在 PyPI 端授权 GitHub 仓库即可。详见下文自动化章节。

## 步骤 1：更新版本号

1. 编辑 [`pyproject.toml`](../pyproject.toml)，把 `[project]` 下的 `version` 更新为将要发布的版本。
2. 同步更新任意需要记录版本的文档（如 `docs/TODO.md`）。
3. 提交更改并打上对应的 Git 标签，例如：

   ```bash
   git commit -am "release: v0.2.0"
   git tag v0.2.0
   ```

## 步骤 2：本地检查

1. 安装依赖并运行测试：

   ```bash
   uv sync
   uv run pytest
   ```

2. 构建分发包并执行元数据检查：

   ```bash
   uv run python -m build
   uv run twine check dist/*
   ```

   如果没有安装 `twine`，可通过 `uv pip install twine` 安装。

## 步骤 3：上传到 TestPyPI（可选但推荐）

1. 将刚才生成的分发包上传到 TestPyPI：

   ```bash
   uv run twine upload --repository testpypi dist/*
   ```

2. 使用临时虚拟环境验证安装：

   ```bash
   uv venv --seed
   source .venv/bin/activate
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple compute-god==<version>
   compute-god --help
   deactivate
   ```

## 步骤 4：正式发布到 PyPI

1. 上传正式包：

   ```bash
   uv run twine upload dist/*
   ```

2. 在项目页面确认最新版本已经上线。

## 自动化发布（GitHub Releases）

仓库内的 [`python-publish.yml`](../.github/workflows/python-publish.yml) workflow 支持 **Trusted Publishing**：

1. 在 PyPI 项目的 `Publishing` 设置中添加当前 GitHub 仓库为 trusted publisher。
2. 在 GitHub 上创建新的 Release（`Draft a new release`），tag 需与版本号一致（如 `v0.2.0`）。
3. Release 发布后，workflow 会自动：
   - 使用 `uv sync --dev` 拉取依赖，并运行 `ruff`、`mypy` 与 `pytest` 做质量检查；
   - 在干净环境中执行 `uv run python -m build` 构建分发包；
   - 将 `dist/` 中的制品上传为 release artifact；
   - 通过 OpenID Connect 与 PyPI 建立信任并上传分发包。

> 若想在自动化流程中加入额外校验（例如运行 `pytest` 或 `ruff`），可编辑 workflow 添加步骤。确保这些检查在构建分发包之前执行。

## 常见问题

- **上传失败：`HTTPError: 403`** – 确认版本号未在 PyPI 上存在；PyPI 不允许覆盖已发布的版本。
- **`twine check` 报告缺少长描述** – 确认 `README.md` 已通过 `readme = "README.md"` 在 `pyproject.toml` 中声明，并使用 UTF-8 编码。
- **GitHub Release 成功但 PyPI 没有更新** – 检查 workflow 日志，确认 PyPI trusted publisher 设置正确，并且 release tag 与 `pyproject.toml` 中的版本一致。

按照以上步骤即可将 `compute-god` 安全地发布到 PyPI。
