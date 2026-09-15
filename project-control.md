# project-control — EV 充电成本计算器（FuelCost Compass）

> Kanban / 项目控制板。**这是唯一事实源**，聊天只做进度可见性与人工确认。
> Skill：`student-site-compliance-pipeline` v2.3.0 ｜ 唯一开发依据：PRD v1（2026-09-09）

## Project Launch Card

| 项 | 值 |
|---|---|
| 关键词 | `ev charging cost calculator` / `tesla model y charging cost` / `cost to charge ev` / `ev vs gas cost calculator` / `phev vs hybrid cost calculator` |
| 域名 | `evchargingcostcalculator.com`（推荐）/ `costtochargeev.com`（副选） |
| 目标市场 | US（主）+ UK / CA / AU / IN / DE |
| 项目类型 | 计算器工具站 + 数据聚合混合型（Cloudflare Pages 静态） |
| 约束 | 无账号/登录/付费墙、无上传、无 AI 生成、无 UGC、无地图、无 TCO |
| 账号准备 | 本阶段无硬性要求；域名邮箱待开通（阻塞上线） |

## 看板

| ID | 阶段 | 任务 | 状态 | 阻塞于 | 解锁动作 |
|---|---|---|---|---|---|
| S01 | 01-discovery | 深潜报告（PDR 28/35） | ✅ DONE | — | — |
| S02 | 02-product | PRD v1 + 四动力总成扩展 | 🟡 NEEDS_REVIEW | Finance / Legal / SEO 回填 | 上游回填 |
| **S03** | **04-compliance** | **合规与基础法律页面** | 🟡 **NEEDS_REVIEW** | **P0-1 / P1-2 / P1-6** | 见下 |
| S03-a | 04 | 数据清单 | ✅ DONE | — | — |
| S03-b | 04 | 第三方映射 | ✅ DONE | — | — |
| S03-c | 04 | 风险分级 | ✅ DONE | — | — |
| S03-d | 04 | 法律页 Route Contract | ✅ DONE | — | — |
| S03-e | 04 | 禁用表达清单 | ✅ DONE | — | — |
| S03-f | 04 | Privacy/Terms/Cookie/Disclaimer 草稿 | ✅ DONE | — | — |
| S03-g | 04 | 可部署站点 + Cookie 闸门 + 自检 | ✅ DONE | — | — |
| S03-h | 04 | QA 验收点 + 交接摘要 | ✅ DONE | — | — |
| S04 | finance | 变现 spec（广告网络 / affiliate 品类 / 定价） | ⬜ TODO | — | Finance 定稿后回填 P1-6 |
| S05 | legal | 管辖地、Art.27 代表、商标文案终审 | ⬜ TODO | S04 | 拍板后替换 `[JURISDICTION]` |
| S06 | seo | Semrush Volume/KD/CPC 回填 | ⬜ TODO | — | 本地查询 |
| S07 | content | 9 区块文案 | ⬜ TODO | S03 禁词表 | 按 `05-banned-expressions.md` 自查 |
| S08 | design | 视觉真源 | ✅ DONE | — | 见「视觉系统」章；token 化已落地 |
| S09 | tech | 计算器引擎 + 数据管道 | ✅ DONE | — | 已用 EPA/EIA 真实数据落地（未编造任何费率） |
| S09-a | tech | 真实数据采集（EPA 车型 / EIA 州电价 / EIA 油价 / DCFC / 5 国） | ✅ DONE | — | `data/collect_*.py` |
| S09-b | tech | ZIP→州映射表（PRD §8 MVP-4，纯本地、不进 URL） | ✅ DONE | — | `data/collect_zips.py`，30 个真值校验通过 |
| S09-c | tech | 计算器引擎（JS + Python 双实现 + 公式一致性测试） | ✅ DONE | — | `site/src/calc.js` ↔ `site/gen.py` |
| S09-d | tech | 页面生成（42 路由）+ 构建期禁用表达硬闸 | ✅ DONE | — | `site/gen_pages.py` + `site/build.py` |
| S09-e | tech | 内链（首页列全部内页 / 车型↔车系↔州互链） | ✅ DONE | — | PRD §8 内链规则 |
| S09-f | design+tech | 设计系统 token 化（色/字/距/动效）+ 边界光束 | ✅ DONE | — | `src/styles.css` 重写；`--beam-*` token |
| S09-g | design+tech | 思考球（Canvas 2D）+ 异步状态语义 + 结果脉冲 | ✅ DONE | — | 新增 `src/orb.js`；T9 覆盖 |
| S10 | qa | QA_GO + Compliance_GO | 🟡 PARTIAL | P0-1（运营主体占位符） | `python verify.py` 已全绿（T1–T9） |
| S11 | launch | Owner Review → Launch | ⬜ TODO | **P0-1 必须清零** | 人工确认 |
| S12 | review | Data Review + 复盘回写 | ⬜ TODO | S11 | — |

## 硬闸门（不可跳过）

| 闸门 | 条件 | 状态 |
|---|---|---|
| PRD / Route Contract | PRD v1 已出 | ✅ |
| 定价 / 合规 | **本阶段**；P0 未清零 | 🟡 **NEEDS_REVIEW** |
| SEO-Copy Freeze | 未开始 | ⬜ |
| Visual Style Rationale | 已出（见「视觉系统」章 rationale） | ✅ |
| Data Contract | PRD §8 已初稿；DCFC 源待确认 | 🟡 |
| 实现 | 计算器 + 42 路由已构建，`verify.py` 全绿 | ✅ |
| PM / SEO / 合规复核 | 未开始 | ⬜ |
| QA | 自动化已过（引擎一致性 20488 断言 / DOM T1–T9）；人工 QA 未做 | 🟡 |
| Owner Review | **需要人工确认**（含 P0-1 解锁） | ⬜ |
| Launch | **需要人工确认**（生产 DNS/域名绑定） | ⬜ |

## 视觉系统（S09-f / S09-g）

**Rationale**：站点是「精密仪器 + 编辑排版」气质，不是消费级 SaaS。因此：暖纸底、深森林绿单强调色、发丝级分隔线、直角、零柔和投影、衬线标题。动效只服务于**层级**与**等待**，不做装饰性堆砌——全页仅 0.7% 像素带强调色（实测）。

**Token 骨架**（`site/src/styles.css` §1）

| 组 | Token | 值 / 说明 |
|---|---|---|
| 纸面 | `--paper` / `--paper-2` / `--paper-3` | `#fbfaf8` / `#f3f1ed` / `#ebe7e0`，不用纯白 |
| 墨色 | `--ink` / `--ink-2` / `--ink-3` | `#16150f` / `#3d3b33` / `#6d6a60`，不用纯黑 |
| 强调 | `--accent` / `--signal` / `--signal-hot` / `--signal-white` | `#124f3e` / `#3fae86` / `#7fe0bd` / `#f2fff9`（光束白热头部） |
| 辅助 | `--brass` / `--warn` / `--err` | `#b8862f` / `#7d4a06` / `#8f2f22` |
| 间距 | `--sp-1…9` | 4pt 基准栅格 |
| 时长 | `--dur-instant/fast/base/slow` | 120 / 180 / 320 / 560 ms |
| 缓动 | `--ease-out` | `cubic-bezier(.16,1,.3,1)`（expo-out，只动 transform/opacity） |
| 光束 | `--beam-w` / `--beam-idle` / `--beam-live` / `--beam-glow` | 2px / 26s / 7s / 可选 drop-shadow |

**边界光束**：`conic-gradient(from var(--beam-a))` 铺在 `padding: var(--beam-w)` 的环上，用 `mask-composite: exclude` 只留外圈；`@property --beam-a { syntax:"<angle>" }` 让角度可被 `@keyframes` 插值。`@property` 不支持时降级为静态渐变。

**强度分级（避免"全场都在闪"）**

| 位置 | 触发时机 | 环透明度 | 周期 |
|---|---|---|---|
| `.calc.beam`（主计算器） | 常驻低亮 | .90 → hover/focus-within 1.0 | 26s → focus 时 7s |
| `.field--beam`（输入框） | 仅 `:focus-within`，全表单同时最多 1 个 | 0 → 1 | 7s |
| `.btn.beam` / `.btn-sm.beam` | 仅 `:hover` / `:focus-visible` | 0 → 1 | 7s |
| `.card-grid a.beam` / `.faq details.beam` | 仅 hover / `[open]` | 0 → 1 | 26s |

**思考球**：Canvas 2D，`createConicGradient` 扫光环 + `globalCompositeOperation:"multiply"` 颜料场（纸面不发光，故用"墨入纸"而非叠加辉光）。`requestAnimationFrame` 由 `IntersectionObserver` + `visibilitychange` 暂停；DPR 上限 2。

| 状态 | 用途 | 速度 | 环 | 颜料 |
|---|---|---|---|---|
| `idle` | 待机 | .18 | 短弧 | 3 团，分散 |
| `working` | ZIP 查表 / 网络等待 | .85 | 整环 + 轨道高光 | 4 团 |
| `solving` | 计算中 | 1.6 | **断开环**（dash） | 5 团，收紧 |
| `done` | 命中 | .30 | 整环 | 3 团，收拢 |
| `fail` | 未命中 | 0 | **极短断环** | 静止 |

**无障碍**：`prefers-reduced-motion: reduce` 下光束 `animation: none`（保留静态渐变，透明度 .9），思考球只绘一帧静态图。实测：动画全停后仍有 0.8% 强调色像素，设计不塌。

## 阻塞与解锁

| 阻塞项 | 级别 | 解锁动作 | 责任方 |
|---|---|---|---|
| 运营主体 + 真实域名邮箱未定 | **P0** | 确定主体、开通可收信域名邮箱、替换占位符、重跑 `site/build.py` | Owner + Legal |
| 适用法律/管辖地未拍板 | P1 | Legal 拍板后替换 `[JURISDICTION]` | Legal |
| 第三方栈未确认 | P1 | Finance 定稿 → 走 `02-third-party-mapping.md` §2.3 六步变更控制 | Finance → Legal → Tech |
| GDPR/UK Art.27 代表 | P1 | Legal 判定 | Legal |
| Cloudflare 日志保留期 | P1 | 查账户配置后回填 Privacy | Tech |

## 需人工确认的动作（不自动执行）

- [ ] 域名注册与生产 DNS 绑定
- [ ] 生产部署（Cloudflare Pages）
- [ ] 任何真实付款/预算消耗
- [ ] 开通第三方服务账号（GA4 / Clarity / 广告网络 / affiliate）
- [ ] 公开发布、外链提交、社媒发布

## 本阶段产物索引

```
ev-charging-cost-calculator/
├── project-control.md                      ← 本文件
├── _review/                                视觉验证测试台（**不在部署目录内**）
│   ├── beam-lab.html                       光束技法对照 A–F
│   ├── orb-lab.html                        思考球 5 态 + 状态 chip + 预备态
│   ├── focus.html   probe.html             焦点态 / 计算样式探针
│   ├── inspect.mjs                          Puppeteer 截图 + 计算样式采集
│   ├── analyse.py                           Pillow 像素级量测（亮度环 / 脉冲 / 球态）
│   └── shots/                               截图 + report.json
├── 04-compliance/
│   ├── compliance-report.md                主报告
│   ├── 01-data-inventory.md                数据清单
│   ├── 02-third-party-mapping.md           第三方映射
│   ├── 03-risk-register.md                 风险登记 P0/P1/P2
│   ├── 04-legal-route-contract.md          Route Contract + 308 别名
│   ├── 05-banned-expressions.md            禁用词 A–H 组
│   ├── 06-qa-compliance-checklist.md       QA 验收点
│   ├── handoff-summary.md                  下游交接摘要
│   └── VERIFICATION.md                     脚本与自检输出
├── legal/                                  法律页真源（Markdown）
│   ├── privacy.md  terms.md  cookie-policy.md
│   └── disclaimer.md  about.md  contact.md
├── data/                                   真实数据（唯一事实源，禁止编造）
│   ├── collect_vehicles.py                 EPA fueleconomy.gov 车型能效（75 款）
│   ├── collect_energy.py                   EIA 861M 州电价 + EIA 周度油价
│   ├── collect_zips.py                     ZIP→州映射（USPS 派生，30 真值校验）
│   ├── vehicles.json  energy.json  regions.json  zips.json
│   └── _raw/                               原始下载物（留存备查）
├── verify.py                               一键验证：构建 + 自检 + 两套测试
└── site/                                   可部署 Cloudflare Pages 站点
    ├── build.py（构建 + 自检）  gen.py（Python 引擎 + 渲染）
    ├── gen_pages.py（42 路由生成器）
    ├── src/（page.html / calc.js / app.js / orb.js / styles.css / consent.js）
    ├── tests/（gen_cases.py / verify_engine.mjs / smoke_dom.mjs）
    ├── index.html  tesla-charging-cost-calculator/  ev-vs-gas-cost-calculator/
    ├── phev-charging-cost-calculator/  gas-cost-calculator/
    ├── ev-vs-phev-vs-hybrid-vs-gas/  charging-cost/{10 州}/
    ├── ev-charging-cost/{uk,de,ca,au,in}/  unit-converter/mpg-l100km/
    ├── privacy/  terms/  cookie-policy/  disclaimer/  about/  contact/  404.html
    └── assets/  _redirects  _headers  robots.txt  sitemap.xml
```

## 构建与验证（阶段 09 落地）

```bash
python verify.py          # 构建 + 自检 + 引擎一致性 + DOM T1–T9，一键全跑
python site/build.py      # 仅构建 + 自检
python data/collect_vehicles.py --force   # 刷新车型数据（增量，默认只补缺失）
python data/collect_energy.py             # 刷新电价/油价
```

四道自动化闸门：

| 闸门 | 覆盖 | 实现 |
|---|---|---|
| 构建自检 | 内链无 404、8 条规范路由、footer 6 链接、308 别名、零第三方资源、Cookie 闸默认关 | `site/build.py check()` |
| 禁用表达硬闸 | A–F 组正则扫描 42 页 + 闸门活性对照（防止空转） | `site/build.py check()` |
| 公式一致性 | calc.js 与 gen.py 对 2048 组输入逐字段比对（20488 断言） | `tests/gen_cases.py` + `tests/verify_engine.mjs` |
| 验收 T1–T9 | jsdom 跑真实构建产物：首屏预渲染、即时更新、EV vs Gas、PHEV 家用充电开关、国家页币种、分享 URL 复原、州页预填、ZIP 不进 URL；**T9 = 光束类在产物中、预备态被移除、思考球挂载 + canvas 降级、ZIP 状态 chip 隐藏→busy→done、结果脉冲触发且节流** | `tests/smoke_dom.mjs` |

### 视觉回归（可选，手动跑）

```bash
# 两个服务器：8899 服务部署产物，8898 服务项目根（测试台所在）
cd site && <python> -m http.server 8899 --bind 127.0.0.1 &
<python> -m http.server 8898 --bind 127.0.0.1 &
cd _review && <node> inspect.mjs        # 截图 + 计算样式
<python> analyse.py                      # 像素量测 → shots/report.json
```

## 部署（Cloudflare Workers）

纯静态站点，用 **Workers Static Assets** 部署（无后端；ZIP 查表是前端 `fetch('/assets/zips.json')`）。

```bash
# 认证：用户本机 wrangler login（OAuth 跳浏览器授权），授权文件落
#       ~/.config/.wrangler/config/default.toml，与隔离工作区 wrangler 共用
wrangler deploy     # 隔离工作区：C:/Users/13568/.workbuddy/binaries/node/workspace/node_modules/wrangler/bin/wrangler.js
```

- 配置：`wrangler.toml`（`assets.directory=./site`，`not_found_handling="404-page"`）+ `worker.js`（纯透传；ASSETS 已原生处理 `_redirects`/`_headers`/404）。
- 线上地址：`https://ev-charging-cost-calculator.1356864775.workers.dev`
- **Workers Static Assets 会读 `_redirects`，但状态码不能是 `404`**——原 `build.py` 里的 `/* /404 404` 触发 `Invalid _redirects ... Got 404`，已删除该行，404 兜底交给 `not_found_handling`。改 `build.py` 时务必保留此约束。
- 正式域名：需在 CF 控制台给 Worker 加 Custom Domain；`robots.txt` 当前写死 `evchargingcostcalculator.com`。

## 复盘回写（待 S12 填写）

- P0/P1 实际发生情况：
- 卡点与平台限制：
- 外链效果 / 转化数据：
- Kill / Iterate / Scale 决策：
