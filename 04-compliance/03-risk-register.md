# 阶段 3 — 风险分级登记表

> P0 = 不能上线 ｜ P1 = 需修复或明确披露后才能上线 ｜ P2 = 可上线后跟进
> 每条含：依据、解锁动作、责任方、是否已在本阶段处置

## P0 — 不能上线

| ID | 风险 | 依据 | 当前处置 | 解锁动作 | 责任方 |
|---|---|---|---|---|---|
| **P0-1** | **运营主体身份与联系邮箱未确定**：法律页只能写 `[OPERATING ENTITY]` / `privacy@[DOMAIN]` 占位符 | GDPR Art.13(1)(a) 要求识别控制者身份；FTC §5 禁止虚假陈述；Google AdSense / affiliate 网络审核要求真实联系信息；Skill 常见坑 #3「用 Gmail/占位邮箱冒充域名邮箱」 | 🟡 **已构造占位符并标红**，未编造实体名 | ① 确定运营主体（个人/公司 + 注册地）② **实际开通**域名邮箱（MX 生效、可收信）③ 替换 `legal/*.md` 与 `site/src/*.html` 中的全部占位符 ④ 复跑 `site/build.py` | **Owner + Legal** |
| **P0-2** | **Cookie 同意闸门**：任何非必要 Cookie/追踪脚本在获得同意前不得加载 | ePrivacy / §25 TDDDG / UK PECR；GDPR Art.7；CCPA/CPRA GPC；Skill 常见失败模式 #2 | 🟢 **已处置**：`site/src/consent.js` 实现"同意前零加载"，所有非必要 TAGS `enabled: false`，banner 三按钮等权 | 上线任何第三方脚本前，翻转 `enabled` → 必须跑通 **QA-GATE-01**（见 `06-qa-compliance-checklist.md`） | **Tech + QA** |

> P0-2 当前**不构成阻塞**（因为确实没有脚本在跑），但它是**上线闸门**：一旦 Finance 定了第三方栈，未通过 GATE 即上线 = P0 违规。

## P1 — 需修复或明确披露

| ID | 风险 | 依据 | 当前处置 | 解锁动作 | 责任方 |
|---|---|---|---|---|---|
| **P1-1** | **ZIP 码进入可分享 URL**：PRD §7 节点④「URL 参数序列化输入」+ 节点③「ZIP→电价」。ZIP 会进入 ①Cloudflare 访问日志 ②跨站 Referer 头 ③用户分享到社交平台后的可见链接 | ZIP 属准标识符，可与车型/国家组合识别个体；与 PRD §9「用户输入仅存在于浏览器本地」的字面表述存在**张力** | 🟢 **已给出替代方案 K6**：URL 序列化**州代码（如 `st=CA`）而非原始 ZIP**；ZIP 仅用于前端即时映射，不写入 URL | ① Tech 实现序列化时只写 `st` 参数 ② 若产品坚持保留 ZIP 参数，必须：缩短日志保留期 + 在 Privacy 明确披露"URL 参数可能进入访问日志" | **Tech + PM** |
| **P1-2** | **会话录制可能采集计算器输入**：Microsoft Clarity 类工具回放 DOM，可能捕获用户输入的里程/电价 | 超出"分析"目的的意外收集；GDPR 数据最小化 Art.5(1)(c) | 🟢 **已写入约束**：启用 Clarity 前必须开启输入脱敏（`data-clarity-mask` / 或禁用计算器区域录制） | ① 在 `consent.js` Clarity 配置中启用 masking ② QA 验证录制回放中无输入值 ③ 若无法验证 → 不在计算器页加载 | **Tech** |
| **P1-3** | **第三方字体/CDN 资源**：引入 Google Fonts 等会在未经同意时向第三方发起请求并暴露访客 IP | 德国 AG München 判决（2022，Google Fonts 案）；§25 TDDDG 不承认正当利益 | 🟢 **已处置（K4）**：全部资源自托管，`site/` 零第三方请求 | 下游 Design/Tech 不得重新引入外部字体或 CDN JS；如需字体，自托管 | **Design + Tech** |
| **P1-4** | **FTC affiliate 披露缺失**：PRD §10 规划 affiliate（家充桩/车险/太阳能），PRD §9 已识别需 FTC 披露，但品类未定 | FTC 16 CFR Part 255（Endorsements）；FTC Act §5 | 🟢 **已预留合规组件**：`site/src/layout.html` 中 `affiliate-disclosure` 区块，`enabled: false` 时不渲染 | ① Finance 定品类 ② 启用披露组件（必须在**首个 affiliate 链接上方**，不能只在 footer）③ Legal 出披露文案 | **Finance + Legal** |
| **P1-5** | **Tesla 商标使用**：PRD §9 要求描述性使用、无 logo、每页 "Not affiliated with Tesla, Inc." | 商标淡化与混淆风险；PRD §9 已列为 Legal 重点 | 🟢 **已落地**：`site/src/layout.html` 全局 trademark 声明 + Tesla 相关页条件化 "Not affiliated with Tesla, Inc." | ① Legal 复核文案措辞 ② 建立素材检查：不得出现 Tesla logo/官方视觉 | **Legal + Content** |
| **P1-6** | **第三方栈未最终确认**（GA4/Clarity/广告网络）：PRD §9 标 `[待确认]`，Finance 未定 | 第三方全部披露是 Skill 硬门槛；未披露即上线 = P0 | 🟢 **已按"先披露后启用"处理**：`02-third-party-mapping.md` 与 Privacy 均留槽位并写明"尚未启用" | Finance 定稿 → 按 `02-third-party-mapping.md` §2.3 六步变更流程执行 | **Finance → Legal → Tech** |
| **P1-7** | **数据新鲜度 = 误导性陈述风险**：PRD §11 要求"Rates updated ≤ 35 天"，PRD 自身把"数据过期 = 可信度崩塌"列为 P1 | 展示过期费率可能对消费者构成 FTC §5 欺骗性行为 | 🟢 **已在 Disclaimer 写明估算性质 + 更新日期字段**，并禁止精度类表述（B6/B7） | ① 建立 `rates.json` 的 `updated_at` 字段与构建期校验（>35 天则 CI 失败）② 每页渲染 "Rates updated {date}" | **Tech + Data** |
| **P1-8** | **GDPR/UK Art.27 代表**：若运营主体在 US 但面向 EEA/UK 用户（PRD §8 含 uk/de 页），可能需指定 EEA/UK 代表 | GDPR Art.27；UK GDPR Art.27 | 🟡 **已标注为 [待确认]**，未编造结论 | 由 Legal 判定是否触发；若触发需在 Privacy 中列代表联系信息 | **Legal** |

## P2 — 上线后跟进

| ID | 风险 | 依据 / 时间线 | 动作 |
|---|---|---|---|
| **P2-1** | **India DPDP Act 2023**：实质义务（同意、通知、跨境、数据主体权利、泄露通报）**2027-05-13 才生效**（DPDP Rules 2025 于 2025-11-13 公告，分三阶段：2025-11-13 Board 成立 → 2026-11-13 Consent Manager → 2027-05-13 实质合规） | 当前**不产生实质义务** | 列入合规日历，2027 Q1 复评；不提前构造合规成本 |
| **P2-2** | **EU Digital Omnibus**：2025-11-19 提案，拟将 Cookie 规则并入 GDPR（新 Art.88a/88b）、豁免第一方聚合统计、拒绝后 6 个月内不得重复请求、支持浏览器级同意信号。EDPB/EDPS 联合意见 2/2026（2026-02-10）。**截至 2026 年中仍为草案，当前规则完全适用** | 若通过将改变 banner 设计 | 监控立法进程；**不提前放松**现有 banner 标准 |
| **P2-3** | **UK Data (Use and Access) Act 2025**：主条款 **2026-02-05 生效**，豁免部分低风险分析 Cookie 的事前同意；新法定投诉流程 **2026-06-19** 起 | 已生效 | 复评 Cookie 分类（分析类是否可降级）；Contact 页已留投诉入口 |
| **P2-4** | **CCPA/CPRA 修订条例 2026-01-01 生效**：ADMT 事前通知与选择退出（2027-01-01 起）、风险评估（2026-01-01 起新处理活动）、网络安全审计（分收入梯队 2028-2030）、**GPC 信号为基线要求**、数据泄露 30 天通报 | 已生效 | 本站**无 ADMT**（纯计算器，不做自动化重大决策）→ ADMT 条款不适用；但一旦投放广告即构成 "sell/share" → 必须提供 Do Not Sell/Share 链接 + 尊重 GPC（已写入 `05-banned-expressions.md` 与 QA） |
| **P2-5** | **无障碍 WCAG 2.2 AA**：美国公共站点 ADA 诉讼风险 | 与设计阶段相关 | 下游 Design/Tech 按 AA 达标；banner 与计算器需键盘可达、对比度达标 |
| **P2-6** | **儿童数据**：站点非面向儿童，但无年龄门；若投放广告需注意不得面向 13 岁以下定向 | COPPA / CCPA（16 岁以下 PI 归为敏感 PI） | Privacy 中声明"不面向 13 岁以下"；广告投放需排除儿童定向 |

## 风险趋势说明

- PRD §3 已列的产品风险（P0 政策依赖、P1 数据维护、P2 季节性）属**商业/运营风险**，不在本阶段合规登记表中重复登记；其中「数据维护」与本表 **P1-7** 存在交叉，已在 P1-7 中从**合规**（误导性陈述）角度重新定级。
- 本阶段相对 PRD §9 新增的合规风险共 **5 项**：P1-1、P1-3、P1-7、P1-8、P2-4。
