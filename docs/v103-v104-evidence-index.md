# LACD v1.0.3 与 v1.0.4 治理与发布证据索引（Governance & Release Evidence Index）

> **规范地位**：本索引为 LACD 软件发布与治理证据的正式归档文件（`LACD-NEXT-21`、`AC-B4`、`AC-C3`）。
> **核心原则**：严格基于 Git 提交历史与 GitHub 平台实证记录，事实求是；**严禁倒签、回溯伪造缺失证据**；未核实事项如实标记为 `RAW_PENDING` 或 `NOT_VERIFIED`。

---

## 1. 历史版本 v1.0.3 证据链（Historical v1.0.3 Chain）

### 1.1 PR 合并与审查证据链汇总

| PR 编号 | 变更标题 / 性质 | 合并提交（Merge Commit SHA） | 合并时间（UTC） | CI 结果 | 审查状态（Q1 / Q2） | 协议对齐与说明 |
|---|---|---|---|---|---|---|
| **#6** | `LACD v1.0.3 — Repository Migration Compatibility & README Experience Patch` (T1) | `714502bc86c593ae1dbc01ea4a7590bd919fd845` | `2026-10-16T02:51:53Z` | Actions run `38840463869` 成功（Python 3.11/3.12 PASS） | Round 1 `FAIL`（F-01 事实错误）；Round 2 外部非标描述为 `PASS_WITH_NOTES`（原始记录归档状态：`RAW_PENDING` / `NOT_VERIFIED`） | 见下文 §1.2 详细说明。外部非标用语不修改冻结协议，未持久化原始会话文本诚实标记为未核实 |
| **#8** | `docs(issue-7): simplify bilingual READMEs and remove AI discoverability content` (T0) | `6d76f1d16a944c3dbf1c51b4f0794cfa04f55667`（**Tag v1.0.3 指向此提交**） | `2026-10-16T03:36:44Z` | Actions run `38845982658` 成功（Python 3.11/3.12 PASS） | 独立 Q2 `PASS`（2026-10-16，隔离会话直接调用；原始记录归档状态：`RAW_PENDING`） | Human 逐字指定 README 修复（Issue #7），去除 AI 发现度内容，合入 main 后作为 v1.0.3 Tag 的目标提交 |
| **#9** | `docs: sync README install version to v1.0.3 (T0 patch)` (T0) | `4610d73ea9c231c9fe78047b514f961a53cffce9` | `2026-10-16T05:41:00Z` | CI 通过 | **`Human T0 Q1/Q2 WAIVED`**（单次人工豁免，**绝非 Q2 PASS**） | 见下文 §1.3 详细说明。PR 描述中显式记录人工豁免，严禁混淆为 Q2 通过 |

---

### 1.2 PR #6 Q2 评据与非标用语核验说明（AC-C2, AC-C3）
1. **Release Notes 记载与协议差异**：
   - GitHub Release `v1.0.3` 正文中对 PR #6 的 Q2 描述记载为：
     > “PR #6（实现）：第二轮独立 Q2 PASS_WITH_NOTES（2026-10-16，全新隔离会话直调；第一轮 FAIL 的 F-01 README 事实错误已修复）。”
   - **协议红线对照**：依据冻结协议 `docs/specification/PROTOCOL.md §5.2`，法定合法 Q2 结论**仅允许 `PASS`、`FAIL`、`HOLD` 三者之一**。`PASS_WITH_NOTES` 属于外部独立大模型给出的非规范自然语言表述。
2. **原始凭据诚实归档（RAW_PENDING / NOT_VERIFIED）**：
   - 由于历史流程中该独立会话的完整原始交互记录（Raw transcript）未能在 PR 页面以可验证永久链接或完整文本直接持久化，根据有界审查反造假规则（Anti-Fabrication Rules），**严禁事后倒签补造“完美”凭据**。
   - 本索引如实将 PR #6 的原始会话持久化证据登记为 `RAW_PENDING` / `NOT_VERIFIED`。

---

### 1.3 PR #9 的 Human 豁免性质说明（AC-C1）
1. **显式豁免声明**：
   - PR #9 为将 README 中的安装版本从 `v1.0.2` 同步至正式发布的 `v1.0.3` 的纯文档（T0）补丁。
   - PR 描述中包含经 Human 批准的流程例外声明：
     ```markdown
     ## Process exception (Human-approved, one-time)
     - Q1: WAIVED_BY_HUMAN_FOR_THIS_T0_PATCH
     - Q2: WAIVED_BY_HUMAN_FOR_THIS_T0_PATCH
     - RISK_ACCEPTANCE: HUMAN_FINAL_REVIEW_REQUIRED
     ```
2. **协议事实确认**：
   - PR #9 的 Q1 与 Q2 状态为 **`Human T0 Q1/Q2 WAIVED`**。
   - **铁律**：此项豁免为 Human 针对该特定 T0 补丁的单次特批，并不代表 LACD 流程存在常态免审通道，**绝对不得将 `WAIVED` 伪称或记录为 `Q2 PASS`**。

---

### 1.4 v1.0.3 Release 发布与制品时间差事实查证（AC-B4）
通过 GitHub REST API（`gh release view v1.0.3`）提取的真实元数据事实如下：

- **Release 标签与名称**：`v1.0.3`（指向 PR #8 的合并提交 `6d76f1d16a944c3dbf1c51b4f0794cfa04f55667`）
- **Release 发布时间（publishedAt）**：`2026-10-16T03:48:55Z`
- **Release 附件资产**：
  * 文件名：`lacd-templates-1.0.3.zip`
  * 资产 ID：`646171857`
  * 资产上传时间（createdAt）：`2026-10-16T04:47:38Z`
  * 资产更新时间（updatedAt）：`2026-10-16T04:47:41Z`
  * 资产 SHA-256 摘要：`8f49019eb5fd4febae37732b940fb610daed9361075d7d07c5ac435179507c34`
  * Release 正文声明哈希：`8f49019eb5fd4febae37732b940fb610daed9361075d7d07c5ac435179507c34`（与真实附件完全一致）
- **时间差分析与事实结论**：
  * **时间差事实**：资产附件的上传时间（04:47:38Z）落后于 Release 发布时间（03:48:55Z）约 **58 分 43 秒（~59 分钟）**。
  * **动因与防范**：这一历史时间差暴露了发布流程在自动化顺序上的脆弱性，直接构成了 v1.0.4 引入发布前强制校验门禁（`AC-B2`）的实践动因。
  * **无篡改证据确认**：经对比，上传资产的实际 SHA-256 与 Release 正文及 RRC 预期哈希完全匹配，**明确确认没有任何证据表明附件存在被替换或内容不一致的篡改行为**。

---

### 1.5 分支保护与 CI 状态的事实边界（Enforcement vs CI）
- **`CI PASS ≠ GitHub Branch Protection ENFORCED`**：
  * 尽管 PR #6、PR #8、PR #9 的 GitHub Actions 运行均显示为绿灯（Success），但这仅代表持续集成任务执行通过，并不等同于 GitHub 仓库已在主干开启并强制生效了分支保护规则（Branch Protection Ruleset / Required Status Checks）。
  * 查验分支保护配置（调用 `/repos/SkyOneBranch/LACD/branches/main/protection`）需要仓库 Admin 权限 Token。在缺乏具权 Admin Token 证实的情况下，依据 `PROTOCOL.md §2` 铁律，该状态必须如实定级为 **`UNVERIFIED`**，严禁未经查证直接宣称 `ENFORCED`。

---

## 2. v1.0.4 治理与发布证据索引模板（v1.0.4 Evidence Index Template）

本模板用于跟踪记录 v1.0.4 版本的 PR 治理、审查凭据、RRC 就绪核验、正式打标发布以及发布后核验（PRV）全生命周期证据。

> **记录守则**：所有尚未完成的后置阶段，必须诚实填写为 `PENDING_HUMAN_MERGE` 或 `PENDING_RELEASE`，**严禁在合入或发布完成前提前虚报 `RELEASED` 或 `PRV PASS`**。

### 2.1 v1.0.4 PR 治理与审查记录表

- **冻结需求与跟踪单**：GitHub Issue [#10](https://github.com/SkyOneBranch/LACD/issues/10)（关联 Notion `412ad272535b815ea874d25edf460ed4` `2026-11-11 LATEST SCOPE`）

| 跟踪项 | 凭据字段 | PR-1（WP-T 发布后文档同步） | PR-2（v1.0.4 特性实现主 PR） |
|---|---|---|---|
| **PR 基本信息** | PR 编号与链接 | [#11](https://github.com/SkyOneBranch/LACD/pull/11)（源分支 `docs/v1.0.4-wp-t-sync`） | `PENDING_PR_CREATION`（源分支 `feature/v1.0.4`，关联 Issue #10） |
| | 目标基线分支 | `main` | `main`（基于 `docs/v1.0.4-wp-t-sync` 栈式对齐以消除 `CHANGELOG.md` 合并冲突；请先普通合并 PR #11 再普通合并本 PR） |
| | 风险分级（T0/T1/T2） | `T1`（`llms.txt` → `T1`、`CHANGELOG.md` → `T0`，整体取最高 `T1`） | `T2`（含 `.github/workflows/ci.yml`、`workflows/lacd-verify.yml` 与风险分级修复，整体取最高 `T2`） |
| **CI 验证** | GitHub Actions 状态 | Python 3.11 / 3.12 push & PR 四项检查全绿（PASS） | `PENDING_PR_CI`（最终凭据写入 PR 评论） |
| | 本地自动化测试结果 | `398 passed, 1 skipped` | 独立 1.0.4 venv 全量 `pytest --cov=lacd --cov-fail-under=80` + `release_assets.py --build --verify --smoke-venv` + Live `v1.0.3` E2E 全绿 |
| **Q1 规格审查** | 审查人 / 模型 | `lacd_independent_reviewer`（会话 `b72ddceb-fc8d-41a0-8f00-694a2329e7b9` / `gemini-2.5-flash`） | 同左（统一覆盖 WP-0 / WP-A / WP-B / WP-C / WP-T，`Q1-01 ~ Q1-10`） |
| | 时间戳（UTC） | `2026-11-12T03:32:00Z` | `2026-11-12T03:32:00Z`（基线 `main` SHA `4610d73ea9c231c9fe78047b514f961a53cffce9`） |
| | 审查结论（PASS/HOLD） | `PASS` | `PASS`（摘要已归档于 Issue [#10](https://github.com/SkyOneBranch/LACD/issues/10)） |
| **Q2 独立审查（6要素）** | 1. `reviewer` | `lacd_independent_reviewer`（隔离会话 `748eaf5f-1174-4b6f-b699-85b3b1f592e2`） | `PENDING_PR_Q2`（避免分支内自指 SHA 循环，最终凭据发布于本 PR 评论） |
| | 2. `model` | `gemini-2.5-flash` | `PENDING_PR_Q2` |
| | 3. `time` | `2026-11-12T03:48:30Z` | `PENDING_PR_Q2` |
| | 4. `reviewed_head_sha` | `08ed0ccc02e20d4671a2c6d8aad62bf65a979e36` | `PENDING_PR_Q2`（严格绑定本 PR 最终稳定 40 位 HEAD） |
| | 5. `verdict` | `PASS` | `PENDING_PR_Q2`（仅限 `PASS` / `FAIL` / `HOLD`） |
| | 6. `raw` | [PR #11 评论 #6813813970](https://github.com/SkyOneBranch/LACD/pull/11#issuecomment-6813813970) | `PENDING_PR_Q2`（持久化于本 PR 评论区） |
| **Human 决策与合并** | 合并提交（Merge Commit SHA） | `PENDING_HUMAN_MERGE` | `PENDING_HUMAN_MERGE` |
| | 合并时间戳（UTC） | `PENDING_HUMAN_MERGE` | `PENDING_HUMAN_MERGE` |
| | 授权人 / 方式 | Human Approve + Regular Merge (`Create a merge commit`) | Human Approve + Regular Merge (`Create a merge commit`) |

---

### 2.2 v1.0.4 RRC 发布就绪核验记录（Post-Merge, Pre-Tag，对齐 `docs/operations/rrc.md`）

| 核验项目 | 检查内容 | 预期结果与规范 | 执行状态 / 记录 |
|---|---|---|---|
| **RRC-1** | 合并 SHA 查验 | `gh api pulls/<N>` `merged=true` 且 `merge_commit_sha == main HEAD` | `PENDING_HUMAN_MERGE` |
| **RRC-2** | 合并提交 CI 全绿 | `MERGE_SHA` 对应的 Actions run（含 `test (3.11)`、`test (3.12)` 及 Packaging Gate）全为 success | `PENDING_HUMAN_MERGE` |
| **RRC-3** | 分支保护与 Required Checks | 分支保护规则生效，Required checks 覆盖合并提交 | 若无 Admin Token 返回 403 则如实记录 `HOLD` / `UNVERIFIED`，由 Human 网页查验 |
| **RRC-4** | Q2 凭据与 HEAD 绑定 | 普通 merge 下 `MERGE_SHA` 第二父提交 == Q2 `reviewed_head_sha`，Q2 为 `PASS` 且未过期 | `PENDING_HUMAN_MERGE` |
| **RRC-5** | 本地制品摘要与 Smoke Venv 核验 | 从 `MERGE_SHA` 执行 `python scripts/release_assets.py --out-dir /tmp/rrc-assets --build --verify --smoke-venv` 返回 0 | `PENDING_HUMAN_MERGE` |
| **RRC-6** | Release Notes 双格式解析预检 | `release-notes-snippet-1.0.4.md` 含闭合 JSON 块与 `Template-Bundle-SHA256:` 明文行，经 `parse_template_bundle` 校验一致 | `PENDING_HUMAN_MERGE` |
| **RRC 总结果** | RRC 综合裁决 | `RRC-1..RRC-6` 全部 PASS → 提交 Human Release Authorization；任一 FAIL/HOLD → 停止或等待解除 | `PENDING_HUMAN_MERGE` |

---

### 2.3 v1.0.4 Tag、Release 与 PRV 记录（Human-Only & Post-Release）

| 阶段 | 凭据项 | 预期规范 | 真实记录与状态 |
|---|---|---|---|
| **Tag 标记** | Git 标签名称 | `v1.0.4` | `PENDING_RELEASE` |
| | 标签指向 Commit SHA | 必须等于 RRC-1 核验的 `MERGE_SHA` | `PENDING_RELEASE` |
| | 打标与推送人 | Human 专享授权（`git tag -a v1.0.4`） | `PENDING_RELEASE` |
| **Release 发布** | 发布发布页面链接 | `https://github.com/SkyOneBranch/LACD/releases/tag/v1.0.4` | `PENDING_RELEASE` |
| | 发布时间（publishedAt） | UTC 时间戳 | `PENDING_RELEASE` |
| | 模板包附件名 | `lacd-templates-1.0.4.zip` | `PENDING_RELEASE` |
| | 模板包上传时间（createdAt）| 验证与 Release 发布时间一致（杜绝 v1.0.3 的 59 分钟延迟） | `PENDING_RELEASE` |
| | 模板包 SHA-256 | 与 RRC-5 计算的哈希完全一致 | `PENDING_RELEASE` |
| **PRV 核验** | 远程 Tag 对应性核验 | 查验 GitHub 远端 `refs/tags/v1.0.4` 精确等于 `MERGE_SHA` | `PENDING_RELEASE` |
| | 远端资产下载校验 | `curl` 下载 Release 附件，本地计算 SHA-256 必须一致 | `PENDING_RELEASE` |
| | 真实客户端升级探测 | 在独立干净环境中运行 `lacd upgrade --check` 能够成功探测到 `1.0.4` | `PENDING_RELEASE` |
| | 综合 PRV 裁决 | 通过后方可批准生产采用 | `PENDING_RELEASE` |
