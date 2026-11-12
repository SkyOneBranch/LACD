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

| 跟踪项 | 凭据字段 | PR-1（WP-T 契约同步） | PR-2（v1.0.4 特性实现主 PR） |
|---|---|---|---|
| **PR 基本信息** | PR 编号与链接 | 待创建（源分支 `docs/v1.0.4-wp-t-sync`） | 待创建（源分支 `feature/v1.0.4`） |
| | 目标基线分支 | `main` | `main` |
| | 风险分级（T0/T1/T2） | `T0` / `T1`（经 `classify_change` 计算） | `T1`（含代码、测试与元数据改动） |
| **CI 验证** | GitHub Actions Run ID | `PENDING_PR_CREATION` | `PENDING_PR_CREATION` |
| | 自动化测试结果 | 待记录（需 `pytest -q` 全绿） | 待记录（需 `pytest -q` 全绿，覆盖率达标） |
| **Q1 规格审查** | 审查人 / 模型 | 待记录 | 待记录 |
| | 时间戳（UTC） | 待记录 | 待记录 |
| | 审查结论（PASS/HOLD） | 待记录 | 待记录 |
| **Q2 独立审查（6要素）** | 1. `reviewer` | 待分配独立审查者 | 待分配独立审查者 |
| | 2. `model` | 待记录模型名称与版本 | 待记录模型名称与版本 |
| | 3. `time` | 待记录完成时间戳（ISO 8601） | 待记录完成时间戳（ISO 8601） |
| | 4. `reviewed_head_sha` | 待填入经审阅的最终稳定 HEAD（40位） | 待填入经审阅的最终稳定 HEAD（40位） |
| | 5. `verdict` | 严格限定为 `PASS` / `FAIL` / `HOLD` | 严格限定为 `PASS` / `FAIL` / `HOLD` |
| | 6. `raw` | 完整原始评审文本或永久可信链接 | 完整原始评审文本或永久可信链接 |
| **Human 决策与合并** | 合并提交（Merge Commit SHA） | `PENDING_HUMAN_MERGE` | `PENDING_HUMAN_MERGE` |
| | 合并时间戳（UTC） | `PENDING_HUMAN_MERGE` | `PENDING_HUMAN_MERGE` |
| | 授权人 / 方式 | Human Approve + Merge on Web | Human Approve + Merge on Web |

---

### 2.2 v1.0.4 RRC 发布就绪核验记录（Post-Merge, Pre-Tag）

| 核验项目 | 检查内容 | 预期结果与规范 | 执行状态 / 记录 |
|---|---|---|---|
| **RRC-1** | 合并 SHA 查验 | `gh api pulls/<N>` `merged=true` 且 `merge_commit_sha == main HEAD` | `PENDING_HUMAN_MERGE` |
| **RRC-2** | 合并提交 CI 全绿 | `MERGE_SHA` 对应的 Actions run 状态全为 success | `PENDING_HUMAN_MERGE` |
| **RRC-3** | 分支保护与 Required Checks | 分支保护规则生效，Required checks 覆盖合并提交 | 若无 Admin Token 则记录为 `UNVERIFIED`，由 Human 网页查验 |
| **RRC-4** | Q2 凭据与 HEAD 绑定 | `reviewed_head_sha` 等于 PR 合并前最终 HEAD，Q2 为 `PASS` 未过期 | `PENDING_HUMAN_MERGE` |
| **RRC-5** | 本地制品摘要与 Manifest 核验 | 从 `MERGE_SHA` 构建 Wheel 与 Bundle ZIP，哈希与 `manifest.json` 一致 | `PENDING_HUMAN_MERGE` |
| **RRC-6** | Release Notes 格式解析 | 正文包含闭合 JSON 块与 `Template-Bundle-SHA256:` 明文行，解析无误 | `PENDING_HUMAN_MERGE` |
| **RRC-7** | CHANGELOG 与版本一致性 | `__version__`、CHANGELOG 章节、Release 目标版本均为 `1.0.4` | `PENDING_HUMAN_MERGE` |
| **RRC-8** | RRC 综合裁决 | 所有项全 PASS → 推荐打标发布；任一项缺陷 → HOLD | `PENDING_HUMAN_MERGE` |

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
