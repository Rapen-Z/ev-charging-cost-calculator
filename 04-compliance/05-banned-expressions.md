# 阶段 5 — 禁用词 / 风险词清单

> 给文案（Content）、设计（Design）、前端（Tech）、QA 的**可执行禁词表**。
> 使用方式：文案定稿前跑一遍本文的 A→E 组；CI 可把 B 组做成正则硬闸。

## A 组 — 商标与归属（Tesla / 车型品牌）🔴 最高优先

❌ **禁止**
- `official` / `officially` / `Official Tesla Calculator`
- `approved by` / `certified by` / `endorsed by` / `partnered with`
- 使用 Tesla / Ford / Hyundai / Rivian 等**任何** logo、官方配色、官方视觉
- 域名含 `tesla`（PRD §9 已弃 `teslachargingcost.com`）
- `Tesla's calculator`、`the Tesla app says`

✅ **允许（描述性使用）**
- `Charging cost for a Tesla Model Y`
- `Tesla Model Y charging cost estimate`
- `Compatible with / for use with Tesla vehicles`

📌 **强制附加**：任何提及 Tesla 的页面，在提及处附近或 footer 出现：
> `Not affiliated with, endorsed by, or sponsored by Tesla, Inc. "Tesla", "Model Y" and other marks are trademarks of their respective owners.`

📌 **全站 footer 商标归属模板句**（每页都要）：
> `All vehicle makes, models, and brand names are trademarks or registered trademarks of their respective owners. Use of these names is for identification and descriptive purposes only and does not imply affiliation or endorsement.`

## B 组 — 数据准确性与精度宣称 🔴

❌ **禁止**
- `100% accurate` / `100% exact` / `perfectly accurate`
- `exact cost` / `your exact bill` / `precise bill amount`
- `real-time rates` / `live pricing` / `up-to-the-minute`
- `official EIA data` / `official EPA figures` → 改 `data published by the U.S. Energy Information Administration (EIA)`
- `we guarantee this matches your electricity bill`
- `to the penny` / `down to the cent`
- `verified by` / `audited by`

✅ **允许**
- `estimate` / `estimated monthly cost` / `approximate`
- `based on EIA state average residential rates, updated {date}`
- `typical` / `on average` / `in most cases`
- `your actual cost will depend on your utility rate plan, driving habits, and weather`

📌 **强制**：每个结果区附近显示 `Estimate only — not a quote.` 与 `Rates updated {date}`。

## C 组 — 承诺与保证 🔴

❌ **禁止**
- `guaranteed` / `guarantee` / `guarantees you will save`
- `risk-free` / `no risk`
- `always free` / `free forever` / `will never charge`
- `unlimited` / `no limits`
- `you will save $X` → 改 `estimated savings of about $X`
- `#1` / `best` / `the most accurate calculator online`（不可证明的最高级）

✅ **允许**
- `free to use`（**当前事实**，若未来收费须同步改文案）
- `no signup required`（**当前事实**，PRD §5 NOT-DO）
- `estimated savings`

## D 组 — 隐私与合规自证 🟡

❌ **禁止**
- `We do not collect any data` / `We collect zero data` / `No data is collected`
  → **虚假陈述**：Cloudflare 访问日志客观存在（IP/UA/URL）。这是本清单最重要的一条（B14）。
- `GDPR compliant` / `CCPA compliant` / `fully compliant`
  → 合规性自证不可证明，且可能构成 FTC §5 欺骗性陈述。
- `bank-level security` / `military-grade encryption`
- `we never share your data` → 改 `we do not sell your personal information` 并说明实际情况
- `anonymous by default`（GA4/广告未启用时可说，启用后即为假）

✅ **允许**
- `Your calculator inputs are processed in your browser and are not stored on our servers.`
- `We do not require an account and do not ask for your name, email, or payment details.`
- `We do not sell your personal information.`（**仅在未启用广告/affiliate 前为真**；启用后必须改为提供 opt-out）

## E 组 — 联盟营销与广告 🟡

❌ **禁止**
- `we recommend` + 未披露佣金关系
- `best charger for you`（暗示中立评测）
- `official partner of {brand}`
- 在 footer 之外才披露（披露必须在**首个 affiliate 链接上方**）

✅ **允许 / 强制**
- `We may earn a commission when you purchase through links on this page. This does not affect your price.`
- `Some links on this page are affiliate links.`

## F 组 — 项目特定禁词（来自 PRD NOT-DO）🟡

| 禁词/表述 | 原因 |
|---|---|
| `trip planner` / `route cost` / `road trip` | PRD §5 NOT-DO：首版不做（Phase 2 再评） |
| `total cost of ownership` / `TCO` / `insurance cost` / `maintenance cost` | PRD §13：TCO/保险/维护不进计算器 |
| `charging station map` / `find chargers near me` | PRD §5 NOT-DO：不做充电桩地图 |
| `sign up` / `create account` / `log in` | PRD §5 NOT-DO：无账号 |
| `AI-powered` / `AI-generated` | PRD §5 NOT-DO：无 AI 生成 |
| `E85` / `time-of-use rates` | PRD §13：无搜索量，不做 |

## G 组 — 分析埋点禁传字段（给 Tech）🔴

分析事件参数**绝对不得**包含：
- ZIP code（原始）
- 完整 URL 查询串
- 具体电价数值、里程数值、油价数值（只允许"是否修改过"这类布尔/枚举维度）
- 任何表单输入原文
- 完整 IP（依赖 GA4 默认处理，不得自行采集回传）

## H 组 — 深色模式（Dark Patterns）禁用（Cookie Banner）🔴

依据：§25 TDDDG、OVG Lüneburg 14 LA 1/24、EDPB 指南、CCPA 2026「选择对称性」要求。

❌ **禁止**
- 「Accept」彩色高亮 + 「Reject」灰化/弱化 → **Equal Choice 违规**
- 预勾选的分析/广告复选框（CJEU Planet49 C-673/17）
- 关闭 banner、滚动页面、继续浏览 = 同意（无主动动作，无效）
- 「Reject」藏在二级菜单或多个点击之后
- 拒绝后在短期内重复弹窗（欧盟 Digital Omnibus 草案拟定为 6 个月内不得重问）
- Cookie wall（无付费替代方案下的强制同意，EDPB Opinion 08/2024）
- 以"正当利益"作为追踪的法律基础（§25 TDDDG 不承认）

✅ **本项目实现**
- `Accept all` / `Reject all` / `Manage` 三按钮**同等尺寸、同等视觉权重**（见 `site/src/styles.css`）
- 默认全部非必要分类 `false`
- footer 常驻 `Cookie settings` 重开入口
- 同意状态含版本号 + 时间戳，存于第一方 `cc_consent`

## 施行方式

1. **Content 阶段**：文案定稿前逐组自查，输出《禁词自查表》
2. **Design 阶段**：视觉稿不得引入 A 组商标元素、H 组深色模式
3. **Tech 阶段**：把 B 组、D 组做成正则硬闸（构建期扫描 Markdown/HTML），命中即 fail
4. **QA 阶段**：`06-qa-compliance-checklist.md` 的 QA-COPY-01～05 逐项验证
