# 阶段 4 — 法律页 Route Contract

> canonical route + 别名 308 规则 + 页面契约。下游前端/QA 直接消费本文件。
> 依据：PRD §8 Route Contract 初稿（法律页那一行）+ 本阶段 §5 法域调研。

## 4.1 Canonical Routes

| Canonical | 页面 | 语言 | Schema | Index | 变更频率 |
|---|---|---|---|---|---|
| `/privacy` | Privacy Policy | en | `WebPage` | ✅ index, follow | 低（随第三方变更） |
| `/terms` | Terms of Service | en | `WebPage` | ✅ index, follow | 低 |
| `/cookie-policy` | Cookie Policy | en | `WebPage` | ✅ index, follow | 低（随第三方变更） |
| `/disclaimer` | Disclaimer | en | `WebPage` | ✅ index, follow | 低 |
| `/about` | About | en | `WebPage` | ✅ index, follow | 低 |
| `/contact` | Contact | en | `WebPage` + `ContactPoint` | ✅ index, follow | 低 |
| `/404` | Not Found | en | — | ❌ noindex | — |

**规范约定**
- Canonical **不带尾斜杠**（与 PRD §8 中 `/privacy /terms /cookie-policy /disclaimer /about /contact` 写法一致）
- 每个法律页输出 `<link rel="canonical" href="https://{DOMAIN}{route}">`（自引用、干净 URL、无查询串）
- 文件落盘为 `{route}/index.html`，Cloudflare Pages 对 `/privacy` 与 `/privacy/` 均返回该 index.html
- 全部法律页 `noindex` 为**否**（PRD §8 只要求 noindex 参数变体与 thank-you 页，法律页需可被索引与被引用于 GSC）

## 4.2 别名 → 308 Permanent Redirect

> 规则来源：Skill「若用别名必须 308 redirect」。所有别名统一 308（保留 SEO 权重、避免链式跳转）。

| 别名 | 308 → | 理由 |
|---|---|---|
| `/privacy-policy` | `/privacy` | 常见外部引用写法 |
| `/privacy-policy/` | `/privacy` | 带尾斜杠变体 |
| `/privacypolicy` | `/privacy` | 拼写变体 |
| `/terms-of-service` | `/terms` | 常见写法 |
| `/terms-and-conditions` | `/terms` | 常见写法 |
| `/tos` | `/terms` | 缩写 |
| `/terms-of-use` | `/terms` | 常见写法 |
| `/cookie` | `/cookie-policy` | 简写 |
| `/cookies` | `/cookie-policy` | 简写 |
| `/cookie-notice` | `/cookie-policy` | 简写 |
| `/legal-disclaimer` | `/disclaimer` | 简写 |
| `/contact-us` | `/contact` | 常见写法 |
| `/about-us` | `/about` | 常见写法 |
| `/refund` | `/terms#no-purchases` | **决策 K1**：无支付 → 不设独立退款页 |
| `/refund-policy` | `/terms#no-purchases` | 同上 |
| `/returns` | `/terms#no-purchases` | 同上 |

**实现方式**：Cloudflare Pages `_redirects` 文件（见 `site/_redirects`），尾部加通配 `/*  /404  404`。共 **16 条**。

> ⚠️ **刻意不含**规范路由自身的尾斜杠变体（如 `/disclaimer/` → `/disclaimer`）。原因：Cloudflare Pages 对目录索引的尾斜杠行为随配置而异，若托管方本身会把 `/disclaimer` 重定向为 `/disclaimer/`，再叠加 ` /disclaimer/ → /disclaimer` 会形成无限重定向环。因此尾斜杠规范化交由托管方处理，**上线后需实测确认**（见 §4.7）。

## 4.7 上线后必须实测的托管行为

| 项 | 期望 | 若不符的处理 |
|---|---|---|
| 请求 `/privacy` | 直接 200 返回 `privacy/index.html`，**无跳转** | 若被 301/308 到 `/privacy/`，则把 canonical 统一改为带尾斜杠版本，并同步 `sitemap.xml` 与 canonical 标签 |
| 请求 `/privacy/` | 200（或 308 到 `/privacy`，二选一，但**必须唯一**） | 同上，保持全站一致 |
| 请求 `/refund` | 308 → `/terms#no-purchases` | — |
| 请求不存在路径 | **404 状态码**（不是 200 软 404） | 检查 `/*  /404  404` 是否生效 |

## 4.3 Footer 链接契约（给前端）

Footer **必须**包含且仅包含以下法律链接，顺序固定：

```
Privacy · Terms · Cookie Policy · Disclaimer · About · Contact
```

附加要求：
1. 每个链接使用 **canonical route**，不得使用别名
2. 每个链接 `href` 为绝对路径（`/privacy` 形式），非相对路径
3. **必须**包含一个「Cookie settings」按钮/链接（不是超链接到页面，而是重新打开同意面板）——GDPR Art.7(3)「撤回同意应与给出同意同样容易」，德国监管要求 footer 重开入口为强制项
4. Tesla 相关页面：footer 上方必须有 `Not affiliated with Tesla, Inc.` 行
5. 全站 footer 版权行包含商标归属声明（见 `05-banned-expressions.md` A 组模板句）

**验收**：❗ 任何 footer 链接返回 404 即本阶段不通过（Skill 硬门槛）。

## 4.4 每页必备元素（QA 逐项核对）

| 元素 | 位置 | 强制 |
|---|---|---|
| `<title>` 唯一且含页面名与站点名 | `<head>` | ✅ |
| `<meta name="description">` | `<head>` | ✅ |
| `rel=canonical` 自引用 | `<head>` | ✅ |
| `robots` = `index, follow` | `<head>` | ✅ |
| 「Last updated」日期（法律页） | 正文顶部 | ✅ |
| 「Not legal advice」表述 | 正文底部 | ✅ |
| 联系邮箱（占位符上线前必须替换） | 正文 + footer | ✅ |
| Cookie settings 重开入口 | footer | ✅ |
| 商标归属声明 | footer | ✅ |
| 隐私/条目的章节锚点 `id` | 正文 | ✅（供跨页深链） |

## 4.5 与 PRD Route Contract 的偏差记录

| 项 | PRD §8 | 本阶段 | 原因 |
|---|---|---|---|
| 退款页 | 未列 | 不新增，别名 308 到 Terms | 无支付（K1） |
| Cookie settings | 未列 | 新增为 footer 强制项 | GDPR Art.7(3) + 德国监管强制 |
| 法律页 schema | PRD 只给前 5 类页面 schema，法律页标 "—" | 统一 `WebPage`，Contact 加 `ContactPoint` | PRD 未指定；`WebPage` 是保守且 Rich Results Test 安全的选择，不虚构 `Organization` 等需要真实主体信息的类型（P0-1 未解） |

## 4.6 参数变体与 noindex

PRD §8：「noindex：任何 thank-you/参数变体」。
本阶段实现：所有法律页 canonical 指向**无查询串**的干净 URL；由于法律页不接受业务参数，无需额外 noindex 规则。计算器页（`?st=&mi=&rate=` 等）由下游实现时统一 canonical 到干净 path。
