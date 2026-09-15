# 阶段 2 — 第三方服务映射

> 映射到 Privacy / Terms：用途、共享对象、保留期、退出方式。
> 状态图例：✅ 已确定 ｜ ⏸ `[待确认]`（默认关闭，不得上线）｜ ➖ 非接收方

## 2.1 映射表

| # | 服务 | 类别 | 用途 | 共享的数据 | 角色 | 保留期 | 退出方式 | 状态 |
|---|---|---|---|---|---|---|---|---|
| T1 | **Cloudflare**（Pages / CDN / DNS / WAF） | 托管与交付 | 提供静态站点、CDN 加速、DDoS 与 bot 防护、HTTPS | IP、User-Agent、Referer、请求 URL（含查询串）、时间戳 | 处理者（Processor） | **[待确认]** 需查账户 Log Retention / Logpush | 无（严格必要，交付服务所必需）；用户可使用 VPN/隐私模式 | ✅ 已确定 |
| T2 | **Google Analytics 4** | 分析 | 流量与交互分析 | 客户端 ID（Cookie）、页面路径、事件参数、粗粒度地理（国家/地区级）、UA | 独立控制者 / 联合（Google 侧） | 建议 14 个月（GA4 可配置；EEA 惯例上限） | Cookie 同意「拒绝」；GPC 信号；Google Analytics Opt-out 浏览器插件 | ⏸ `[待确认]` — Finance 未定，**enabled: false** |
| T3 | **Microsoft Clarity** | 分析 / 会话录制 | 热图与会话回放 | 鼠标轨迹、滚动、DOM 快照、**可能包含表单/输入值** | 处理者 | 由 Microsoft 控制（**[待确认]**） | Cookie 同意「拒绝」 | ⏸ `[待确认]` — **且启用前必做输入脱敏（P1-2）** |
| T4 | **广告网络**（未定，Finance 选型中） | 广告 | 展示广告投放与归因 | Cookie/设备 ID、页面上下文、粗粒度地理 | 独立控制者 | **[待确认]** | Cookie 同意「拒绝」；GPC；CCPA「Do Not Sell or Share」链接 | ⏸ `[待确认]` — **enabled: false** |
| T5 | **Affiliate 网络**（家充桩 / 车险 quote / 太阳能，PRD §10） | 联盟营销 | 外链归因与佣金 | 外链点击、Referer、目标站设置的归因 Cookie | 独立控制者 | 由各网络控制（**[待确认]**） | 不使用即不触发；CCPA Do Not Sell/Share | ⏸ 未启用 — **启用前必须先上 FTC 披露（P1-4）** |
| T6 | **U.S. EIA**（州电价、油价） | 数据源 ➖ | 提供公开费率数据 | **无**（我们不向其发送数据） | 非接收方 | — | — | ✅ 已确定（仅作为数据来源披露） |
| T7 | **fueleconomy.gov / EPA**（EV 能效、PHEV UF） | 数据源 ➖ | 提供公开能效数据 | **无** | 非接收方 | — | — | ✅ 已确定（仅作为数据来源披露） |
| T8 | **第三方字体 / JS CDN**（Google Fonts、jsDelivr、unpkg 等） | 资源分发 | — | — | — | — | 不适用 | ❌ **已决定不引入**（决策 K4）。德国 AG München 2022 判决认定未经同意从 Google Fonts CDN 加载资源违反 GDPR |

## 2.2 当前实际生效的第三方（诚实披露口径）

**只有一个：Cloudflare（T1）。**

其余全部为"计划中、未启用、默认关闭"。因此 Privacy Policy 采用**双层写法**：
- 已启用层：逐项列 Cloudflare 与数据源，写明共享内容与保留期
- 计划层：明确写"These services are not currently enabled. We will update this policy before enabling them." —— **先披露后启用**，避免"Analytics 上线但 Privacy 没写"这一常见坑（stage-rubric 常见失败模式 #2）

## 2.3 第三方变更控制流程（给下游 Tech / Finance）

新增或替换任何第三方脚本，必须按顺序完成，否则构成 P0-2 违规：

1. 在 `02-third-party-mapping.md` 增行（用途/共享数据/保留期/退出方式）
2. 在 `legal/privacy.md`「Third-party services」同步增段
3. 在 `legal/cookie-policy.md` Cookie 表同步增行
4. 在 `site/src/consent.js` 的 `TAGS` 配置中登记，分类正确（necessary / analytics / advertising）
5. 跑 `06-qa-compliance-checklist.md` 的 **QA-GATE-01**（同意前零非必要 Cookie）
6. 更新 `legal/privacy.md` 顶部 "Last updated" 日期

> 任一步未完成 → 该脚本 `enabled` 必须保持 `false`。

## 2.4 数据处理协议（DPA）待办

| 服务 | 需要 DPA / SCC | 状态 |
|---|---|---|
| Cloudflare | Cloudflare DPA（含 SCC），随服务条款自动适用 | ✅ 需存档留证 |
| Google Analytics 4 | Google Ads Data Processing Terms | ⏸ 启用前签署 |
| Microsoft Clarity | Microsoft DPA | ⏸ 启用前签署 |
| 广告网络 | 视选型而定 | ⏸ 启用前签署 |
| Affiliate 网络 | 视选型而定 | ⏸ 启用前签署 |

## 2.5 跨境传输

站点托管于 Cloudflare 全球边缘（含美国）。EEA/UK 访客的访问日志可能传输至美国。
- 传输机制：依赖 Cloudflare 的 DPA + 标准合同条款 / 或 Data Privacy Framework（**具体机制 [待确认]，需查 Cloudflare 当前认证状态**）
- 启用 GA4/Clarity/广告后，需重评 Schrems II 影响（德国 DPA 对美国托管追踪器审查最严）
