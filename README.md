# EV 充电成本计算器（FuelCost Compass）— 阶段 04-compliance + 站点实现

合规与基础法律页面阶段交付包。执行 Skill：`student-site-compliance-pipeline` v2.3.0。
唯一开发依据：`PRD-ev-charging-cost-calculator-v1`（2026-09-09）。

## 状态

**[NEEDS_REVIEW]** — 合规包 + 完整站点均已落地并通过自动化验证；但 P0-1（运营主体 + 真实域名邮箱）未回填前不得上线。

站点已建好：42 条路由、纯前端计算器、真实 EPA/EIA 数据。`python verify.py` 全绿（构建自检 / 引擎一致性 20488 断言 / DOM T1–T9）。

## 从哪开始

| 你是谁 | 先看 |
|---|---|
| 项目负责人 | `project-control.md`（看板 / 阻塞 / 人工确认项） |
| 法务 / 合规 | `04-compliance/compliance-report.md` §5（法域调研）+ `03-risk-register.md`（P0/P1/P2） |
| 文案 | `04-compliance/05-banned-expressions.md` |
| 设计 | `project-control.md` §「视觉系统」+ `05-banned-expressions.md` A 组（商标）、H 组（深色模式禁用） |
| 前端 | `04-compliance/04-legal-route-contract.md` + `site/src/consent.js` |
| QA | `04-compliance/06-qa-compliance-checklist.md` + `04-compliance/VERIFICATION.md` |
| 下一阶段负责人 | `04-compliance/handoff-summary.md`（含启动 Prompt） |

## 目录

```
project-control.md                  看板（唯一事实源）
data/                               真实数据采集脚本与数据集（唯一事实源，禁止编造）
site/                               可部署 Cloudflare Pages 站点（含计算器引擎与测试）
verify.py                           一键验证：构建 + 自检 + 引擎一致性 + DOM T1–T9
_review/                            视觉验证测试台（不在部署目录内；Puppeteer 截图 + Pillow 像素量测）
04-compliance/
  compliance-report.md              主报告（Preflight / 法域 / 关键决策 / 已知限制）
  01-data-inventory.md              数据清单
  02-third-party-mapping.md         第三方映射 + 六步变更控制
  03-risk-register.md               风险登记 P0×2 / P1×8 / P2×6
  04-legal-route-contract.md        canonical route + 16 条 308 别名
  05-banned-expressions.md          禁词 A–H 组
  06-qa-compliance-checklist.md     37 个验收点
  handoff-summary.md                下游交接摘要
  VERIFICATION.md                   脚本与自检输出（可验证证据）
legal/                              法律页真源（Markdown，6 份）
```

## 构建

```bash
python verify.py                # 构建 + 自检 + 引擎一致性 + DOM T1–T9（推荐）
python site/build.py            # 仅构建 + 自检
python site/build.py --check    # 只自检
```

修改法律文案 → 改 `legal/*.md` → 重跑构建。
修改计算器页面 → 改 `site/gen_pages.py` / `site/src/*` → 重跑构建。
刷新数据 → 跑 `data/collect_*.py` → 重跑构建。
不要直接改 `site/` 下生成的 HTML（会被覆盖）。

## 数据（全部来自官方公开源，无一个数字是编造的）

| 数据 | 来源 | 产物 |
|---|---|---|
| 车型能效（75 款：33 EV / 11 PHEV / 15 HEV / 15 汽油） | EPA / DOE `fueleconomy.gov` web services | `data/vehicles.json` |
| 州住宅电价（51 州，EIA Form 861M 2026-06） | U.S. EIA | `data/energy.json` |
| 汽油零售价（EIA 周度） | U.S. EIA | `data/energy.json` |
| DC 快充费率（网络均价，估算） | 已公开网络定价页，标注为 estimate | `data/regions.json` |
| UK/DE/CA/AU/IN 居民电价与币种 | Ofgem / Verivox / NRCan / AER / IEA | `data/regions.json` |
| ZIP→州映射（912 个前缀，30 个真值校验） | USPS ZIP 数据（Census 派生） | `data/zips.json` |

## 视觉系统

「精密仪器 + 编辑排版」气质：暖纸底（`#fbfaf8`）、深森林绿单强调色（`#124f3e`）、发丝级分隔线、直角、**零柔和投影**、衬线标题。全部收敛在 `site/src/styles.css` §1 的 token 里（色 / 4pt 间距 / 4 档时长 / expo-out 缓动）。

- **边界光束**：`conic-gradient(from var(--beam-a))` 铺在 2px 环上，`mask-composite: exclude` 只留外圈，`@property` 让角度可插值；`@property` 不支持时降级为静态渐变。
- **思考球**：Canvas 2D，conic 扫光环 + `multiply` 颜料场（纸面不发光，用「墨入纸」而非叠加辉光）。5 种状态（idle / working / solving / done / fail）**在环长、环断续、转速、颜料收敛度上结构性区分**，不只是换速度。
- **强度分级**：主计算器常驻低亮；输入框只标记当前焦点（全表单同时最多 1 个亮的）；按钮与卡片只在 hover 时亮。实测整屏仅 **0.66%** 像素带强调色——克制优先。
- **无障碍**：`prefers-reduced-motion: reduce` 下光束与思考球全部冻结为静态帧（保留 0.9 透明度渐变），动画全停后设计仍成立。

## 已实现的功能

- 计算器引擎：**双实现**（`src/calc.js` 前端 + `gen.py` 构建期预渲染），2048 组输入逐字段比对一致
- 公式：`月成本 = 里程 ÷ 能效 × 电价 × (1 + 充电损耗)`，家用/公共双费率加权
- PHEV：EPA utility factor 拆分电/油里程；关闭「家用充电」按纯油重算并给出提示（PRD T7）
- 城市/高速插值、冬季修正（能效 ×0.85）、ZIP→州均价（纯本地、不进 URL）
- 结果 URL 序列化可分享；每页公开计算公式与数据来源
- 页面：首页、Tesla 车系页 + 9 个车型页、4 个对比页、四动力总成旗舰页、PHEV、汽油、10 个州页、5 个国家页、单位换算器
- 构建期禁用表达硬闸（A–F 组），含「闸门活性」对照防止空转
- 动效：主计算器边界光束、输入框焦点光束、按钮/卡片 hover 光束、思考球（ZIP 查表等待 / 命中 / 未命中）、结果更新脉冲

## 已知限制

- **运营主体占位符未替换**（`[OPERATING ENTITY]` / `[CONTACT EMAIL]` / `[JURISDICTION]`）→ 上线前必做
- DCFC $0.47/kWh 是网络均价**估算**，非官方数据集；页面已标注为 estimate
- 非美国页面沿用 EPA 能效数据（可验证的公开数据集），已在页面明示；本地车型评级可能不同
- 州页首版 10 州（PRD §8 指定），扩展到 51 州改 `gen.py` 的 `STATES_10` 一行即可
- ZIP→州按 3 位前缀匹配（≥90% 一致才收录），边界 ZIP 可能落在邻州
- 未做：账号、支付、地图、路线规划、UGC、TCO/保险/维护

## 上线前必做

1. 替换全部 `[OPERATING ENTITY]` / `[CONTACT EMAIL]` / `[JURISDICTION]` 占位符
2. 开通真实可收信的域名邮箱
3. 重跑 `python site/build.py`，确认自检仍通过
4. 跑 `06-qa-compliance-checklist.md` 的 GATE-01 与 GATE-02
5. Owner Review 人工确认后部署
