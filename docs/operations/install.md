# 安装（v1.0.4）

> **注意**：LACD 当前**未发布到 PyPI**。请勿直接执行 `pip install lacd`（除非后续官方完成 PyPI 发布）。
> 以下安装方式均经过自动化门禁与双仓库测试实测。

## 方式 1：从 GitHub Release 下载 Wheel + SHA-256 校验安装（推荐，极速、离线可用）

从 [GitHub Releases](https://github.com/SkyOneBranch/LACD/releases/tag/v1.0.4) 下载预构建的 `lacd-1.0.4-py3-none-any.whl` 及其 release-manifest / release notes snippet 核对哈希：

```bash
# 下载 wheel 并核验 SHA-256（示例 sha256 见对应 Release Notes 与 release-manifest-1.0.4.json）
pip install lacd-1.0.4-py3-none-any.whl
```

## 方式 2：使用 pipx / uv 独立工具链安装（推荐用于全局 CLI）

使用 `pipx` 或 `uv tool` 可将 LACD 隔离安装到专用虚拟环境，避免污染全局 Python：

```bash
# 使用 pipx：
pipx install "git+https://github.com/SkyOneBranch/LACD.git@v1.0.4"

# 或使用 uv tool：
uv tool install "git+https://github.com/SkyOneBranch/LACD.git@v1.0.4"
```

## 方式 3：从 Git Release Tag 安装（标准 pip 方式）

```bash
pip install "git+https://github.com/SkyOneBranch/LACD.git@v1.0.4"
# 或固定到精确 commit SHA：
pip install "git+https://github.com/SkyOneBranch/LACD.git@<40位commit SHA>"
```

## 方式 4：本地源码安装（开发调试）

```bash
git clone https://github.com/SkyOneBranch/LACD.git && cd LACD
pip install .
```

## 项目隔离执行（多版本共存）

```bash
python -m venv .venv-lacd-1.0.4 && . .venv-lacd-1.0.4/bin/activate
pip install "git+https://github.com/SkyOneBranch/LACD.git@v1.0.4"
lacd status --json
```

验证安装：`lacd --version` 应输出 `lacd 1.0.4`。
