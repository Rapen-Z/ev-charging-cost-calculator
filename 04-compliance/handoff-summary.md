# 合规与基础法律页面交接摘要

> 阶段：`04-compliance` ｜ Skill：`student-site-compliance-pipeline` v2.3.0
> 项目：EV 充电成本计算器（FuelCost Compass）｜ 日期：2026-09-10

## 当前结论

- 状态：**[NEEDS_REVIEW]**
- 一句话结论：本站点为纯前端、无账号、无支付、无 AI 的计算器工具站，合规基线风险 🟢 低（与 PRD §9 一致）；**法律页、Cookie 同意闸门、Route Contract、禁用词表、QA 验收点已全部交付并自检通过**，可并行进入下游阶段；但 **P0-1（运营主体 + 真实域名邮箱）未解前不得上线**，`[JURISDICTION]` 等占位符替换前不得标记 DONE。

**为什么不是 [DONE]**：Skill 规定只有 `[DONE] / [BLOCKED] / [NEEDS_REVIEW]` 三态。本阶段产出完整、未受阻（不输出 `[BLOCKED: SETUP_REQUIRED]`），但存在需 Owner/Legal 回填的占位符与待确认项（P0-1、P1-2、P1-8），按"不编造"原则不能自行填写，故为 `[NEEDS_REVIEW]`。

## 关键输入

- 项目：EV 充电成本计算器（ChargeCost / FuelCost Compass）
- 当前阶段：04-compliance
- 上游资料：`PRD-ev-charging-cost-calculator-v1 (2).md`（2026-09-09，唯一开发依据）
- 上游状态：PRD 自身为 `[NEEDS_REVIEW]`（待 Finance / Legal / SEO 回填）
- 目标市场：US（主）+ UK / CA / AU / IN / DE（PRD §8 五国页）

## 本阶段交付物

| 文件 | 内容 |
|---|---|
| `04-compliance/compliance-report.md` | 主报告：Preflight、输入契约、法域调研、8 项关键决策、验收自检 |
| `04-compliance/01-data-inventory.md` | 24 项字段/通道数据清单 |
| `04-compliance/02-third-party-mapping.md` | 7 类第三方映射 + 6 步变更控制 |
| `04-compliance/03-risk-register.md` | P0×2 / P1×8 / P2×6 风险登记 |
| `04-compliance/04-legal-route-contract.md` | canonical route + 16 条 308 别名 + footer 契约 |
| `04-compliance/05-banned-expressions.md` | A–H 八组禁词（含埋点禁传字段、深色模式禁用） |
| `04-compliance/06-qa-compliance-checklist.md` | 37 个验收点 + Go/No-Go 判定 |
| `legal/*.md`（6 份） | Privacy / Terms / Cookie Policy / Disclaimer / About / Contact 草稿 |
| `site/` | 可部署 Cloudflare Pages 站点（8 路由 + 同意闸门 + 自检脚本） |
| `project-control.md` | Kanban 事实源 |

**核心判断**
1. 风险等级 🟢 低（与 PRD §9 一致），但**引入广告/分析/affiliate 后升为 🟡 中**。
2. Cookie 同意闸门必须**先于**任何非必要脚本；当前所有第三方标签 `enabled: false`。
3. URL 分享参数**不得包含原始 ZIP**（改为州代码）—— 这是对 PRD §7 节点④ 的合规修正。
4. 不设独立退款页（无支付），`/refund*` 308 → `/terms#no-purchases`。
5. 全部资源自托管，不引第三方字体/CDN（德国 AG München 2022 判决）。
6. 禁止写"我们不收集任何数据"——服务器日志客观存在，该表述为虚假陈述。

**证据**：`site/build.py` 自检输出（8 路由全在、8 条内链全解析、16 条 308、零第三方资源、标签全禁用）+ 本地 HTTP 冒烟（`/`、`/privacy/`、`/assets/*`、`/robots.txt`、`/sitemap.xml` = 200，`/nope` = 404）；Skill 脚本 `validate_handoff.py` / `validate_compliance_docs.py` 输出见 `VERIFICATION.md`。

**已确认项**
- 无支付、无账号、无上传、无 AI → 不触发 `blockingRules` 的 BLOCKED
- 无硬性账号/Token/登录态要求（requirements.json 全空）
- 8 个 canonical 路由全部可访问，footer 6 个法律链接无 404
- 同意前零非必要 Cookie（机制已实现，且当前无脚本可加载）

**待确认项**
- 运营主体名称与注册地（P0-1）
- 适用法律与管辖地（P1-2，PRD §9 已标）
- 第三方栈最终清单（P1-6，Finance 未定）
- GDPR/UK Art.27 代表是否必需（P1-8）
- Cloudflare 访问日志保留期（M5）
- 数据跨境传输具体机制（M6）

## 质量门槛自检

**通过项**
- [x] 法律页与实际数据收集一致
- [x] 第三方服务全部披露（含"尚未启用"槽位）
- [x] 高风险素材/IP 有免责声明（Tesla 描述性使用 + Not affiliated 声明）
- [x] footer/legal route 不会 404（构建期自检通过）
- [x] 必须声明非法律意见（报告 §9 + 全站 footer）
- [x] 必须列第三方服务
- [x] 必须有联系方式占位
- [x] 不得承诺未实现能力

**未通过 / 未关闭项**
- [ ] 运营主体与真实域名邮箱未回填（P0-1）→ 阻塞上线
- [ ] 管辖地未拍板（P1-2）
- [ ] 第三方栈未定（P1-6）

## 风险

**P0（不能上线）**
- **P0-1** 运营主体身份 + 真实可送达域名邮箱未确定 —— 解锁：确定主体 + 实际开通 MX 可收信邮箱 + 替换全部占位符 + 重跑 `site/build.py`
- **P0-2** Cookie 同意闸门：非必要脚本在同意前不得加载 —— 当前已默认全关；解锁：启用第三方前必须跑通 QA-GATE-01

**P1（需修复或明确披露）**
- P1-1 ZIP 入 URL（改州代码 + Referrer-Policy）
- P1-2 Clarity 等会话录制须先做输入脱敏
- P1-3 第三方字体/CDN（已自托管规避）
- P1-4 FTC affiliate 披露（组件已预留，未启用）
- P1-5 Tesla 商标文案需 Legal 复核
- P1-6 第三方栈未最终确认
- P1-7 数据新鲜度 → 过期数据构成误导性陈述（需构建期 ≤35 天校验）
- P1-8 GDPR/UK Art.27 代表待定

**P2（上线后跟进）**
- P2-1 India DPDP 实质义务 2027-05-13 生效
- P2-2 EU Digital Omnibus（2025-11-19 提案，截至 2026 年中仍草案）
- P2-3 UK DUAA 2025（2026-02-05 生效）Cookie 分类复评
- P2-4 CCPA/CPRA 2026-01-01 修订条例（GPC 为基线要求）
- P2-5 WCAG 2.2 AA 无障碍
- P2-6 儿童数据（非面向 <13，广告投放需排除儿童定向）

## 给下游的最小必要信息

- 下一阶段：Finance（变现 spec）→ Legal（合规文定稿）→ SEO → Content（文案）→ Design → Tech → QA

**必须读取**
- Content：`05-banned-expressions.md` 全组 + `legal/disclaimer.md`
- Design：`05-banned-expressions.md` A 组（商标）+ H 组（深色模式禁用）
- Tech：`04-legal-route-contract.md` + `site/src/consent.js` 的 `TAGS` + `01-data-inventory.md` §1.9
- QA：`06-qa-compliance-checklist.md`
- Finance：P1-4、P1-6 + `02-third-party-mapping.md` §2.3 六步变更控制
- Legal：`compliance-report.md` §5 + P0-1、P1-2、P1-5、P1-8

**不能假设**
- ❌ 不能用 "official" / "100% accurate" / "guaranteed" / "free forever"
- ❌ 不能用 Tesla 或任何品牌 logo / 官方视觉
- ❌ 不能引入第三方字体或 CDN JS
- ❌ 不能把原始 ZIP 放进分享 URL
- ❌ 不能在披露组件启用前挂 affiliate 链接
- ❌ 不能直接加分析/广告脚本（须走六步变更控制 + QA-GATE-01）
- ❌ 不能写"我们不收集任何数据"

**建议启动 Prompt**

```text
你现在执行 ShipSolo 做站流水线的下一阶段。
项目：EV 充电成本计算器（FuelCost Compass），域名 evchargingcostcalculator.com
上游：阶段 04-compliance 已交付（见 04-compliance/handoff-summary.md）

请先读取并严格遵守：
1. 04-compliance/05-banned-expressions.md（A–H 八组禁词）
2. 04-compliance/04-legal-route-contract.md（canonical route 与 308 别名）
3. 04-compliance/03-risk-register.md（P0/P1/P2 与解锁动作）

硬约束（违反即为 P0）：
- 不得使用 official / approved / endorsed / guaranteed / 100% accurate / exact / real-time / free forever
- 不得使用任何车企 logo 或官方视觉；提及 Tesla 必须附 "Not affiliated with Tesla, Inc."
- 不得引入第三方字体或 CDN 资源（全部自托管）
- 计算器 URL 参数不得包含原始 ZIP（只写州代码 st）
- 不得在 Cookie 同意前加载任何非必要脚本
- 不得写"我们不收集任何数据"

输出：本阶段交付物 + 验收清单自检 + 下游交接摘要。
最后一行只能是：[DONE] / [BLOCKED] / [NEEDS_REVIEW]。
```

## 状态行

**[NEEDS_REVIEW]**
