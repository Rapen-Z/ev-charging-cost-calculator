# EV Charging Cost Calculator（FuelCost Compass）

一个纯静态、数据驱动的电动汽车充电成本计算器。零运行时依赖、零密钥、零第三方资源，
所有数字都来自公开数据集（EPA / EIA / USPS），没有任何一个是编造的。

线上：<https://ev-charging-cost-calculator.1356864775.workers.dev>（Cloudflare Workers Static Assets）

---

## 它算什么

```
月成本 = 里程 ÷ 能效 × 电价 × (1 + 充电损耗)
```

- **能效**取自 EPA/DOE `fueleconomy.gov`（EV 用 mi/kWh，汽油/混动用 MPG）
- **电价**取自主管机构公开数据（州住宅均价 + 公共快充网络均价估算）
- **双费率加权**：家用充电与公共快充按比例混合
- **PHEV**：按 EPA utility factor 拆分电/油里程；关闭「家用充电」即按纯油重算
- 支持城市/高速插值、冬季修正（能效 ×0.85）、ZIP → 州均价（纯本地查表，不进 URL）

页面公开计算公式与全部数据来源；结果可序列化进 URL 分享。

## 数据（真实、可核验）

| 数据 | 来源 | 产物 |
|---|---|---|
| 车型能效 **104 款 / 25 品牌**（49 EV / 13 PHEV / 20 HEV / 22 汽油） | EPA / DOE `fueleconomy.gov` web services | `data/vehicles.json` |
| 州住宅电价（51 州） | U.S. EIA Form 861M | `data/energy.json` |
| 汽油零售价（周度） | U.S. EIA | `data/energy.json` |
| DC 快充费率（网络均价，**估算**，页面已标注） | 公开网络定价页 | `data/regions.json` |
| UK / DE / CA / AU / IN 居民电价与币种 | Ofgem / Verivox / NRCan / AER / IEA | `data/regions.json` |
| ZIP → 州映射（912 个前缀，30 个真值校验） | USPS ZIP（Census 派生） | `data/zips.json` |

采集脚本 `data/collect_*.py` 均为**增量**：保留已缓存条目，只补缺失的 slug。

## 架构

```
data/collect_*.py ──► data/*.json ──┐
                                    ▼
site/src/  ─────────────────►  site/build.py  ──►  site/   （开发产物，含源文件）
  layout.html / page.html         │                    │
  styles.css（设计 token）         │                    ▼
  calc.js（纯计算引擎）            │                 dist/  （部署产物，仅可公开文件）
  app.js（交互层）                 │                    │
  orb.js / consent.js             ▼                    ▼
                            site/tests/*          wrangler deploy
```

| 层 | 文件 | 职责 |
|---|---|---|
| 数据 | `data/collect_*.py` → `data/*.json` | 抓取并缓存真实数据，唯一事实源 |
| 渲染 | `site/gen.py`、`site/gen_pages.py` | 逐路由生成 HTML；`gen.py` 同时以前端同一套公式做构建期预渲染 |
| 编排 | `site/build.py` | 读数据 → 渲染 → 拷贝资源 → 输出 `_redirects`/`_headers`/`robots.txt`/`sitemap.xml`/404 → 自检 → 暂存 `dist/` |
| 前端 | `site/src/calc.js` | 纯计算引擎（无 DOM），浏览器与测试共用同一份 |
| 前端 | `site/src/app.js` | 交互层：车型选择器、结果渲染、参考面板 |

**引擎双实现互校**：`site/src/calc.js`（前端）与 `site/gen.py`（构建期）对同一组输入必须给出完全一致的结果 —— 由 20488 条断言强制。

### 车型选择器

- 覆盖 104 款车型，按动力类型分组
- **搜索框**：车型数 > 6 时出现，按车名 / 品牌 / 级别实时筛选
- **自定义车型**：选「＋ Add your own vehicle…」可手动输入自行车的能效（EV/PHEV 用 mi/kWh，汽油/混动用 MPG），合成一条记录复用同一个计算引擎

## 构建与验证

```bash
python verify.py                # 一键全量验证（推荐）
python site/build.py            # 仅构建 + 自检 + 暂存 dist/
python site/build.py --check    # 只跑自检，不重建
```

`verify.py` 的通过标准（缺一不可）：

1. **构建 + 自检** — 42 条路由、内部链接全解析、footer 法务链接齐全、重定向单跳、零第三方资源
2. **禁用表达硬闸** — A–F 组禁令，附「闸门活性」对照防止正则空转
3. **引擎一致性** — 20488 条断言，`calc.js` 与 `gen.py` 逐字段一致
4. **DOM 冒烟 T1–T9** — jsdom 下 47 条断言

改文案或禁用表达相关代码后**必须**重跑，闸门会挡住不合规表述。

修改入口：

| 改什么 | 动哪里 |
|---|---|
| 法律文案 | `legal/*.md` |
| 计算器页面 | `site/gen_pages.py` / `site/src/*` |
| 数据 | 跑 `data/collect_*.py` |
| 视觉 | `site/src/styles.css` §1 的 token |
| **不要**直接改 | `site/` 下生成的 HTML、`dist/`（都会被覆盖） |

## 设计系统

「精密仪器 + 编辑排版」气质：暖纸底、深森林绿单强调色、发丝级分隔线、直角、**零柔和投影**、衬线标题。
全部收敛在 `site/src/styles.css` §1 的 token 里（色 / 4pt 间距 / 4 档时长 / expo-out 缓动）；
组件只引用语义别名，不写死具体值。

- **双主题**：完整亮色 + 暗色（`prefers-color-scheme`），`color-scheme` 让原生控件同步适配。
  全部前景/背景配对在两种主题下实测通过 **WCAG AA**。
- **边界光束**：`conic-gradient` + `mask-composite`，`@property` 插值角度；不支持时降级为静态渐变。
- **思考球**：Canvas 2D 扫光环 + 「墨入纸」颜料场；5 种状态在环长 / 断续 / 转速 / 收敛度上结构性区分。
- **克制**：整屏仅约 0.66% 像素带强调色；按钮与卡片只在 hover 时亮。
- **无障碍**：`prefers-reduced-motion: reduce` 下光束与思考球冻结为静态帧，动画全停后设计仍成立。

## 性能

每个计算器页面都曾把整车数据内联进 HTML（占页面 62%，52 页重复）。
现在数据只产出**一份** `assets/fuel-data.js`，被所有页面引用并跨路由缓存；
所有脚本 `defer`，不再阻塞渲染。

| 指标 | 之前 | 现在 |
|---|---|---|
| 首页 HTML | 39.5 KB | 15.4 KB（−61%） |
| 共享数据 | 每页内联 24.6 KB | 独立文件，缓存一次全站复用 |

## 部署

```bash
python site/build.py      # 产出 dist/（只含可公开文件）
wrangler deploy           # 上传 dist/ 到 Cloudflare Workers
```

`wrangler.toml` 中 `[assets] directory = "./dist"`。**必须部署 `dist/` 而非 `site/`**：
`site/` 还包含构建脚本、模板与测试套件，直接部署会把源码树暴露在站点根目录。

`_redirects`（308 别名）与 `_headers`（安全响应头）由 Workers Static Assets 原生消费，不对外暴露为文件。
404 由 `not_found_handling = "404-page"` 提供。

## 目录

```
data/                     数据采集脚本与数据集（唯一事实源，禁止编造）
site/src/                 模板、样式、前端脚本（源）
site/*.py                 构建与渲染管线
site/tests/               引擎一致性 + DOM 冒烟测试
site/                     开发产物（构建生成，不入库）
dist/                     部署产物（构建生成，不入库）
verify.py                 一键验证入口
wrangler.toml, worker.js  Cloudflare Workers 配置
04-compliance/            合规包：数据清单 / 第三方映射 / 风险登记 / 禁词 / 验收清单
legal/                    法律页真源（Markdown，6 份）
project-control.md        项目看板（唯一事实源）
```

## 上线前必做

1. 替换全部 `[OPERATING ENTITY]` / `[CONTACT EMAIL]` / `[JURISDICTION]` 占位符
2. 开通真实可收信的域名邮箱
3. 在 Cloudflare 控制台绑定 Custom Domain，并同步修改 `robots.txt` 中的 canonical 域名
4. 重跑 `python verify.py`，确认全绿
5. 跑 `04-compliance/06-qa-compliance-checklist.md` 的 GATE-01 / GATE-02，Owner Review 后发布

## 已知限制

- DCFC 费率是网络均价**估算**，非官方数据集（页面已标注为 estimate）
- 非美国页面沿用 EPA 能效数据（可验证的公开数据集），页面已明示；本地车型评级可能不同
- 州页首版 10 州，扩展到 51 州改 `gen.py` 的 `STATES_10`
- ZIP → 州按 3 位前缀匹配（一致率 ≥90% 才收录），边界 ZIP 可能落在邻州
- 未做：账号、支付、地图、路线规划、UGC、TCO / 保险 / 维护

---

## 谁先看什么（内部导航）

| 你是谁 | 先看 |
|---|---|
| 项目负责人 | `project-control.md` |
| 法务 / 合规 | `04-compliance/compliance-report.md` §5 + `03-risk-register.md` |
| 文案 | `04-compliance/05-banned-expressions.md` |
| 前端 | `site/src/` + `04-compliance/04-legal-route-contract.md` |
| QA | `04-compliance/06-qa-compliance-checklist.md` + `VERIFICATION.md` |
