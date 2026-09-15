# 合规与基础法律页面 — 合规评估报告

> ShipSolo 流水线 · 阶段 `04-compliance` · Skill `student-site-compliance-pipeline` v2.3.0
> 唯一开发依据：`PRD-ev-charging-cost-calculator-v1` (2026-09-09)

## 1. 基本信息

| 项 | 值 |
|---|---|
| 项目 | EV 充电成本计算器（暂名 ChargeCost，含 v1.1 四动力总成扩展 "FuelCost Compass"） |
| 域名候选 | `evchargingcostcalculator.com`（推荐）/ `costtochargeev.com`（副选） |
| 当前阶段 | `04-compliance` |
| 执行日期 | 2026-09-10 |
| 目标市场 | 主 US/English；次 UK、CA、AU、IN、DE（PRD §8 Route Contract 五国页） |
| 技术栈 | Cloudflare Pages 静态 + 车型/费率 JSON（PRD §6） |
| 状态 | **[NEEDS_REVIEW]**（P0 未清零，见 §7） |

## 2. 上游输入与 Preflight

### 2.1 Preflight 结果

`requirements.json` 中 `accounts` / `env` / `browserSessions` 均为空数组 → 本阶段无硬性账号、Token、浏览器登录态要求。
已运行 `scripts/check_setup.py`，输出：git / node / npm / python3 / curl / wrangler / gh 全部 `OK`，无 MISSING 环境变量。

**结论：不输出 `[BLOCKED: SETUP_REQUIRED]`。**

### 2.2 输入契约核对

| 契约项 | 状态 | 依据 |
|---|---|---|
| 站点功能清单 | ✅ | PRD §5 定位边界、§6 站点类型化、§8 MVP 功能范围、§13 四动力扩展 |
| 收集的数据类型 | 🟡 部分 | PRD §9 已给数据流口径，但未列字段级清单与保留期 → 本阶段补齐（见 `01-data-inventory.md`） |
| 第三方服务 | 🟡 部分 | PRD §9 标 GA4/Clarity/广告网络 `[待确认]` → 按 `[待确认]` 处理，第三方表留槽位并默认关闭 |
| 目标市场 | ✅ | PRD §8：US 主站 + 5 国页（uk/ca/au/in/de）→ 多法域 |
| 素材/IP/品牌使用 | ✅ | PRD §9 商标红线（Tesla）+ Data Contract（EIA/EPA 公共数据源） |

### 2.3 阻断规则检查（`requirements.json.blockingRules`）

| 规则 | 判定 |
|---|---|
| 涉及支付/登录/上传/AI API 但没有功能说明：BLOCKED | ✅ 不触发。PRD §5 NOT-DO 明确：无账号/登录/付费墙/上传；§6 无后端无上传；NOT-DO 明确"不做 AI 生成内容"。四项能力**均不存在**，故无需功能说明。 |
| 不能把法律结论写成律师意见 | ✅ 遵守。全文标注"非法律意见"，法域结论标注依据与 `[待确认]`。 |

### 2.4 关键假设（无证据不编造，逐条标源）

- **A1** 计算全部在浏览器前端完成，输入不落服务器。来源：PRD §6「计算全部在浏览器前端本地完成（无后端、无上传）」+ §9「用户输入仅存在于浏览器本地 + URL 参数」。
- **A2** 无支付、无订阅、无退款场景。来源：PRD §5 NOT-DO + §10「无订阅无付费墙」。
- **A3** 无 AI 生成、无 UGC。来源：PRD §5 NOT-DO「不做论坛/UGC/AI 生成内容」。
- **A4** 服务器侧日志（IP/UA/Referer/URL 含查询串）由 Cloudflare 产生。依据：Cloudflare Pages 为托管/CDN 服务，必然产生访问日志；具体保留期为 **[待确认]**（需查 Cloudflare 账户 Log Retention / Logpush 配置）。
- **A5** 车型能效与州电价来自 EIA / fueleconomy.gov 等美国政府公开源。来源：PRD §8 Data Contract。是否构成美国政府公共领域作品可自由引用，PRD §8 已主张；本阶段**不重复断言**，改为在页面写"数据来源 + 更新日期 + 计算公式"，不主张版权豁免。

### 2.5 缺失信息

- M1 运营主体（自然人/公司、注册地）—— Legal 未定 → **P0**
- M2 适用法律与管辖地 —— PRD §9 标 `[待确认]` → P1
- M3 第三方栈最终清单（GA4 / Clarity / 广告网络 / affiliate 网络）—— Finance 未定 → P1
- M4 DCFC 公共充电费率数据源 —— PRD §8 标 `[待确认]` → P2（数据准确性，非合规阻断）
- M5 Cloudflare 访问日志保留期 —— 需查账户配置 → P1

## 3. 本阶段结论

**一句话结论**：本项目是一个"纯前端、无账号、无支付、无 AI"的计算器工具站，合规基线风险为 🟢 低（与 PRD §9 判定一致）；但引入广告/分析/affiliate 后即升为 🟡 中，必须在**上线任何非必要 Cookie 之前**完成 Cookie 同意闸门 + 第三方披露 + FTC 披露，且 P0 占位符（运营主体、域名邮箱）替换前不得上线。

**证据**：
- 数据清单：见 `01-data-inventory.md`（24 个字段/通道，含 3 项此前未披露项）
- 第三方映射：见 `02-third-party-mapping.md`（7 类服务，3 类 `[待确认]`）
- 风险分级：见 `03-risk-register.md`（P0 ×2 / P1 ×8 / P2 ×6）
- 法域依据：见 §5 法域调研（含 2026 现行状态核实）

**重要修正（相对 PRD §9）**：PRD §9 写"用户输入仅存在于浏览器本地 + URL 参数；无服务器存储"。这句话**字面正确但不完整**——URL 参数会进入 CDN/服务器访问日志与 Referer 头。本阶段因此新增 P1-1（ZIP 码不得出现在可分享 URL 中）。详见 `03-risk-register.md`。

## 4. 交付物

| # | 交付物 | 路径 |
|---|---|---|
| D1 | 合规评估报告（本文件） | `04-compliance/compliance-report.md` |
| D2 | 数据清单 | `04-compliance/01-data-inventory.md` |
| D3 | 第三方映射表 | `04-compliance/02-third-party-mapping.md` |
| D4 | 风险登记表 P0/P1/P2 | `04-compliance/03-risk-register.md` |
| D5 | 法律页 Route Contract（含 308 别名表） | `04-compliance/04-legal-route-contract.md` |
| D6 | 禁用词/风险词清单 | `04-compliance/05-banned-expressions.md` |
| D7 | QA 合规验收点 | `04-compliance/06-qa-compliance-checklist.md` |
| D8 | Privacy 草稿 | `legal/privacy.md` |
| D9 | Terms 草稿 | `legal/terms.md` |
| D10 | Cookie Policy 草稿 | `legal/cookie-policy.md` |
| D11 | Disclaimer 草稿 | `legal/disclaimer.md` |
| D12 | About / Contact 草稿 | `legal/about.md`、`legal/contact.md` |
| D13 | 可部署静态站（法律页 + Cookie 同意 + footer 无 404） | `site/` |
| D14 | 项目控制板（事实源） | `project-control.md` |
| D15 | 下游交接摘要 | `04-compliance/handoff-summary.md` |

## 5. 法域调研（2026 现行状态核实）

> 未核实即写入法律页 = 编造。以下每条均标注核实结果与状态。

| 法域 | 适用规则 | 2026 现行状态 | 对本项目的动作 |
|---|---|---|---|
| 🇺🇸 US 联邦 | FTC Act §5（欺骗性行为）、FTC 16 CFR Part 255（背书与推荐指南） | 有效 | affiliate 披露 + 估算免责（已落地） |
| 🇺🇸 California | CCPA/CPRA；**修订条例 2026-01-01 生效**（ADMT、风险评估、网络安全审计） | ✅ 已生效（CPPA 2025-09-23 公告，OAL 批准） | 本站无 ADMT → 不适用 ADMT 条款；但广告投放 = "sell/share" → 需 **Do Not Sell/Share 链接 +  honoring GPC** |
| 🇬🇧 UK | UK GDPR + PECR；**Data (Use and Access) Act 2025 (DUAA)** 主条款 **2026-02-05 生效** | ✅ 已生效（2025-06-19 御准） | DUAA 豁免**部分低风险分析 Cookie** 的事前同意 → 复评 Cookie 分类；新增法定投诉流程（2026-06-19 起）→ Contact 页需留投诉入口 |
| 🇪🇺 EEA | GDPR + ePrivacy 指令 | ✅ 现行 | **Digital Omnibus（2025-11-19 提案）截至 2026 年中仍为草案**，EDPB/EDPS 联合意见 2/2026（2026-02-10）已出。**当前规则完全适用，不提前放松** |
| 🇩🇪 Germany | GDPR + **§25 TDDDG**（原 TTDSG，**2024-05-14 更名为 TDDDG**，§25 内容不变） | ✅ 现行 | 设备存储只有"同意"或"严格必要"两条路，**不承认正当利益**；Accept/Reject 必须同等显著（OVG Lüneburg 14 LA 1/24 认定高亮 Accept = dark pattern） |
| 🇨🇦 Canada | PIPEDA | 现行 | 基础披露即可 |
| 🇦🇺 Australia | Privacy Act 1988 / APP | 现行 | 基础披露即可 |
| 🇮🇳 India | **DPDP Act 2023 + DPDP Rules 2025** | 🟡 **分阶段生效**：Rules 2025-11-13 公告；**Stage 3（同意、通知、跨境、数据主体权利等实质义务）2027-05-13 才生效** | 当前**不产生实质义务** → 列为 P2 监控项，不提前构造合规成本 |

**结论（关键决策 K3）**：法律页按"US 主站 + EEA/UK 从严"的**单一英文版本 + 法域附录**编写，不按国家拆 5 套法律页。理由：PRD §8 的 5 国页是**费率/单位本地化的计算器页**，不是独立法律实体站点；拆 5 套会导致维护成本与不一致风险。EEA/UK 从严即可覆盖 CA/AU/IN/DE 的基础要求。

## 6. 验收清单 / 质量门槛

### 6.1 Skill 四项硬性门槛

- [x] **必须声明非法律意见** —— 见本文件 §9 免责声明；`legal/*.md` 每页页脚均有 "Not legal advice" 表述
- [x] **必须列第三方服务** —— 见 `02-third-party-mapping.md`（7 类，含 3 类 `[待确认]` 槽位）
- [x] **必须有联系方式占位** —— `privacy@[DOMAIN]` 占位；**但占位符 ≠ 可上线**，见 P0-1
- [x] **不得承诺未实现能力** —— 见 §8：法律页未承诺任何未实现功能；计算器引擎、affiliate 位均为"未启用"，文中如实表述

### 6.2 Skill 四项验收清单

- [x] **法律页与实际数据收集一致** —— 数据清单 24 项 → Privacy 逐项对应；明确写"我们不宣称零数据收集"（服务器日志客观存在）
- [x] **第三方服务全部披露** —— 已确认的 2 类（Cloudflare、数据源）+ 待确认 3 类均在 Privacy 中有段落（待确认项标注"尚未启用"）
- [x] **高风险素材/IP 有免责声明或替代方案** —— Tesla 商标：无 logo、描述性使用、"Not affiliated with Tesla, Inc." 声明（每页 Tesla 相关处）
- [x] **footer/legal route 不会 404** —— 已构建并自检通过，见 §10 验证证据

### 6.3 本阶段未能关闭的项

- [ ] 运营主体与真实域名邮箱（P0-1）—— 需 Owner 提供
- [ ] 适用法律/管辖地拍板（P1-2）—— 需 Legal 拍板
- [ ] 第三方栈最终确认（P1-6）—— 需 Finance 定稿

## 7. 风险摘要

| 级别 | 数量 | 摘要 |
|---|---|---|
| **P0** | 2 | 运营主体/域名邮箱未定；Cookie 同意闸门（当前已默认关闭，属上线前硬闸） |
| **P1** | 8 | ZIP 入 URL、会话录制采集输入、第三方字体、FTC 披露、商标复核、第三方清单、数据新鲜度、GDPR Art.27 代表 |
| **P2** | 6 | India DPDP 2027、EU Digital Omnibus、UK DUAA 复评、CCPA 2026 条例、WCAG 无障碍、儿童数据 |

完整登记表见 `03-risk-register.md`。

## 8. 关键决策记录

| ID | 决策 | 理由 | 影响 |
|---|---|---|---|
| **K1** | 不产出独立 `/refund` 路由；退款/无购买条款并入 Terms「No Purchases」章节 | PRD §5 NOT-DO 无支付、§10 无订阅 → 独立退款页是无内容空页，且会稀释 footer。PRD §8 Route Contract 亦未列 `/refund` | `/refund*` 别名 308 → `/terms#no-purchases`；footer 不放退款链接 |
| **K2** | Cookie 同意机制**默认全部关闭**（所有非必要脚本 `enabled: false`），但机制本身完整可运行 | PRD §9 标第三方 `[待确认]`、Finance 未定 → 在确认前加载任何追踪脚本即为 P0 违规 | 上线第三方脚本 = 单点开关翻转 + 跑 QA-GATE-01 |
| **K3** | 法律页单一英文版 + 法域附录，不按 5 国拆分 | 见 §5 结论 | 降低维护成本，避免 5 份不一致 |
| **K4** | 字体与所有静态资源**自托管**，不引 Google Fonts | 德国 AG München 判决（2022）认定未经同意从 Google Fonts CDN 加载资源违反 GDPR；且消除第三方请求面 | `site/` 零第三方资源请求 |
| **K5** | 首页只做"合规外壳"，**不实现计算器** | 计算器需要 EIA/EPA 真实费率与能效数据（PRD §8 Data Contract）。本阶段无该数据，按 Skill「没有证据的数据不要编造」**禁止编造费率** | 计算器引擎归 07-实现阶段；首页 footer/banner/声明可供 QA 立即验收 |
| **K6** | URL 分享参数改用**州代码**而非原始 ZIP | 见 P1-1：ZIP 属准标识符，且会进入访问日志与 Referer | 需下游 Tech 在实现序列化时遵守 |
| **K7** | 设置 `Referrer-Policy: strict-origin-when-cross-origin` | 限制跨站 Referer 泄露查询串，配合 K6 | 已写入 `site/_headers` |
| **K8** | Cookie 同意存储采用 "Reject / Accept / Manage" 三按钮**同等视觉权重** | §25 TDDDG 与 OVG Lüneburg 14 LA 1/24 的 Equal-Choice 要求 | 已实现于 `site/src/consent.js` + `styles.css` |

## 9. 免责声明

**本报告及附带的法律页草稿不构成法律意见（Not legal advice）。** 本文档由 AI 依据公开 PRD 与公开法域信息生成，产出的是**可复核的合规草案**，用于降低上线风险与平台审核失败概率，不替代执业律师针对具体事实的审查。所有法域结论均标注依据与生效状态；标注 `[待确认]` 的项在 Owner 或 Legal 确认前不得视为已解决。涉及生产部署、真实付费、公开发布的动作，本阶段未执行且不应由本阶段自动执行。

## 10. 验证证据

| 检查 | 命令/方式 | 结果 |
|---|---|---|
| Preflight | `python scripts/check_setup.py` | 通过，无 MISSING |
| 交接完整性 | `python scripts/validate_handoff.py 04-compliance/handoff-summary.md` | 见 §11 |
| 合规报告结构 | `python scripts/validate_compliance_docs.py 04-compliance/compliance-report.md` | 见 §11 |
| 路由 404 / footer 链接 | `python site/build.py --check` | 见 §11 |

（运行输出见 `04-compliance/VERIFICATION.md`）

## 11. 已知限制（交付时必须说明）

| # | 限制 | 影响 | 建议 |
|---|---|---|---|
| L1 | **未实现计算器引擎**（决策 K5） | 首页是合规外壳，不含计算功能与任何费率数字 | 需要 EIA/EPA 真实数据后由 07-实现阶段完成；本阶段禁止编造费率 |
| L2 | **法律页含占位符** `[OPERATING ENTITY]` / `[CONTACT EMAIL]` / `[JURISDICTION]` | 占位符未替换前不得上线（P0-1） | Owner/Legal 回填后重跑 `site/build.py` |
| L3 | **尾斜杠行为未实测** | 取决于托管方配置；已在 `_redirects` 中刻意规避重定向环 | 上线后按 §4.7 实测，必要时统一 canonical 写法 |
| L4 | **未做真实浏览器 / Lighthouse / Rich Results 验证** | 本阶段只做了结构自检与本地 HTTP 冒烟（200/404） | 由 QA 阶段用真实环境完成（PRD §11 要求 Lighthouse ≥ 90、Rich Results 通过） |
| L5 | **未验证 Cloudflare 日志保留期与跨境传输机制** | Privacy 中相应段落为 `[TO BE CONFIRMED]` | Tech 查账户配置后回填 |
| L6 | **法律页为英文单版**（决策 K3） | 未做 5 国本地语言版本 | 若某国页流量显著，再评估本地化法律页 |
| L7 | **未引入 CSP** | 后续注入第三方脚本时不会被 CSP 拦截（有意为之，避免阻碍 Finance 选型） | 第三方栈定稿后补 CSP 白名单（列为 P2 待办） |
| L8 | **法域信息具有时效性** | 截至 2026-09-10 核实；EU Digital Omnibus 仍在立法进程 | 每季度复评；India DPDP 2027-05-13 前复评 |
| L9 | **Cookie 同意未做真实跨浏览器测试** | 仅实现逻辑，未在 Safari/ITP、Firefox ETP、GPC 扩展下实测 | QA 阶段验证（ITP 会限制第一方 Cookie 生命周期） |
| L10 | **本报告非法律意见** | 不能替代执业律师审查 | 上线前建议由 Legal 复核 P0-1、P1-2、P1-5、P1-8 |

## 12. 状态

**[NEEDS_REVIEW]** —— P0-1（运营主体 + 域名邮箱）与 P1-2（管辖地）未由 Owner/Legal 回填前，不可标记 DONE；但本阶段草案、Route Contract、Cookie 闸门与可部署站点已完整交付，可并行进入下游阶段。
