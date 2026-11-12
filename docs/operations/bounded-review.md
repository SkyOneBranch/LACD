# 有界审查操作指南（Bounded Review Operational Guide）

> **规范地位**：本指南为 LACD 开发流程的操作级运行手册（Runbook），严格对齐已冻结的 `docs/specification/PROTOCOL.md §5` 及 `docs/decisions/ADR-0012-q2-rrc-prv.md`。
> 本指南不得篡改、削弱或替代任何冻结契约（`PRODUCT.md`、`PROTOCOL.md`、`UPGRADE_CONTRACT.md`、`MODULE_CONTRACT.md`）。

---

## 1. 风险分级与审查适用性（AC-C1）

LACD 严格沿用已冻结且经代码实现的经典三级风险分类体系（`MODULE_CONTRACT §4` 与 `src/lacd/governance/risk.py`），**严禁自创或引入任何非标等级**（如所谓的 `Solo-Lite`、`Standard`、`Strict` 等）：

| 等级 | 涵盖路径与语义 | 审查与治理门槛 |
|---|---|---|
| **T0** | 纯文档、示例、许可证、更新日志：`docs/**`、`examples/**`、`README*`、`LICENSE*`、`NOTICE*`、`CHANGELOG*`（注意排除项） | 本地 `lacd verify` + CI；默认走标准流程；若跳过 Q1/Q2，必须且仅能通过 **Human 单次显式授权（WAIVED）**，严禁常态免审 |
| **T1** | 常规代码、测试、配置、治理描述：`src/**`、`tests/**`、`schemas/**`、`pyproject.toml`、`AGENTS.md`、`llms.txt` 及常规未匹配项 | **完整流程**：独立 Q1（需求/规格） → 编码与测试 → CI 自动化门禁 → 独立 Q2（审查最终 HEAD） → Human Merge |
| **T2** | 高危治理、工作流、凭据、安全边界：`.github/**`、`.lacd/**`、`**/workflows/**`、`SECURITY.md`、含密钥/token 关键字、路径穿越/非法路径 | **最高审查级别**：强制全量 Q1 冻结审查 → 针对性反向安全测试（Negative Tests） → CI 全绿 → 独立 Q2 → Human 安全检查点 → Human Merge |

### 1.1 关键路径判定红线（Path Classification Traps）
路径分类由 `classify_change()` 实现，严格按规则顺序优先匹配，取改动文件集合中的**最高风险等级**（T2 > T1 > T0）。开发与审查人员必须警惕以下易混淆路径：
- **`SECURITY.md` 是 T2**：尽管属于 markdown 文档，但在规则中置于 T0 之前优先匹配，作为安全披露边界严格定级为 `T2`。
- **`AGENTS.md` 是 T1**：根目录的 `AGENTS.md` 是 Agent 的治理入口文件，不是普通说明文档，代码中显式将其定级为 `T1`，绝不属于 T0。
- **`llms.txt` 是 T1**：作为根目录上下文指引，不属于 `docs/` 或 `examples/`，亦不具备 `readme/license/notice/changelog` 前缀，按兜底规则严格定为 `T1`，绝不属于 T0。

### 1.2 T0 变更的 Human 豁免规则（Human Waiver）
1. 任何跳过 Q1 或 Q2 的 T0 PR，必须获得 Human 的**逐次、单次、显式豁免**（例如历史 PR #9 中 Human 显式批准的 `WAIVED_BY_HUMAN_FOR_THIS_T0_PATCH`）。
2. **不存在自动常态免审**：历史 PR #9 仅代表该次特定文档补丁的人工豁免实例，不得被解释为所有 T0 任务的永久免审通行证。
3. **记录诚实性**：被 Human 豁免的环节，在证据归档中必须客观记录为 `WAIVED`，**严禁伪称或混淆为 `Q2 PASS`**。

---

## 2. 严格 Q2 凭据与 HEAD 强失效铁律（AC-C2, AC-C3）

### 2.1 唯一合法的 Q2 结论（Verdicts）
依据 `PROTOCOL.md §5.2`，正式的 Q2 审查结论**仅允许以下三者之一**：
- **`PASS`**：未发现任何阻断性缺陷（BLOCKER / CORE_AC / SECURITY），符合合并至主干的质量要求。
- **`FAIL`**：发现代码、需求契约、安全性或测试断言缺陷，禁止推荐合并，禁止进入 RRC。
- **`HOLD`**：审查存在外部依赖未定、关键事实无法核实或需要 Human 介入决策，暂停流程。

### 2.2 Q2 凭据必备六要素（Six Mandatory Receipt Fields）
一次合法的 Q2 凭据必须完整包含以下 6 个字段，缺一不可：
1. `reviewer`：审查者身份（独立审查账号、独立角色标识）。
2. `model`：审查所使用的具体模型及版本（如 Claude-3.5-Sonnet、GPT-4o 等）。
3. `time`：审查完成的 UTC 时间戳（ISO 8601 格式）。
4. `reviewed_head_sha`：所审查的 PR 分支 **最终稳定 HEAD** 的 40 位完整 Git SHA。缺少该字段的 Q2 凭据直接视为无效。
5. `verdict`：法定结论（必须为 `PASS`、`FAIL` 或 `HOLD`）。
6. `raw`：独立审查产出的完整原始评审意见文本或不可篡改的持久化引用链接。

### 2.3 HEAD 变动绝对过期铁律（Zero Non-Substantive Diff Exceptions）
- 若 `reviewed_head_sha != PR 当前 HEAD`，则该 Q2 凭据**立即失效**，必须重新审查。
- **无“非实质改动”例外**：无论是修改了代码逻辑、调整了一行注释、修复了一个标点，还是执行了 `git rebase` / `merge main`，只要 HEAD SHA 改变，原 Q2 凭据均告作废。可判定性绝对优先于便利性。

### 2.4 上下文隔离与非标术语映射
- **隔离性本质**：Q2 的独立性是由审查方处于**实现者上下文之外**（全新会话、无实现者偏见、无共享草稿）所保证的，而不是靠 JSON 结构体格式来保证。单凭结构化 JSON 输出绝不能证明审查上下文实现了有效隔离。
- **非标用语处理**：若外部独立审查模型给出了诸如 `PASS_WITH_NOTES`、`LGTM_CONDITIONAL` 等非标文本，操作规范如下：
  1. `raw` 字段完整逐字保留审查者的原始输出，不得纂改原始记录；
  2. 提取并分离非阻断性改进建议（P2 Notes），归入后续优化跟踪项；
  3. 审查结论严格规范映射为法定的 `PASS`、`FAIL` 或 `HOLD`，**严禁在未经 ADR 修改冻结协议的情况下向 `PROTOCOL.md` 引入非标枚举值**。

---

## 3. 有界升级与防死循环规则（AC-C4）

在多轮审查与多 Agent 协作中，必须防止无限陷入局部修辞争论，同时严守安全与正确性红线：

```
                    ┌─────────────────────────┐
                    │   Round 1: Q2 Review    │
                    └────────────┬────────────┘
                                 │
                     ┌───────────┴───────────┐
                 FAIL│                       │PASS
                     ▼                       ▼
          ┌───────────────────────┐    ┌─────────────────┐
          │ Fix Code/Tests/Docs   │    │ Ready for Human │
          └──────────┬────────────┘    └─────────────────┘
                     │ (New HEAD)
                     ▼
          ┌─────────────────────────┐
          │   Round 2: Q2 Review    │
          └────────────┬────────────┘
                       │
           ┌───────────┴───────────┐
       FAIL│                       │PASS
           ▼                       ▼
    ┌──────────────────────┐   ┌─────────────────┐
    │ New Factual Blocker? │   │ Ready for Human │
    └──────┬───────────────┘   └─────────────────┘
     Yes   │               │ No (Subjective/Stylistic Deadlock)
           ▼               ▼
┌──────────────────┐  ┌───────────────────────────────────┐
│ Fix & Retest     │  │ Escalate Bounded Options Packet  │
│ (Max 1 more loop)│  │ to Human (Strictly Anti-Loop)    │
└──────────────────┘  └───────────────────────────────────┘
```

1. **阻断性缺陷绝不妥协（No Auto-PASS for Blockers）**：
   - 凡涉及核心代码实现缺陷（`CODE`）、验收标准违背（`CORE_AC`）或安全漏洞（`SECURITY`），**无论经历多少轮审查，均严禁“达到 N 轮自动放行”**。阻断性缺陷必须在代码或测试中彻底修复并重新验证。
2. **两轮收敛与人工升级机制（Anti-Loop Escalation）**：
   - 若经历 2 轮审查后，审查意见中**未提出任何新的客观事实阻断项**，仅存在主观措辞偏好、非功能性架构分歧或边界裁量争议，**严禁开启无休止的第 3、4 轮循环**。
   - 实现者必须立即整理并向 Human 提交一份**有界决策数据包（Bounded Options Packet）**：
     * 说明已满足的验收条件与通过的测试清单；
     * 明确当前争议点的双方观点与技术影响；
     * 提供闭合的决策选项（如：选项 A 采纳并合入，将建议作为后续跟踪 Issue；选项 B 针对争议点进行特定最小调整；选项 C 关闭 PR）；
     * 由 Human 行使最终仲裁权。
3. **历史证据缺失诚实记录（Historical Honesty）**：
   - 针对历史版本中不可追溯的审查记录缺失，操作人员必须诚实记录为 `NOT_VERIFIED` 或 `RAW_PENDING`，并将事实边界提交 Human 裁决，**严禁倒签假凭据、篡改历史提交或虚构次级放行契约**。

---

## 4. 关键阶段职责分离（AC-C5）

整个软件发布生命周期划分为六个职责明确、互不重叠的独立阶段，严禁阶段跃迁与概念混淆：

```
┌──────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────────────┐
│ 1. PR QA     │ ──> │ 2. Human    │ ──> │ 3. RRC      │ ──> │ 4. Tag /     │ ──> │ 5. PRV      │ ──> │ 6. Downstream        │
│ (CI + Q2)    │     │    Merge    │     │ (Post-Merge)│     │    Release   │     │ (Post-Rel)  │     │    Adopter ENFORCED  │
└──────────────┘     └─────────────┘     └─────────────┘     └──────────────┘     └─────────────┘     └──────────────────────┘
```

1. **PR QA（CI + 独立 Q2）**：
   - 执行时机：PR 合并前。
   - 职责：验证分支 CI 测试全绿；独立审查方完成对 PR 最终 HEAD 的全面质量核查并签署法定凭据。
2. **Human Merge（人工合并）**：
   - 执行时机：PR QA 通过后。
   - 职责：Human 确认范围、风险与回退路径，在 GitHub 网页端执行 Approve 与 Merge。**Q2 是专业建议，Human Merge 才是法定授权；Q2 绝不能替代 Human Merge**。
3. **RRC（Release Readiness Check，发布就绪核验）**：
   - 执行时机：Human 合并**之后**、打 Tag **之前**。
   - 职责：运行脚本和核验手册（`docs/operations/rrc.md`），检查合并提交 SHA、该 SHA 对应的 CI 状态、本地制品构建摘要（Wheel / Bundle ZIP / Manifest）、Release Notes 草稿格式。
   - **关键区别**：**RRC 是确定性的机器与元数据核验，不是第二次 Q2**；RRC 仅核验发布预期，**不核验 Tag 本身（因为此时 Tag 尚未创建）**；RRC 证据严禁回写 `main` 分支以防 SHA 递归改变。
4. **Tag / Release（打标与发布）**：
   - 执行时机：RRC PASS 之后。
   - 职责：**纯 Human 授权执行**。依据 RRC 核准的 commit SHA 打 Git 附注标签并推送，在 GitHub Release 页面发布版本并上传模板包附件。
5. **PRV（Post-Release Verification，发布后真实核验）**：
   - 执行时机：GitHub Release 正式发布**之后**。
   - 职责：从外部客观视角核验已发布的生产制品——验证远程 Tag 是否准确指向目标 SHA（防止 Tag 被篡改或漂移）、Release 附件与哈希是否一致、`lacd upgrade --check` 能否真实探测到新版本并顺利安装。PRV 通过后，方可宣布支持生产环境采纳。
6. **Downstream Adopter ENFORCED（采用者端强制生效）**：
   - 执行时机：下游项目接入与持续治理阶段。
   - 职责：属于采用者仓库的状态机维度（`remote_enforcement = enforced`），代表下游仓库的 GitHub 分支保护和必需检查已由 GitHub API 实证生效。该状态需要具权的 Token 查证，绝不能将本仓库构建阶段的 `CI PASS` 混同为下游的 `ENFORCED`。

---

## 5. 三个典型演练案例（Three Synthetic Walkthrough Cases）

### 案例 1：T0 纯文档小修/勘误（Pure Doc Typo / Version Sync Patch）
- **变更场景**：修正 `docs/operations/install.md` 中的命令排版错误或安装版本号。
- **阶段 1：路径与风险判定**
  - 执行 `classify_change(['docs/operations/install.md'])` 返回 `T0`。
  - 检查变动文件列表，确认未夹带 `.github/`、`SECURITY.md`、`AGENTS.md` 或 `llms.txt`。
- **阶段 2：实现与本地自检**
  - 实施修改，运行 `lacd verify --local` 确保本地一致性。
- **阶段 3：免审决策与凭据记录**
  - 该补丁影响范围极小，团队决定申请 Human 豁免独立 Q1/Q2。
  - 在 PR 描述中清晰声明：
    ```markdown
    ## Process exception (Human-approved, one-time)
    - Q1: WAIVED_BY_HUMAN_FOR_THIS_T0_PATCH
    - Q2: WAIVED_BY_HUMAN_FOR_THIS_T0_PATCH
    - RISK_ACCEPTANCE: HUMAN_FINAL_REVIEW_REQUIRED
    ```
  - **红线核对**：在 PR 元数据与发布索引中，该审查状态必须如实标记为 `WAIVED`，**严禁标注为 `Q2 PASS`**。
- **阶段 4：合并**
  - CI 检查绿灯通过，Human 完整审阅 Diff 后在 GitHub 执行合并。

---

### 案例 2：T1 标准功能/缺陷修复（Standard Code & Test Fix）
- **变更场景**：修复 CLI 状态计算的一处边缘缺陷，并补充单元测试。
- **阶段 1：路径与风险判定**
  - 改动路径：`src/lacd/cli/main.py`、`tests/unit/test_cli_status.py`。
  - 执行 `classify_change`，判定结果为 `T1`。
- **阶段 2：Q1 规格与证伪设计**
  - 开展独立 Q1，明确需求验收标准：在修复代码生效前，新增的测试用例必须能够稳定复现并红灯报错（Fail-Before-Pass 证伪设计）。
- **阶段 3：编码、测试与 CI**
  - 编写失败用例，随后编写修复逻辑，本地运行 `pytest` 全绿。
  - 推送分支至 PR，触发远程 GitHub Actions CI，全量测试套件成功。当前 PR HEAD SHA 为 `a1b2c3d...`。
- **阶段 4：独立 Q2 审查与 HEAD 变动处理**
  - 独立 Web AI 接入会话（上下文隔离），审阅 PR HEAD `a1b2c3d...`。
  - 评审意见返回：“核心逻辑与测试通过，建议为某处局部变量添加更详细的类型注解（Non-blocking P2 Note）”。
  - **分支决策 A（直接合入）**：若判定该建议属于低优先级非阻断建议，可在记录中规范归档为 `PASS`，建议登记为后续技术债务 Issue，当前 Q2 凭据保持对 `a1b2c3d...` 有效。
  - **分支决策 B（现场修改）**：若开发者现场提交了类型注解修改，推送后 HEAD SHA 变更为 `e5f6g7h...`。
    * **铁律触发**：原针对 `a1b2c3d...` 的 Q2 凭据**即刻作废（EXPIRED）**；
    * 必须在独立会话中针对新 HEAD `e5f6g7h...` 重新执行 Q2 审查，取得新的有效 Q2 凭据。
- **阶段 5：合并**
  - 有效 Q2 PASS 凭据具备 + CI 全绿 → Human 执行 PR 合并。

---

### 案例 3：T2 工作流/安全敏感变更（Workflow / Governance / Security-Adjacent Change）
- **变更场景**：调整 `.github/workflows/ci.yml` 中的构建步骤，并调整 `src/lacd/governance/risk.py`。
- **阶段 1：路径与风险判定**
  - 改动包含 `.github/` 路径，`classify_change` 直接且严格判定为最高等级 `T2`。
- **阶段 2：强制 Q1 与反向测试设计**
  - 必须进行全量 Q1 审查，产出详细的风险控制方案。
  - 编写反向安全用例（Negative Security Tests）：验证在恶意伪造路径、未授权上下文或边界逃逸输入下，安全防护能够可靠拦截（Fail-Closed）。
- **阶段 3：编码与 CI**
  - 完成实现与自动化测试，CI 必须全量通过且分支保护策略严密。
- **阶段 4：严格 Q2 审查与防死循环约束**
  - 独立 Q2 介入。若 Q2 发现权限配置过宽问题（阻断性安全缺陷），出具 `FAIL` 结论。
  - **安全红线**：**该安全缺陷决不能因为多轮审查而自动放行或降级免审**，必须由开发者完成修复。
  - 修复完成后，HEAD 移动，原 Q2 凭据作废，开展第 2 轮 Q2 审查。
  - 若第 2 轮审查中，安全缺陷已修复，但双方对 GitHub Actions 某个非安全相关的 cache 目录配置风格产生争议：
    * 触发**两轮防死循环规则**：严禁无休止辩论，实现者整理有界决策包（说明安全缺陷已修复，列出 cache 配置方案 A 与 B 的利弊），直接上报 Human 仲裁。
    * Human 裁定选定方案 A，提交最终调整，新 HEAD `9z8y7x...` 重新经独立 Q2 审查通过，出具合法 Q2 PASS 凭据。
- **阶段 5：合并与后续阶段**
  - Human 完成最终审核并执行 Merge。合并完成后，方可由发布负责人启动 RRC 发布核验流程。
