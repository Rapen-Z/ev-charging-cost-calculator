# 阶段 1 — 数据清单

> 项目：EV 充电成本计算器（FuelCost Compass） | 阶段 04-compliance | 2026-09-10
> 依据：PRD §5/§6/§7/§8/§13。字段级清单为本次新增（PRD §9 仅给了口径，未列字段）。

## 1.1 用户主动输入（User-provided input）

| # | 字段 | 来源 | 存储位置 | 是否离端 | 敏感度 | 备注 |
|---|---|---|---|---|---|---|
| U1 | ZIP code | PRD §7 节点③「ZIP→电价」 | 浏览器内存 + **URL 查询串** | ❌ 不离端（但见下） | 🟡 准标识符 | **P1-1：建议改为州代码** |
| U2 | 电价 override（$/kWh） | PRD §7 节点③ | 浏览器内存 + URL | ❌ | 🟢 低 | |
| U3 | 月里程 | PRD §7 节点③ | 浏览器内存 + URL | ❌ | 🟢 低 | |
| U4 | home / public(DCFC) 充电比例 | PRD §8 MVP-1 | 浏览器内存 + URL | ❌ | 🟢 低 | |
| U5 | 车型选择 | PRD §8「车型库 ~30 款」 | 浏览器内存 + URL | ❌ | 🟢 低 | 可能与 U1 组合推断位置 |
| U6 | PHEV「家充可用」开关 | PRD §13 T7 | 浏览器内存 + URL | ❌ | 🟢 低 | |
| U7 | 油种（regular/premium/diesel） | PRD §13 新增关键因子 | 浏览器内存 + URL | ❌ | 🟢 低 | |
| U8 | 油价 override | PRD §13 | 浏览器内存 + URL | ❌ | 🟢 低 | |
| U9 | 国家/货币/单位偏好 | PRD §8 五国页 | URL path + 可能 localStorage | ❌ | 🟢 低 | |
| U10 | city/highway 行驶比例 | PRD §13 | 浏览器内存 + URL | ❌ | 🟢 低 | |

**判定**：U1–U10 全部为**非特殊类别个人数据**，且单条不识别自然人。但 **U1（ZIP）+ U5（车型）+ U9（国家）** 组合后具备准识别性，且进入 URL → **P1-1**。

## 1.2 客户端持久化（Client-side persistence）

| # | 载体 | 内容 | 目的 | 是否需同意（EEA/UK/DE） |
|---|---|---|---|---|
| C1 | `localStorage` / Cookie `cc_consent` | 同意状态（分类 + 时间戳 + 版本号） | 记录与证明同意（GDPR Art.7(1) 举证责任） | ✅ **豁免**（严格必要） |
| C2 | URL 查询串 | 计算器输入（分享链接，PRD §7 节点④ T6） | 结果可分享/可还原 | ✅ 豁免（但落日志，见 S1） |
| C3 | `localStorage` 记住上次输入 | **尚未实现** | 提升回访体验 | ❌ 需同意（非必要）→ 实现前必须挂同意闸门 |

> C3 当前**不存在**。若下游要实现"记住我的输入"，必须先加同意分类，否则构成 P0。

## 1.3 自动采集（Automatically collected）

| # | 数据 | 采集方 | 法律基础（EEA/UK） | 保留期 |
|---|---|---|---|---|
| S1 | 访问日志：IP、User-Agent、Referer、时间戳、**请求 URL（含查询串）** | Cloudflare（Pages/CDN） | 正当利益（Art.6(1)(f) 安全与服务交付） | **[待确认]**（需查账户 Log Retention） |
| S2 | 聚合流量统计（若启用 Cloudflare Web Analytics，无 Cookie） | Cloudflare | 正当利益 | **[待确认]**；启用后需在 Privacy 增补 |
| S3 | 性能/RUM | 无 | — | — |
| S4 | 崩溃/错误上报 | 无 | — | — |

## 1.4 上传内容

**无。** PRD §6「无后端、无上传」。

## 1.5 AI / 生成式处理

**无。** PRD §5 NOT-DO「不做论坛/UGC/AI 生成内容」。

> 因此本阶段**不产出** AI 内容安全过滤方案、AI 输出版权条款、训练数据条款。若下游引入 AI 生成 FAQ 或文案，必须回到本阶段重开合规（触发 P0）。

## 1.6 支付数据

**无。** PRD §5 NOT-DO + §10「无订阅无付费墙」。无卡数据、无账单地址、无 PCI-DSS 范围、无退款场景。

> 因此 **不产出独立 Refund Policy**（决策 K1）。

## 1.7 账号 / 认证数据

**无。** PRD §5 NOT-DO「不做账号/登录/付费墙」。无邮箱、无密码、无凭据。

## 1.8 Cookie 与类似技术

| # | 名称 | 类别 | 提供方 | 触发条件 | 状态 |
|---|---|---|---|---|---|
| K1 | `cc_consent` | 严格必要 | 本站第一方 | 页面加载 | ✅ 已实现 |
| K2 | `_ga`, `_ga_*` | 分析 | Google Analytics 4 | 同意后 | ⏸ `[待确认]` Finance 未定，**默认关闭** |
| K3 | `_clck`, `_clsk` | 分析/会话录制 | Microsoft Clarity | 同意后 | ⏸ `[待确认]`，**默认关闭**；启用须先做输入脱敏（P1-2） |
| K4 | 广告网络 Cookie | 广告 | 未定 | 同意后 | ⏸ `[待确认]`，**默认关闭** |
| K5 | affiliate 网络 Cookie | 广告/归因 | 未定 | 点击外链后由落地页设置 | ⏸ 未启用；启用须先加 FTC 披露（P1-4） |

## 1.9 分析事件（Analytics events）

| 事件 | 参数 | 状态 |
|---|---|---|
| `page_view` | page_path、referrer | ⏸ 待第三方确认 |
| `calculator_view` | model、state（**不传 ZIP**） | ⏸ |
| `calculator_input_change` | 字段维度（**不传具体值**） | ⏸ |
| `result_share` | 是否复制/分享 | ⏸ |
| `affiliate_outbound_click` | 品类、目标 | ⏸ |

**约束（已写入 `05-banned-expressions.md` 与 QA 表）**：分析事件参数**不得包含** ZIP、完整 URL 查询串、具体电价值。

## 1.10 汇总判定

- **数据敏感度：低**（无特殊类别数据、无儿童定向、无支付、无凭据）
- **与 PRD §9「🟢 低风险」一致** ✅
- **新增披露义务 3 项**（PRD §9 未覆盖）：
  1. URL 查询串进入访问日志（P1-1）
  2. Cloudflare 作为处理者的日志保留期需披露（M5）
  3. "我们不收集任何数据"是**虚假陈述**，禁止写入任何页面（见 `05-banned-expressions.md` B14）
