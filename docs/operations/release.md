# 发布检查清单（maintainer / Human 执行）

> LACD 的正式发布（tag / Release / 制品上传）必须由 Human 授权并执行，
> Muse / AI Agent 不得代办、不得谎称已发布。

## 发布步骤（v1.0.4+ 标准化发布流程）

1. **候选构建验证**
   - [ ] `pytest -q` 全绿（含 acceptance AT-01..AT-25 及 e2e matrix）
   - [ ] `pytest --cov=lacd --cov-fail-under=80 -q` 覆盖率达标
   - [ ] `src/lacd/__init__.py` 的 `__version__`、`pyproject.toml`、模板 manifest 版本一致
2. **PR 合并**：实现 PR 经 Human Approve + Merge 到 `main`，CI 全绿（含 CI Packaging Gate 检查）
3. **打 Tag**：`git tag -a v1.0.4 -m "LACD v1.0.4" && git push origin v1.0.4`（精确 commit 一经固定即不可变）
4. **发布前制品构建与核验（AC-B2，防制品滞后）**：
   在正式创建 GitHub Release **前**，从当前 merge commit 构建并完整自检所有发布制品：
   ```bash
   python scripts/release_assets.py --out-dir /tmp/rrc-assets --build --verify --smoke-venv
   ```
   该命令自动完成：
   - 构建 `lacd-<version>-py3-none-any.whl`（含 templates、schemas、manifest，无 `.pyc`）
   - 构建 `lacd-templates-<version>.zip`
   - 生成 `release-manifest-<version>.json`
   - 生成 `release-notes-snippet-<version>.md`（含双格式 SHA-256）
   - 在独立临时虚拟环境中验证 `lacd init`、`status`、`verify --local --strict`
   确保在创建 GitHub Release 时所有制品与 Hash 预先就绪，**绝不滞后于 Release 发布**。
5. **创建 GitHub Release（Human 授权执行）**：
   - 基于 Tag 创建正式 Release
   - 上传 `/tmp/rrc-assets/` 下的两个关键附件：
     - `lacd-<version>-py3-none-any.whl`
     - `lacd-templates-<version>.zip`
   - Release 正文填入对应 CHANGELOG，并在底部粘贴 `/tmp/rrc-assets/release-notes-snippet-<version>.md` 的完整内容
6. **PRV 发布后验证（AC-B3）**：
   Release 发布完毕后，立即运行发布后核验（PRV）：
   ```bash
   python scripts/release_assets.py --verify-public-release --tag v1.0.4
   ```
   该工具自动请求 GitHub Releases 公开 API，重新下载模板包和 wheel，核验 SHA-256 与 bundle 加载能力。若有任何不匹配立即 fail-closed 报警。
7. **分支保护与公告**：确认 `main` Ruleset / Required Checks 生效。

---

## Release notes 规范（FR-02，闭合双格式）

> Release 正文必须**同时**包含闭合 JSON 块与 `Template-Bundle-SHA256:` 明文行
> （双格式，互相备份；`parse_template_bundle` 按 (a)→(b)→(c) 顺序解析，全部
> fail-closed）。**围栏必须闭合**——v1.0.0 的未闭合围栏导致解析失败，不得重蹈。

```markdown
## LACD vX.Y.Z — <release title>

<CHANGELOG 对应章节内容>

## Template bundle

`lacd-templates-X.Y.Z.zip` — SHA-256 verified by `lacd upgrade` before use:

```json
{"template_bundle": {"url": "https://github.com/SkyOneBranch/LACD/releases/download/vX.Y.Z/lacd-templates-X.Y.Z.zip", "sha256": "<64 hex>"}}
```

Template-Bundle-SHA256: <64 hex>
```

**填写要求**：
- `<64 hex>` 两处必须一致，直接取自 `scripts/release_assets.py` 生成的 snippet。
- `url` 必须与附件的 `browser_download_url` 一致
  （`https://github.com/SkyOneBranch/LACD/releases/download/vX.Y.Z/lacd-templates-X.Y.Z.zip`）。
- JSON 块的围栏必须闭合（开头和结尾各一行 ` ``` `）。

### 发布校验清单（Human 发布时逐项打勾）

- [ ] `scripts/release_assets.py --build --verify --smoke-venv` 在发布前执行并通过
- [ ] 附件包含 `lacd-<version>-py3-none-any.whl` 与 `lacd-templates-<version>.zip`
- [ ] tag 的 SHA == `main` 合并提交的 SHA（`git rev-parse vX.Y.Z` 核对）
- [ ] 正文 JSON 块中 `sha256` == 附件实测 sha256
- [ ] 正文 `Template-Bundle-SHA256:` 行的 sha256 == 同一值
- [ ] Release 为正式版（非 draft、非 prerelease）
- [ ] 发布后执行 `scripts/release_assets.py --verify-public-release --tag vX.Y.Z` 成功（PRV 通过）

任一项不匹配 → 停止发布，修复后重走清单。**绝不发布 sha256 存疑的模板包。**
