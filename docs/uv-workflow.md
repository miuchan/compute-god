# 使用 uv 的开发工作流

`uv` 提供极速的 Python 依赖解析与隔离能力。本仓库已经使用 `uv` 约定化开发体验，主要约束如下：

## 安装依赖

```bash
uv sync --dev
```

该命令会根据 `pyproject.toml` 与 `uv.lock` 安装运行时与开发时依赖。若需要更新版本，修改 `pyproject.toml` 或运行 `uv add <package>` 后重新生成锁文件：

```bash
uv lock
```

## 常用脚本

项目脚本定义在 `pyproject.toml` 的 `[tool.uv.scripts]` 中，可使用 `uv run <script>` 调用：

```bash
uv run test         # 运行 pytest
uv run test-cov     # 运行带覆盖率的 pytest
uv run lint         # Ruff 静态检查
uv run format       # Ruff 格式化
uv run typecheck    # mypy 类型检查
```

`uv run` 会自动在隔离环境中执行脚本，确保依赖一致。

## 提交流程

1. `uv sync --dev`
2. `uv run format && uv run lint`
3. `uv run test`
4. `git commit`

若在 CI 中使用，可直接调用上述脚本，保证本地与 CI 环境一致。
