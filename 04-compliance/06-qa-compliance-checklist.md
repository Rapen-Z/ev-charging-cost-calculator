# 阶段 6 — QA 合规验收点与交接包

> 给 QA / 前端 / 文案的可勾选验收表。**GATE 项不通过 = 不可上线。**

## QA-GATE-01 · Cookie 同意闸门 🔴 GATE

| # | 检查 | 方法 | 期望 |
|---|---|---|---|
| 1 | 首次访问（清空 localStorage/Cookie）后，在**未做任何选择**时，浏览器 Application → Cookies 中除 `cc_consent` 外**无任何 Cookie** | DevTools → Application → Cookies | 仅 `cc_consent` |
| 2 | 同上，Network 面板中**无** `googletagmanager.com` / `google-analytics.com` / `clarity.ms` / 广告域请求 | DevTools → Network，过滤第三方域 | 0 请求 |
| 3 | 同上，Application → Local/Session Storage 中无第三方条目 | DevTools | 无 |
| 4 | 点击「Reject all」后，重复检查 1–3 | 同上 | 仍仅 `cc_consent` |
| 5 | 点击「Accept all」后，第三方脚本按分类加载 | Network | 仅已 `enabled: true` 的标签加载 |
| 6 | 刷新页面后，同意状态保持且**不再弹窗** | 手工 | 不重复弹 |
| 7 | footer「Cookie settings」可重新打开面板，且可撤回同意 | 手工 | 撤回后第三方 Cookie 被清除、脚本不再加载 |
| 8 | 「Accept all」与「Reject all」按钮尺寸、颜色、对比度**一致** | 目视 + 量取 computed style | 一致（H 组） |
| 9 | 无预勾选复选框 | 目视 | 无 |
| 10 | 关闭 banner / 滚动 / 继续浏览 **不产生**同意 | 手工 | `cc_consent` 不写入同意值 |

## QA-GATE-02 · 法律页路由与 footer 🔴 GATE

| # | 检查 | 期望 |
|---|---|---|
| 11 | footer 中 6 个法律链接（Privacy/Terms/Cookie Policy/Disclaimer/About/Contact）逐个点击 | **全部 200，无 404**（Skill 硬门槛） |
| 12 | 访问 §4.2 全部 16 个别名 | 返回 **308** 并落到正确 canonical |
| 13 | 无重定向链（别名 → 别名 → canonical） | 单次 308 |
| 14 | `/refund`、`/refund-policy`、`/returns` | 308 → `/terms#no-purchases` |
| 15 | 访问不存在的路径（如 `/nope`） | 返回 **404 状态码** + 404 页（含 footer 法律链接） |
| 16 | 每页 `<link rel=canonical>` | 自引用、无查询串、无尾斜杠 |
| 17 | 每页 `robots` meta | `index, follow` |
| 18 | `robots.txt` 可访问且未屏蔽法律页 | 200 且 Allow |
| 19 | `sitemap.xml` 含全部 6 个 canonical 法律页 URL | 含且 only canonical（无别名） |

## QA-COPY-01～05 · 文案禁词

| # | 检查 | 方法 |
|---|---|---|
| 20 | 全站无 A 组禁词（official/approved/endorsed/…） | 全文搜索，含图片 alt 与 title |
| 21 | 无 B 组精度宣称（100% accurate / exact / real-time / …） | 全文搜索 |
| 22 | 无 C 组承诺（guaranteed / free forever / unlimited / …） | 全文搜索 |
| 23 | 无 D 组自证（"we collect no data" / "GDPR compliant" / …） | 全文搜索，**重点检查 Privacy 页首段** |
| 24 | Tesla 提及页均含 `Not affiliated with Tesla, Inc.` | 逐页检查 |
| 25 | 全站 footer 含商标归属模板句 | 逐页检查 |

## QA-DATA-01～03 · 数据一致性

| # | 检查 | 期望 |
|---|---|---|
| 26 | Privacy 中列出的第三方 == `02-third-party-mapping.md` == 实际加载的脚本 | 三者完全一致（常见坑 #2） |
| 27 | Cookie Policy 的 Cookie 表 == DevTools 实际观测到的 Cookie | 一致 |
| 28 | 分享链接（计算器）URL 中**无原始 ZIP** | 只有 `st` 之类州代码参数（P1-1 / K6） |

## QA-ANALYTICS-01～03 · 埋点

| # | 检查 | 期望 |
|---|---|---|
| 29 | 分析事件参数不含 G 组禁传字段 | Network → 收集请求 payload 检查 |
| 30 | 若启用 Clarity：录制回放中**看不到**计算器输入值 | 回放验证（P1-2） |
| 31 | 分析事件不传完整 URL 查询串 | payload 检查 |

## QA-LEGAL-01～04 · 法律页内容

| # | 检查 | 期望 |
|---|---|---|
| 32 | 每页含「Last updated」日期 | 存在且真实（不得早于实际上线日） |
| 33 | 每页含「Not legal advice」表述 | 存在 |
| 34 | 联系邮箱为**真实可用的域名邮箱** | 发测试邮件确认可收（P0-1；上线前必须为真实地址，不得是占位符或 Gmail） |
| 35 | 运营主体名称已替换占位符 | 无 `[OPERATING ENTITY]` 残留 |

## QA-A11Y-01～02 · 无障碍（P2-5，建议项）

| # | 检查 | 期望 |
|---|---|---|
| 36 | Cookie banner 可纯键盘操作与关闭 | Tab 可达、焦点可见 |
| 37 | 正文对比度 ≥ 4.5:1，banner 按钮对比度 ≥ 4.5:1 | Lighthouse / axe |

## 上线前 Go/No-Go 判定

| 条件 | 判定 |
|---|---|
| GATE-01 全 10 项通过 | 必需 |
| GATE-02 全 9 项通过 | 必需 |
| COPY 20–25 通过 | 必需 |
| DATA 26–28 通过 | 必需 |
| LEGAL 32–35 通过 | 必需（34/35 依赖 P0-1 解锁） |
| ANALYTICS 29–31 | 仅在启用相应第三方后必需 |
| A11Y 36–37 | 建议 |

**Compliance_GO 条件**：上述"必需"项全绿 **且** P0-1 已解锁（真实主体 + 真实域名邮箱）。

## 交接包内容（给下游）

| 下游 | 必须读取 | 不能假设 |
|---|---|---|
| **Content（文案）** | `05-banned-expressions.md` 全组；`legal/disclaimer.md` | 不能假设可以用 "official"、"100% accurate"、"guaranteed"；不能假设 affiliate 已可上线 |
| **Design（设计）** | `05-banned-expressions.md` A 组 + H 组 | 不能假设可以用 Tesla logo 或任何品牌官方视觉；不能假设 banner 可高亮 Accept |
| **Tech（前后端）** | `04-legal-route-contract.md`；`site/src/consent.js` 的 `TAGS` 配置；`01-data-inventory.md` §1.9 | 不能假设可以引入第三方字体/CDN（K4）；不能假设 URL 可带原始 ZIP（K6）；不能假设可以直接加分析脚本（P0-2） |
| **QA** | 本文件 | 不能假设未列在第三方表中的脚本是允许的 |
| **Finance** | `03-risk-register.md` P1-4、P1-6；`02-third-party-mapping.md` §2.3 | 不能假设 affiliate 链接可在披露组件启用前上线 |
| **Legal** | `compliance-report.md` §5；`03-risk-register.md` P0-1、P1-2、P1-5、P1-8 | 不能假设管辖地已定；不能假设 Art.27 代表不需要 |
