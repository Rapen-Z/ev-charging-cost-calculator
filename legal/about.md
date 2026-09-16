---
title: About
route: /about
description: Why this calculator exists, what it does, and how it is put together.
updated: 2026-09-10
---

# About

**Last updated:** 2026-09-10

## What this is

A free calculator that estimates what it costs to run a vehicle — comparing battery-electric, plug-in hybrid, hybrid and petrol/diesel options — using your own mileage and local energy prices instead of a single national average.

It runs entirely in your browser. No signup, no account, no uploads, no payment.

## Why we built it

Most charging-cost tools either cover a single brand, or ask for a ZIP code and then hide the calculation. We wanted the opposite:

- **Show the number immediately** — defaults are pre-filled, so you see an estimate before you type anything.
- **Show the working** — the formula and the inputs are on the page, so you can sanity-check the result.
- **Separate home and public charging** — charging at home and paying for DC fast charging are completely different cost realities, and mixing them hides the truth.
- **Compare across powertrains** — EV vs PHEV vs hybrid vs petrol, on the same assumptions.

## How the calculation works

At its core, the charging-cost estimate is:

```
monthly cost = (monthly miles ÷ efficiency in mi/kWh)
               × price in $/kWh
               × (1 + charging loss %)
```

Home and public charging are weighted separately, because they are priced differently. The fuel comparison adds miles ÷ MPG × fuel price, with adjustments for city/highway split and, for plug-in hybrids, the share of miles that actually run on electricity.

The exact assumptions in force are shown on each page, next to the result.

## Where the data comes from

| Data | Source |
|---|---|
| Vehicle efficiency (mi/kWh, MPGe, MPG) | U.S. EPA / fueleconomy.gov |
| Plug-in hybrid utility factor | U.S. EPA |
| State electricity prices | U.S. Energy Information Administration (EIA) |
| Fuel prices | U.S. Energy Information Administration (EIA) |
| Public DC fast-charging prices | Publicly published network pricing |

Every page shows **when its rates were last updated**. If you spot a figure that looks wrong, please tell us — see [Contact](/contact).

## What this site is not

To keep it fast and honest, we deliberately do **not** do some things:

- No charging-station maps or navigation — there are excellent dedicated tools for that.
- No route or road-trip planning.
- No total-cost-of-ownership modelling — we cover **fuel and charging costs**, not depreciation, insurance, maintenance or finance.
- No accounts, no user-generated content, no AI-written content.
- No signup, no paywall.

## Independence

**[OPERATING ENTITY]** operates this site. We are **not affiliated with, endorsed by, or sponsored by** any vehicle manufacturer or utility company.

Vehicle makes and models are named for identification only. All trademarks are the property of their respective owners, and we do not use manufacturer logos.

## Advertising and affiliate links

**[Not currently enabled]** We may display advertising and use affiliate links in the future. If we do:

- It will be disclosed on the page, above the first affiliate link.
- Advertising will be kept separate from the calculator and will never change your estimate.
- Non-essential advertising cookies will only load after you consent — see the [Cookie Policy](/cookie-policy).

## Not legal, financial or professional advice

Everything on this site is general information for comparison purposes. It is not legal, financial, tax, or professional advice, and it is not a quote. Please read the [Disclaimer](/disclaimer).

## Get in touch

**[support@evchargingcost.online](mailto:support@evchargingcost.online)** — or use the [Contact page](/contact).
