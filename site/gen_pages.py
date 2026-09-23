#!/usr/bin/env python3
"""Build every calculator page. Called from build.py."""
from __future__ import annotations

import json
from pathlib import Path

import gen
from gen import (STATES_10, esc, money, cat_label, monthly_cost, mi_per_kwh,
                 mpg_of, period_label, rates_strip, sources_block, faq_block,
                 calc_widget, by_slug, render_page, write)

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"


# ------------------------------------------------------------------ pre-render
def prerender_single(v, p, sym="$"):
    r = monthly_cost(v, p)
    mpk = mi_per_kwh(v, p.get("citySharePct"), p.get("winter")) if v["category"] in ("ev", "phev") else 0
    per_mile = r["monthly"] / (p.get("milesPerMonth") or 1)
    out = [f'<p class="result-lead">{money(r["monthly"], sym)}<small> / month</small></p>',
           f'<p class="result-sub">{esc(v["name"])} · {esc(cat_label(v["category"]))} · '
           f'{int(p.get("milesPerMonth", 0)):,} miles/month</p>',
           '<dl class="result-grid">']
    cells = [("Per mile", money(per_mile, sym, 3)), ("Per year", money(r["monthly"] * 12, sym))]
    if mpk > 0:
        cells.append(("Efficiency", f"{mpk:.2f} mi/kWh"))
    if r["kwh"] > 0:
        cells.append(("Energy used", f"{round(r['kwh']):,} kWh/mo"))
    if r["gallons"] > 0:
        cells.append(("Fuel used", f"{r['gallons']:.1f} gal/mo"))
    for dt, dd in cells:
        out.append(f'<div class="result-cell"><dt>{dt}</dt><dd>{dd}</dd></div>')
    out.append("</dl>")
    if v["category"] == "phev" and r["note"]:
        out.append(f'<div class="flag"><strong>Heads up.</strong> {esc(r["note"])}</div>')
    out.append(_formula(p, sym))
    return "".join(out)


def _cost_chart(pairs, sym="$"):
    if not pairs or len(pairs) < 2:
        return ""
    max_m = max((r["monthly"] for _, r in pairs), default=1) or 1
    best = min(pairs, key=lambda x: x[1]["monthly"])
    bars = []
    for v, r in pairs:
        pct = max(12, min(100, round((r["monthly"] / max_m) * 100)))
        is_win = (v is best[0])
        badge = '<span class="cost-bar__badge">Lowest</span>' if is_win else ''
        win_cls = ' is-winner' if is_win else ''
        bars.append(
            f'<div class="cost-bar{win_cls}">'
            f'<div class="cost-bar__header">'
            f'<span class="cost-bar__name">{esc(v["name"])} {badge}</span>'
            f'<span class="cost-bar__val">{money(r["monthly"], sym)}/mo</span>'
            f'</div>'
            f'<div class="cost-bar__track">'
            f'<div class="cost-bar__fill" style="width:{pct}%"></div>'
            f'</div>'
            f'</div>'
        )
    return f'<div class="cost-chart"><div class="cost-chart__title">Monthly Cost Comparison</div>{"".join(bars)}</div>'


def prerender_compare(pairs, p, sym="$"):
    best = min(pairs, key=lambda x: x[1]["monthly"])
    out = [f'<p class="result-lead">{money(best[1]["monthly"], sym)}<small> / month</small></p>',
           f'<p class="result-sub">Cheapest option: {esc(best[0]["name"])}</p>',
           _cost_chart(pairs, sym),
           '<div class="compare"><table><thead><tr><th>Vehicle</th><th>Type</th>'
           '<th>Month</th><th>Year</th><th>Per mile</th></tr></thead><tbody>']
    for v, r in pairs:
        w = ' class="win"' if v is best[0] else ''
        out.append(f'<tr><td>{esc(v["name"])}</td><td>{esc(cat_label(v["category"]))}</td>'
                   f'<td{w}>{money(r["monthly"], sym)}</td><td>{money(r["monthly"] * 12, sym)}</td>'
                   f'<td>{money(r["monthly"] / (p.get("milesPerMonth") or 1), sym, 3)}</td></tr>')
    out.append("</tbody></table></div>")
    if len(pairs) >= 2:
        a, b = pairs[0], pairs[1]
        diff = b[1]["monthly"] - a[1]["monthly"]
        if abs(diff) > 0.5:
            cheap, dear = (a[0], b[0]) if diff > 0 else (b[0], a[0])
            out.append(f'<div class="savings"><strong>{esc(cheap["name"])}</strong> costs about '
                       f'{money(abs(diff), sym)}/month ({money(abs(diff) * 12, sym)}/year) less to run than '
                       f'{esc(dear["name"])} at {int(p.get("milesPerMonth", 0)):,} miles/month.</div>')
    for v, r in pairs:
        if r["note"]:
            out.append(f'<div class="flag"><strong>Heads up.</strong> {esc(r["note"])}</div>')
    out.append(_formula(p, sym))
    return "".join(out)


def _formula(p, sym="$"):
    txt = ("monthly cost = miles ÷ efficiency × price × (1 + charging loss)\n"
           f"  miles            = {int(p.get('milesPerMonth', 0)):,}\n"
           f"  home rate        = {sym}{p.get('homeRateUsdKwh', 0):.4f}/kWh  "
           f"({int(p.get('homeSharePct', 0))}% of charging)\n"
           f"  public DC rate   = {sym}{p.get('publicRateUsdKwh', 0):.4f}/kWh  "
           f"({100 - int(p.get('homeSharePct', 0))}%)\n"
           f"  charging loss    = {int(p.get('chargingLossPct', 0))}%"
           + ("\n  winter correction = ON (efficiency × 0.85)" if p.get("winter") else ""))
    return f'<div class="formula"><strong>How this is worked out</strong><code>{esc(txt)}</code></div>'


def card_grid(items):
    """items: list of (href, name, meta) -> responsive link cards."""
    cells = "".join(
        f'<a href="{esc(h)}" class="beam beam--mono"><span class="c-name">{esc(n)}</span>'
        f'<span class="c-meta">{esc(m)}</span></a>'
        for h, n, m in items)
    return f'<div class="card-grid">{cells}</div>'


def _ld_app_faq(name, route, description, faqs=None):
    cfg = json.loads((gen.SRC / "config.json").read_text(encoding="utf-8"))
    url = cfg["base"] + route
    graph = [
        {
            "@type": "WebApplication",
            "@id": url + "#app",
            "name": name,
            "url": url,
            "applicationCategory": "UtilityApplication",
            "operatingSystem": "Any (web browser)",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "description": description,
        }
    ]
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "@id": url + "#faq",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faqs
            ],
        })
    return {
        "@context": "https://schema.org",
        "@graph": graph,
    }


def _ld_state_page(name, route, description, faqs=None):
    cfg = json.loads((gen.SRC / "config.json").read_text(encoding="utf-8"))
    url = cfg["base"] + route
    graph = [
        {
            "@type": "WebApplication",
            "@id": url + "#app",
            "name": f"{name} EV Charging Cost Calculator",
            "url": url,
            "applicationCategory": "UtilityApplication",
            "operatingSystem": "Any (web browser)",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "description": description,
        },
        {
            "@type": "BreadcrumbList",
            "@id": url + "#breadcrumb",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": cfg["base"] + "/"
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "State Charging Costs",
                    "item": cfg["base"] + "/charging-cost/"
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": name,
                    "item": url
                }
            ]
        },
        {
            "@type": "Dataset",
            "@id": url + "#dataset",
            "name": f"{name} residential electricity price",
            "description": f"EIA Form 861M residential average price for {name}.",
            "url": url,
            "variableMeasured": "Residential electricity price (USD/kWh)",
        }
    ]
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "@id": url + "#faq",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faqs
            ],
        })
    return {
        "@context": "https://schema.org",
        "@graph": graph,
    }


STATE_UTILITIES: dict[str, list[str]] = {
    "AL": ["Alabama Power", "TVA (Tennessee Valley Authority)"],
    "AK": ["Chugach Electric", "Golden Valley Electric (GVEA)", "Alaska Electric Light & Power"],
    "AZ": ["Arizona Public Service (APS)", "Salt River Project (SRP)", "Tucson Electric Power (TEP)"],
    "AR": ["Entergy Arkansas", "Electric Cooperatives of Arkansas", "SWEPCO"],
    "CA": ["Pacific Gas & Electric (PG&E)", "Southern California Edison (SCE)", "San Diego Gas & Electric (SDG&E)", "SMUD"],
    "CO": ["Xcel Energy", "United Power", "CORE Electric Cooperative", "Colorado Springs Utilities"],
    "CT": ["Eversource Energy", "United Illuminating (UI)"],
    "DE": ["Delmarva Power", "Delaware Electric Cooperative"],
    "DC": ["Pepco (Potomac Electric Power Company)"],
    "FL": ["Florida Power & Light (FPL)", "Duke Energy Florida", "Tampa Electric (TECO)", "JEA"],
    "GA": ["Georgia Power", "Cobb EMC", "Jackson EMC", "Sawnee EMC"],
    "HI": ["Hawaiian Electric (HECO/MECO/HELCO)", "Kauai Island Utility Cooperative (KIUC)"],
    "ID": ["Idaho Power", "Avista", "Rocky Mountain Power"],
    "IL": ["Commonwealth Edison (ComEd)", "Ameren Illinois"],
    "IN": ["AES Indiana (IPL)", "Duke Energy Indiana", "NIPSCO", "CenterPoint Energy"],
    "IA": ["MidAmerican Energy", "Alliant Energy (IPL)"],
    "KS": ["Evergy Kansas", "Midwest Energy"],
    "KY": ["LG&E and KU (Louisville Gas & Electric)", "Duke Energy Kentucky", "Kentucky Power"],
    "LA": ["Entergy Louisiana", "Cleco Power", "SWEPCO"],
    "ME": ["Central Maine Power (CMP)", "Versant Power"],
    "MD": ["Baltimore Gas & Electric (BGE)", "Pepco", "Potomac Edison", "Delmarva Power"],
    "MA": ["Eversource", "National Grid", "Unitil"],
    "MI": ["DTE Energy", "Consumers Energy"],
    "MN": ["Xcel Energy", "Minnesota Power", "Otter Tail Power"],
    "MS": ["Mississippi Power", "Entergy Mississippi"],
    "MO": ["Ameren Missouri", "Evergy Missouri"],
    "MT": ["NorthWestern Energy", "Montana-Dakota Utilities"],
    "NE": ["Nebraska Public Power District (NPPD)", "Omaha Public Power District (OPPD)", "Lincoln Electric System (LES)"],
    "NV": ["NV Energy"],
    "NH": ["Eversource New Hampshire", "Liberty Utilities", "Unitil"],
    "NJ": ["Public Service Electric & Gas (PSE&G)", "Jersey Central Power & Light (JCP&L)", "Atlantic City Electric"],
    "NM": ["Public Service Company of New Mexico (PNM)", "El Paso Electric", "Xcel Energy"],
    "NY": ["Consolidated Edison (ConEd)", "National Grid", "PSEG Long Island", "NYSEG", "Rochester Gas & Electric (RG&E)", "Central Hudson"],
    "NC": ["Duke Energy Carolinas", "Duke Energy Progress", "NCEMC Cooperatives"],
    "ND": ["Montana-Dakota Utilities", "Otter Tail Power", "Xcel Energy"],
    "OH": ["AEP Ohio", "Duke Energy Ohio", "FirstEnergy (Ohio Edison, Toledo Edison)", "AES Ohio"],
    "OK": ["Oklahoma Gas & Electric (OG&E)", "Public Service Company of Oklahoma (PSO)"],
    "OR": ["Portland General Electric (PGE)", "Pacific Power", "Eugene Water & Electric Board (EWEB)"],
    "PA": ["PECO Energy", "PPL Electric Utilities", "Duquesne Light", "FirstEnergy (Met-Ed, Penelec, West Penn Power)"],
    "RI": ["Rhode Island Energy"],
    "SC": ["Duke Energy Carolinas", "Duke Energy Progress", "Dominion Energy South Carolina", "Santee Cooper"],
    "SD": ["Black Hills Energy", "NorthWestern Energy", "Otter Tail Power", "Xcel Energy"],
    "TN": ["Nashville Electric Service (NES)", "Memphis Light Gas & Water (MLGW)", "EPB Chattanooga", "Knoxville Utilities Board (KUB)"],
    "TX": ["Oncor Electric Delivery", "CenterPoint Energy", "AEP Texas", "Texas-New Mexico Power (TNMP)"],
    "UT": ["Rocky Mountain Power"],
    "VT": ["Green Mountain Power (GMP)", "Vermont Electric Cooperative"],
    "VA": ["Dominion Energy Virginia", "Appalachian Power (AEP)", "Northern Virginia Electric Cooperative (NOVEC)"],
    "WA": ["Puget Sound Energy (PSE)", "Seattle City Light", "Avista", "Snohomish County PUD", "Tacoma Power"],
    "WV": ["Appalachian Power", "Mon Power"],
    "WI": ["We Energies", "Alliant Energy", "Wisconsin Public Service (WPS)", "Madison Gas & Electric (MGE)"],
    "WY": ["Rocky Mountain Power", "Cheyenne Light Fuel & Power (Black Hills Energy)"],
}

COMPARE_VEHICLE_SLUGS: list[tuple[str, str]] = [
    ("tesla-model-y-long-range-rwd", "EV SUV"),
    ("tesla-model-3-premium-rwd", "EV Sedan"),
    ("ford-f150-lightning-4wd", "EV Pickup"),
    ("ford-escape-phev", "PHEV Compact SUV"),
    ("toyota-camry-hybrid-le", "Hybrid Sedan"),
    ("honda-cr-v-awd", "Gas Compact SUV"),
    ("ford-explorer-awd", "Gas 3-Row SUV"),
]


# ------------------------------------------------------------------------ main
def build(vehicles, energy, regions, out_root):
    gen.DATA_JSON = json.dumps(gen.browser_payload(vehicles, energy, regions),
                               separators=(",", ":"), ensure_ascii=False)
    V = by_slug(vehicles)
    routes = []
    states = energy["states"]
    us_kwh = energy["usAverageUsdPerKwh"]
    us_gas = energy["usAverageGasolineUsdPerGal"]
    dcfc = regions["dcFastCharging"]["usdPerKwh"]
    el_period = period_label(energy["sources"]["electricity"]["period"])

    def base_p(state_code=None, **kw):
        p = {
            "milesPerMonth": 1000, "homeSharePct": 80,
            "homeRateUsdKwh": states[state_code]["usdPerKwh"] if state_code else us_kwh,
            "publicRateUsdKwh": dcfc, "gasUsdPerGal": us_gas,
            "chargingLossPct": 10, "citySharePct": 55,
            "winter": False, "homeCharging": True,
        }
        p.update(kw)
        return p

    def pick(cat, prefer=None):
        for v in vehicles["vehicles"]:
            if v["category"] == cat and (not prefer or v["slug"] == prefer):
                return v
        return None

    def first_of(cats, prefer=None):
        for v in vehicles["vehicles"]:
            if v["category"] in cats and (not prefer or v["slug"] == prefer):
                return v
        return None

    ALL_SHOW = ["zip", "state", "publicRate", "homeShare", "gasPrice", "loss", "city", "winter", "homeCharging"]
    p0 = base_p()

    # ---------------- home ----------------
    ev0 = first_of(["ev"], "tesla-model-y-long-range-rwd")
    gas0 = first_of(["gas"], "toyota-rav4") or first_of(["gas"])
    content = [
        f'<p class="eyebrow">Free · No signup · Runs in your browser</p>',
        '<h1>EV Charging Cost Calculator</h1>',
        '<p class="lede">Work out what an electric car actually costs to charge — by model, by state, '
        'and with home and public fast charging priced separately. Side-by-side against petrol.</p>',
        rates_strip(energy, regions, f'<span><b>Rates updated:</b> {esc(el_period)}</span>'),
        calc_widget({"mode": "compare",
                     "groups": json.dumps([["ev"], ["gas"]]),
                     "vehicle-a": ev0["slug"], "vehicle-b": gas0["slug"],
                     "state": "", "show": ALL_SHOW},
                    prerender_compare([(ev0, monthly_cost(ev0, p0)),
                                       (gas0, monthly_cost(gas0, p0))], p0)),
        '<h2>Why home and public charging are priced separately</h2>',
        '<p>Charging at home and paying for DC fast charging are completely different economics. '
        'Blending them into one number is the single biggest reason online estimates feel wrong. '
        f'The US residential average is about {money(us_kwh, "$", 4)}/kWh, while public DC fast charging '
        f'runs around {money(dcfc)}/kWh — roughly three times as much. Use the "Charging at home" slider '
        'to match how you actually charge.</p>',
        '<h2>Where the numbers come from</h2>',
        '<p>Every efficiency figure is the EPA combined rating published by the U.S. '
        'Environmental Protection Agency on fueleconomy.gov, and every electricity price is the '
        'EIA state residential average. '
        'The formula is shown on the calculator itself so you can check our arithmetic.</p>',
        '<h2>Charging cost by state</h2>',
        '<p>These pages prefill the EIA residential average for that state, so you land on a '
        'number instead of a national guess. Or explore the <a href="/charging-cost/">all 50 states charging cost ranking</a>.</p>',
        card_grid([(f'/charging-cost/{c.lower()}/', states[c]['name'],
                    f"{money(states[c]['usdPerKwh'], '$', 4)}/kWh") for c in STATES_10] + [
            ('/charging-cost/', 'All 50 States Ranked →', 'Compare every US state')
        ]),
        '<h2>Outside the United States</h2>',
        '<p>Local currency, local residential electricity price, same EPA efficiency data. '
        'Every price field stays editable.</p>',
        card_grid([(f"/ev-charging-cost/{c['code']}/", c['name'],
                    f"{c['rateDisplay']}/kWh") for c in regions['countries']]),
        '<h2>Every other calculator on this site</h2>',
        card_grid([
            ('/charging-cost/', '50-State Leaderboard', 'All 50 US states ranked by cost'),
            ('/ev-vs-gas-cost-calculator/', 'EV vs Gas', 'Side-by-side monthly running cost'),
            ('/ev-vs-hybrid-cost-calculator/', 'EV vs Hybrid', 'Battery-electric against a hybrid'),
            ('/hybrid-vs-gas-cost-calculator/', 'Hybrid vs Gas', 'Fuel cost difference per year'),
            ('/phev-vs-hybrid-cost-calculator/', 'PHEV vs Hybrid', 'With and without home charging'),
            ('/ev-vs-phev-vs-hybrid-vs-gas/', 'Compare all four', 'One set of assumptions'),
            ('/phev-charging-cost-calculator/', 'PHEV calculator', 'EPA utility factor built in'),
            ('/gas-cost-calculator/', 'Petrol cost calculator', 'The baseline'),
            ('/tesla-charging-cost-calculator/', 'Tesla charging cost', 'Every current model'),
            ('/unit-converter/mpg-l100km/', 'MPG \u2194 L/100 km', 'Unit converter'),
        ]),
        faq_block([
            ("How accurate is this calculator?",
             "It is an estimate, not a quote. It uses EPA-published efficiency ratings and EIA "
             "prices, so it is a good comparison tool — but your bill depends on your tariff, how much "
             "you charge at home, the weather and how you drive."),
            ("Does it include a home charger or installation cost?",
             "No. This calculator covers running cost only — energy and fuel. Charger hardware and "
             "installation are upfront costs and are deliberately left out."),
            ("Why is public fast charging so much more expensive?",
             f"Fast-charging networks pay for expensive grid connections, hardware and site leases. "
             f"A representative US average is about {money(dcfc)}/kWh, versus roughly "
             f"{money(us_kwh, '$', 4)}/kWh at home."),
            ("Do I need to enter a ZIP code?",
             "No. Pick your state instead — the calculator prefills the EIA state average electricity "
             "price. We deliberately do not put your ZIP into shareable links."),
            ("Can I share my result?",
             "Yes. Every change is written into the page URL, so you can copy the link and anyone "
             "opening it sees exactly the same numbers."),
            ("Does cold weather change the result?",
             "Yes. Tick the winter correction to apply an efficiency penalty (roughly 15% more energy). "
             "Cold batteries and cabin heating both cost range."),
            ("Is this affiliated with Tesla or any carmaker?",
             "No. Vehicle names are used only to identify which car a calculation refers to."),
        ]),
        sources_block(energy, regions, vehicles),
    ]
    write("/", render_page("/", "EV Charging Cost & Rates Calculator (2026) — by Model & State",
                           "Estimate what an EV costs to charge per month, by vehicle model and US state, "
                           "with residential electricity rates, home charging, and DC fast charging.",
                           "".join(content), jsonld=_ld_app_faq(
                               "EV Charging Cost & Rates Calculator", "/",
                               "Estimate EV charging cost and electricity rates by model and state.", [
                                   ("How accurate is this calculator?",
                                    "It is an estimate using EPA-published efficiency and EIA average prices, not a quote."),
                                   ("Does it include charger installation cost?",
                                    "No — it covers running cost only."),
                                   ("Do I need a ZIP code?",
                                    "No. Select your state; the EIA state average is prefilled."),
                               ])), out_root)
    routes.append("/")

    # ---------------- Tesla hub ----------------
    teslas = [v for v in vehicles["vehicles"] if v["make"] == "Tesla"]
    t0 = teslas[0]
    cards = "".join(
        f'<a href="/tesla-charging-cost-calculator/{esc(v["slug"])}/">'
        f'<span class="c-name">{esc(v["name"])}</span>'
        f'<span class="c-meta">{v["miPerKwh"]:.2f} mi/kWh · {v["mpgeCombined"]:.0f} MPGe</span></a>'
        for v in teslas)
    t_faqs = [
        ("How much does it cost to charge a Tesla at home and at a Supercharger?",
         f"A full home charge for a Tesla typically costs between $19 and $30 at the US residential "
         f"average of {money(us_kwh, '$', 4)}/kWh. At a public Tesla Supercharger (averaging ~${dcfc:.2f}/kWh), "
         f"a full charge costs approximately $46 to $72. For 1,000 miles of driving per month, expect around "
         f"$67 to $118 depending on your model."),
        ("Is this run by Tesla?", "No. This is an independent estimator and is not "
         "affiliated with, endorsed by, or sponsored by Tesla, Inc."),
        ("How much does it cost to charge a Model Y at home?",
         f"At the US average of about {money(us_kwh, '$', 4)}/kWh and 1,000 miles a month, the "
         f"{esc(t0['name'])} works out near {money(monthly_cost(t0, p0)['monthly'])}/month. "
         "Change the state to see your price."),
        ("Does this include Supercharger idle fees?", "No. Idle and session fees vary by site and "
         "are not included — only the per-kWh energy price."),
        ("Which Tesla is cheapest to run?", "Generally the smallest battery and most efficient "
         "drivetrain. Use the model list above to compare mi/kWh figures directly."),
        ("Do I need to enter a ZIP code?", "No — pick your state."),
        ("Can I share my result?", "Yes, the URL carries your inputs."),
    ]
    tesla_quick_table = [
        '<h2>How Much Does It Cost to Charge a Tesla? (2026 Averages)</h2>',
        '<p>Quick benchmark across popular Tesla models, based on published EPA ratings, US average residential electricity ($0.1942/kWh), and typical Supercharger pricing ($0.47/kWh):</p>',
        '<div class="table-scroll"><table class="model-cost-table">'
        '<thead><tr><th>Tesla Model</th><th>EPA Range</th><th>Full Home Charge</th><th>Full Supercharger</th><th>Est. Monthly (1,000 mi)</th></tr></thead>'
        '<tbody>'
        '<tr><td><strong>Tesla Model 3</strong> (Premium RWD)</td><td>363 miles</td><td>~$19.11</td><td>~$46.24</td><td><strong>$67.59</strong>/mo</td></tr>'
        '<tr><td><strong>Tesla Model Y</strong> (Long Range RWD)</td><td>357 miles</td><td>~$19.24</td><td>~$46.56</td><td><strong>$69.19</strong>/mo</td></tr>'
        '<tr><td><strong>Tesla Model S</strong> (Dual Motor)</td><td>410 miles</td><td>~$23.76</td><td>~$57.51</td><td><strong>$74.42</strong>/mo</td></tr>'
        '<tr><td><strong>Tesla Model X</strong> (Dual Motor)</td><td>352 miles</td><td>~$24.21</td><td>~$58.60</td><td><strong>$88.33</strong>/mo</td></tr>'
        '<tr><td><strong>Tesla Cybertruck</strong> (Dual Motor AWD)</td><td>325 miles</td><td>~$29.79</td><td>~$72.09</td><td><strong>$117.69</strong>/mo</td></tr>'
        '</tbody></table></div>',
        '<p class="state-stat__sub" style="margin-top:6px;">*Estimates assume full 0–100% battery replenishment with 10% AC charging loss. Monthly cost assumes standard 80% home / 20% Supercharger mix. Use the calculator below to set your exact state rates and mileage.</p>',
    ]
    content = [
        '<p class="eyebrow">Free · No signup · Not affiliated with Tesla, Inc.</p>',
        '<h1>Tesla Charging Cost Calculator</h1>',
        '<p class="lede">What it costs to charge a Tesla, model by model, at your local electricity '
        'price — with home and Supercharger-style public pricing kept separate.</p>',
        '<div class="notice notice--plain"><p><strong>Not a Tesla owner?</strong> Estimate any EV, '
        'plug-in hybrid or petrol car with the <a href="/">general EV charging cost calculator</a> '
        '— it covers every make and model, not just Tesla.</p></div>',
        rates_strip(energy, regions, f'<span><b>Rates updated:</b> {esc(el_period)}</span>'),
        "".join(tesla_quick_table),
        calc_widget({"mode": "single", "groups": json.dumps([["ev"]]), "make": "Tesla",
                     "vehicle-a": t0["slug"], "state": "", "show": ALL_SHOW},
                    prerender_single(t0, p0)),
        '<h2>Every Tesla model</h2>',
        f'<div class="card-grid">{cards}</div>',
        '<h2>How much cheaper is charging at home?</h2>',
        '<p>Typically by a factor of about three. The exact gap depends on where you live: in states '
        'with cheap power the home advantage is enormous, while in high-price states the gap narrows. '
        'Move the "Charging at home" slider to see the crossover for your own mix.</p>',
        faq_block(t_faqs),
        sources_block(energy, regions, vehicles),
    ]
    write("/tesla-charging-cost-calculator/", render_page(
        "/tesla-charging-cost-calculator/", "Tesla Charging Cost Calculator (2026) — Home & Supercharger",
        "Estimate monthly Tesla charging costs across Model 3, Model Y, Model S, Model X, and Cybertruck at home rates and Supercharger pricing.",
        "".join(content), tesla=True,
        jsonld=_ld_app_faq("Tesla Charging Cost Calculator", "/tesla-charging-cost-calculator/",
                           "Estimate monthly charging cost for every Tesla model.", t_faqs)), out_root)
    routes.append("/tesla-charging-cost-calculator/")

    # ---------------- Tesla model pages ----------------
    for v in teslas:
        r = monthly_cost(v, p0)
        mpk = v["miPerKwh"]
        full = v.get("totalRangeMi") or 0
        vm_faqs = [
            (f'How much does it cost to charge a {esc(v["name"])} per month?',
             f'At the US average residential rate and 1,000 miles a month, about '
             f'{money(r["monthly"])}. Your number will differ with your local rate and mileage.'),
            (f'How far will the {esc(v["name"])} go on 1 kWh?',
             f'About {mpk:.2f} miles per kWh on the EPA combined cycle '
             f'({v["kwhPer100MiCombined"]:.1f} kWh per 100 miles).'),
            ("Do these figures come from Tesla?", "No — they are the EPA's published ratings "
             "for this vehicle. This site is not affiliated with Tesla, Inc."),
            ("Does this include charger installation?", "No — running cost only."),
            ("Does winter change it?", "Yes. Tick the winter correction for roughly 15% more energy."),
            ("Can I share this result?", "Yes — the URL carries your inputs."),
        ]
        content = [
            f'<p class="eyebrow">Free · No signup · Not affiliated with Tesla, Inc.</p>',
            f'<h1>{esc(v["name"])} Charging Cost (2026)</h1>',
            f'<p class="lede">The {esc(v["name"])} uses about {mpk:.2f} miles per kWh '
            f'({v["kwhPer100MiCombined"]:.1f} kWh per 100 miles) on the EPA combined cycle'
            + (f', with an EPA-rated range of {full:.0f} miles' if full > 0 else '')
            + '. Here is what that costs per month.</p>',
            '<div class="notice notice--plain"><p><strong>Not driving this Tesla?</strong> Compare any '
            'EV, plug-in hybrid or petrol car with the <a href="/">general EV charging cost calculator</a>.'
            '</p></div>',
            rates_strip(energy, regions, f'<span><b>Rates updated:</b> {esc(el_period)}</span>'),
            calc_widget({"mode": "single", "groups": json.dumps([["ev"]]), "make": "Tesla",
                         "vehicle-a": v["slug"], "state": "", "show": ALL_SHOW},
                        prerender_single(v, p0)),
            f'<h2>{esc(v["name"])} running cost at a glance</h2>',
            '<div class="result-grid">',
            f'<div class="result-cell"><dt>Efficiency</dt><dd>{mpk:.2f} mi/kWh</dd></div>',
            f'<div class="result-cell"><dt>Energy per 100 mi</dt><dd>{v["kwhPer100MiCombined"]:.1f} kWh</dd></div>',
            f'<div class="result-cell"><dt>MPGe</dt><dd>{v["mpgeCombined"]:.0f}</dd></div>',
            (f'<div class="result-cell"><dt>EPA range</dt><dd>{full:.0f} mi</dd></div>' if full > 0 else ""),
            f'<div class="result-cell"><dt>Cost per mile (US avg)</dt><dd>{money(r["monthly"] / 1000, "$", 3)}</dd></div>',
            f'<div class="result-cell"><dt>Cost per year (US avg)</dt><dd>{money(r["monthly"] * 12)}</dd></div>',
            '</div>',
            f'<h2>Charging the {esc(v["name"])} at home vs on the road</h2>',
            '<p>Home charging is billed at your utility rate; DC fast charging is billed at the '
            'network rate and is usually around three times higher. The slider in the calculator above '
            'lets you set the split.</p>',
            faq_block(vm_faqs),
            '<h2>Other Tesla models</h2>',
            card_grid([(f'/tesla-charging-cost-calculator/{o["slug"]}/', o['name'],
                        f"{o['miPerKwh']:.2f} mi/kWh")
                       for o in teslas if o['slug'] != v['slug']]),
            '<h2>Compare it with something else</h2>',
            card_grid([
                ('/tesla-charging-cost-calculator/', 'All Tesla models', 'Back to the model hub'),
                ('/ev-vs-gas-cost-calculator/', 'EV vs Gas',
                 f'How the {v["name"]} compares on fuel cost'),
                ('/charging-cost/', 'State cost leaderboard', 'All 50 states ranked'),
            ]),
            sources_block(energy, regions, vehicles),
        ]
        route = f'/tesla-charging-cost-calculator/{v["slug"]}/'
        write(route, render_page(route, f'{v["name"]} Charging Cost Calculator (2026)',
                                 f'Estimate the monthly charging cost of a {v["name"]} at your local '
                                 f'electricity price. EPA {mpk:.2f} mi/kWh.',
                                 "".join(content), tesla=True,
                                 jsonld=_ld_app_faq(f'{v["name"]} Charging Cost Calculator', route,
                                                    f'Estimate monthly charging cost of a {v["name"]}.', vm_faqs)), out_root)
        routes.append(route)

    # ---------------- comparison pages ----------------
    COMPARISONS = [
        ("/ev-vs-gas-cost-calculator/", "EV vs Gas Cost Calculator",
         "Compare the monthly running cost of an electric car and a petrol car side by side.",
         "Which is actually cheaper to run? Put an EV and a petrol car on the same mileage and the "
         "same local prices and see the difference per month and per year.",
         ["ev"], ["gas"], ALL_SHOW, [
             ("Is an EV always cheaper to run?", "Almost always on home charging, and it depends on "
              "your local electricity price versus petrol. Public fast charging narrows the gap a lot."),
             ("What is included in the comparison?", "Energy and fuel cost only. Purchase price, "
              "insurance, maintenance, depreciation and tax are deliberately excluded."),
             ("Why does my state matter so much?", "Because residential electricity ranges from about "
              "13c to over 50c per kWh across the US, which swings the answer more than any other input."),
             ("How do you handle city versus highway driving?", "Use the city driving slider — the "
              "calculator interpolates between the EPA city and highway ratings."),
             ("Can I share my comparison?", "Yes, the URL carries every input."),
             ("Is this a quote?", "No. It is an estimate from published average data."),
         ]),
        ("/ev-vs-hybrid-cost-calculator/", "EV vs Hybrid Cost Calculator",
         "Compare the monthly running cost of a battery-electric car and a hybrid.",
         "A hybrid never needs plugging in; an EV is cheaper per mile if you can charge at home. "
         "Put both on your mileage and prices and see which wins where you live.",
         ["ev"], ["hev"], ALL_SHOW, [
             ("Which is cheaper to run?", "Usually the EV, if you charge at home. A hybrid closes the "
              "gap if you rely on public fast charging."),
             ("Does this include purchase price?", "No — running cost only."),
             ("Do hybrids need charging?", "Conventional hybrids do not plug in; this calculator "
              "treats them as petrol-powered."),
             ("Can I share this?", "Yes, via the page URL."),
             ("Is this a quote?", "No, an estimate."),
             ("Does weather change it?", "Yes — use the winter correction for a colder-climate figure."),
         ]),
        ("/hybrid-vs-gas-cost-calculator/", "Hybrid vs Gas Cost Calculator",
         "Compare the monthly fuel cost of a hybrid and a conventional petrol car.",
         "How long does the hybrid premium take to pay back in fuel? Start with the monthly and yearly "
         "difference at your mileage and local petrol price.",
         ["hev"], ["gas"], ["gasPrice", "city", "winter"], [
             ("How much does a hybrid save on fuel?", "It depends on your mileage and petrol price. "
              "Set both above and read the yearly difference."),
             ("Does this include the higher purchase price?", "No — fuel cost only."),
             ("Why is my real MPG different from the sticker?", "Driving style, terrain, temperature "
              "and trip length all move it. Use the city driving slider to match your mix."),
             ("Can I share this?", "Yes, via the URL."),
             ("Is this a quote?", "No, an estimate."),
             ("Do hybrids cost more to maintain?", "Maintenance is outside this calculator's scope."),
         ]),
        ("/phev-vs-hybrid-cost-calculator/", "PHEV vs Hybrid Cost Calculator",
         "Compare a plug-in hybrid and a conventional hybrid — with and without home charging.",
         "A plug-in hybrid only beats a conventional hybrid if you actually plug it in. Turn the home "
         "charging switch off and watch the answer flip.",
         ["phev"], ["hev"], ["zip", "state", "publicRate", "homeShare", "gasPrice", "loss", "city", "winter", "homeCharging"], [
             ("Why does home charging matter so much?", "Because a plug-in hybrid that never plugs in "
              "is just a heavier hybrid — it carries a battery it never uses."),
             ("What is the utility factor?", "The EPA's estimate of the share of miles a plug-in hybrid "
              "drives on electricity. It is shown for each model and drives the split here."),
             ("What happens if I turn home charging off?", "The plug-in hybrid is recosted on petrol at "
              "its charge-sustaining economy — effectively as a conventional hybrid."),
             ("Does this include purchase price?", "No — running cost only."),
             ("Can I share this?", "Yes, via the URL."),
             ("Is this a quote?", "No, an estimate."),
         ]),
    ]
    for route, title, desc, lede, ca, cb, show, faqs in COMPARISONS:
        va = first_of(ca)
        vb = first_of(cb)
        title_h1 = title
        extra_content = []
        if route == "/hybrid-vs-gas-cost-calculator/":
            title = "Hybrid vs Gas Savings Calculator (2026) — Hybrid Car Fuel Savings"
            title_h1 = "Hybrid vs Gas (Petrol) Fuel Savings Calculator"
            desc = "Calculate hybrid car fuel savings vs gas and petrol cars. Compare monthly and annual fuel savings for popular hybrids across the US, Canada (CAD), and UK."
            lede = "Calculate how much money you save driving a hybrid car versus a conventional petrol or gas vehicle. Compare monthly and yearly fuel savings based on your driving distance and local fuel prices."
            extra_content = [
                '<h2>How Much Does a Hybrid Car Save on Fuel?</h2>',
                '<p>On average, driving a hybrid saves between <strong>$350 and $600 per year</strong> in fuel costs compared to an equivalent gasoline car over 12,000 miles (at typical fuel prices of $3.68/gallon). Because hybrid powertrains capture energy through regenerative braking and use an electric motor during stop-and-go driving, fuel savings are largest in urban city traffic.</p>',
                '<div class="table-scroll"><table class="model-cost-table">'
                '<thead><tr><th>Comparison (Hybrid vs Gas)</th><th>Hybrid Rating</th><th>Gas Rating</th><th>Est. Annual Savings</th><th>Payback Context</th></tr></thead>'
                '<tbody>'
                '<tr><td><strong>Sedan:</strong> Toyota Camry Hybrid vs Corolla Gas</td><td>51 MPG combined</td><td>35 MPG combined</td><td><strong style="color:var(--accent-ink)">+$408 / year</strong></td><td>Recovers hybrid premium in ~4–5 years</td></tr>'
                '<tr><td><strong>Compact SUV:</strong> Toyota RAV4 Hybrid vs RAV4 Gas</td><td>39 MPG combined</td><td>29 MPG combined</td><td><strong style="color:var(--accent-ink)">+$372 / year</strong></td><td>Popular family commuter benchmark</td></tr>'
                '<tr><td><strong>Hatchback:</strong> Toyota Prius vs Standard Gas Car</td><td>57 MPG combined</td><td>32 MPG combined</td><td><strong style="color:var(--accent-ink)">+$576 / year</strong></td><td>Highest annual fuel savings in class</td></tr>'
                '</tbody></table></div>',
                '<h2>Calculating Hybrid Savings in Canada & the UK</h2>',
                '<p>For drivers outside the United States, fuel savings translate directly into local metric units:</p>',
                '<ul>'
                '<li><strong>In Canada (CAD &amp; L/100 km):</strong> A 51 MPG hybrid uses approximately 4.6 L/100 km, while a 35 MPG gas car consumes about 6.7 L/100 km. At an average Canadian retail fuel price of $1.60 CAD per litre, driving 20,000 km per year delivers approximately <strong>$670 CAD in annual fuel savings</strong>. You can convert between US MPG and L/100 km using our <a href="/unit-converter/mpg-l100km/">MPG to L/100 km converter</a>, or view provincial energy rates on our <a href="/ev-charging-cost/ca/">Canada EV cost page</a>.</li>'
                '<li><strong>In the United Kingdom &amp; Commonwealth (Petrol):</strong> British imperial gallons are roughly 20% larger than US gallons. Because conventional self-charging hybrids do not plug into the mains, they run purely on standard unleaded petrol — meaning no home wallbox installation or charging infrastructure is required.</li>'
                '</ul>'
            ]
            faqs = [
                ("How much does a hybrid car save on fuel per year?",
                 "Based on 12,000 miles per year at US average fuel prices, a hybrid car typically saves "
                 "between $350 and $600 per year compared to a similar petrol car. High-mileage and city drivers save even more."),
                ("How do I calculate hybrid fuel savings in Canada?",
                 "Canadian drivers can convert fuel economy to L/100 km: a 50 MPG hybrid consumes roughly 4.7 L/100 km "
                 "versus 7.0 L/100 km for a standard gas vehicle. At $1.60 CAD per litre, this saves roughly $35 to $60 CAD per month."),
                ("Is a hybrid car worth the extra purchase price?",
                 "From a fuel-savings perspective, the typical hybrid price premium ($1,500 to $2,500) pays for itself in "
                 "roughly 3 to 5 years under average driving conditions, after which all fuel savings represent pure cost reduction."),
                ("Does this calculator compare hybrid vs petrol for UK drivers?",
                 "Yes. Conventional hybrids run on standard petrol. Set your local petrol price and annual mileage in the calculator above "
                 "to see your exact monthly and yearly fuel difference."),
                ("Why do hybrids save more fuel in city driving than on highways?",
                 "In stop-and-go city driving, hybrids constantly recapture kinetic energy via regenerative braking that would "
                 "otherwise be lost as friction heat, and the electric motor powers low-speed acceleration without burning petrol."),
                ("Do conventional hybrids need to be plugged in?",
                 "No. Standard hybrids recharge their high-voltage battery internally using engine power and regenerative braking. "
                 "If you want to plug in and charge from home electricity, see our PHEV calculator."),
            ]
        content = [
            f'<p class="eyebrow">Free · No signup · Runs in your browser</p>',
            f'<h1>{esc(title_h1)}</h1>',
            f'<p class="lede">{esc(lede)}</p>',
            rates_strip(energy, regions, f'<span><b>Rates updated:</b> {esc(el_period)}</span>'),
            calc_widget({"mode": "compare", "groups": json.dumps([ca, cb]),
                         "vehicle-a": va["slug"], "vehicle-b": vb["slug"],
                         "state": "", "show": show},
                        prerender_compare([(va, monthly_cost(va, p0)),
                                           (vb, monthly_cost(vb, p0))], p0)),
            '<h2>What is included — and what is not</h2>',
            '<p>This is a running-cost comparison: energy and fuel only. Purchase price, finance, '
            'insurance, maintenance, depreciation, tax and incentives are all excluded, because mixing '
            'them into a monthly fuel figure is how comparisons end up misleading.</p>',
            "".join(extra_content),
            faq_block(faqs),
            '<h2>Other comparisons</h2>',
            card_grid([(r2, t2, d2) for r2, t2, d2, *_ in COMPARISONS if r2 != route][:4]),
            sources_block(energy, regions, vehicles),
        ]
        write(route, render_page(route, title, desc, "".join(content),
                                 jsonld=_ld_app_faq(title, route, desc, faqs)), out_root)
        routes.append(route)

    # ---------------- PHEV calculator (T7) ----------------
    pv = first_of(["phev"])
    phev_faqs = [
        ("What is the EPA utility factor?", "The EPA's estimate of the proportion of miles a "
         "plug-in hybrid will drive on electricity, based on real-world driving and charging data."),
        ("Is a PHEV worth it without home charging?", "Rarely on fuel cost alone. Switch the home "
         "charging control off to see the difference for the model you are considering."),
        ("Does this include the petrol part?", "Yes — petrol miles are costed at the model's "
         "charge-sustaining MPG at the fuel price you set."),
        ("Do you include installation of a home charger?", "No — running cost only."),
        ("Can I share my result?", "Yes, via the URL."),
        ("Is this a quote?", "No, an estimate."),
    ]
    content = [
        '<p class="eyebrow">Free · No signup · Runs in your browser</p>',
        '<h1>PHEV Charging Cost Calculator</h1>',
        '<p class="lede">A plug-in hybrid splits its miles between electricity and petrol. This '
        'calculator uses the EPA-published utility factor for your model — and lets you switch home '
        'charging off to see what happens if you never plug in.</p>',
        rates_strip(energy, regions, f'<span><b>Rates updated:</b> {esc(el_period)}</span>'),
        calc_widget({"mode": "single", "groups": json.dumps([["phev"]]),
                     "vehicle-a": pv["slug"], "state": "",
                     "show": ["zip", "state", "publicRate", "homeShare", "gasPrice", "loss", "city", "winter", "homeCharging"]},
                    prerender_single(pv, p0)),
        '<h2>The home charging switch is the whole question</h2>',
        '<p>Plug-in hybrids are scored by the EPA with a <strong>utility factor</strong>: the share of '
        'miles the car is expected to drive on electricity. With a charger at home, that share is real. '
        'Without one, the car runs almost entirely on petrol — and because it carries a battery it is '
        'usually no more efficient than a conventional hybrid.</p>',
        '<p>Turn off <em>Home charging available</em> above and the result is recosted on petrol alone. '
        'That is the honest answer to "should I buy a PHEV if I cannot charge at home?".</p>',
        faq_block(phev_faqs),
        sources_block(energy, regions, vehicles),
    ]
    write("/phev-charging-cost-calculator/", render_page(
        "/phev-charging-cost-calculator/", "PHEV Charging Cost Calculator (2026)",
        "Estimate the monthly running cost of a plug-in hybrid using the EPA-published utility factor, "
        "with and without home charging.", "".join(content),
        jsonld=_ld_app_faq("PHEV Charging Cost Calculator", "/phev-charging-cost-calculator/",
                           "Estimate monthly running costs of a plug-in hybrid vehicle.", phev_faqs)), out_root)
    routes.append("/phev-charging-cost-calculator/")

    # ---------------- gas calculator ----------------
    gv = first_of(["gas"])
    gas_faqs = [
        ("How do you calculate fuel cost?", "Miles divided by MPG, times the fuel price. The MPG "
         "is interpolated between the EPA city and highway ratings using your city driving share."),
        ("Which fuel price do you use?", "The latest EIA weekly US average is prefilled; override "
         "it with your own local price."),
        ("Does this include tax or registration?", "No — fuel cost only."),
        ("Can I share my result?", "Yes, via the URL."),
        ("Is this a quote?", "No, an estimate."),
        ("Do you cover diesel?", "Not currently — the vehicle set here is petrol and hybrid only."),
    ]
    content = [
        '<p class="eyebrow">Free · No signup · Runs in your browser</p>',
        '<h1>Petrol Cost Calculator</h1>',
        '<p class="lede">What your petrol car costs per month and per year at your mileage, your city '
        'mix and your local fuel price — the baseline every EV comparison on this site is measured '
        'against.</p>',
        rates_strip(energy, regions, f'<span><b>Rates updated:</b> {esc(el_period)}</span>'),
        calc_widget({"mode": "single", "groups": json.dumps([["gas"]]),
                     "vehicle-a": gv["slug"], "state": "",
                     "show": ["gasPrice", "city", "winter"]},
                    prerender_single(gv, p0)),
        '<h2>Why your real MPG differs from the sticker</h2>',
        '<p>EPA ratings are measured on a fixed cycle. Real economy moves with speed, terrain, load, '
        'tyres, temperature and trip length — short trips from cold are especially expensive. Use the '
        'city driving slider to match your own mix, and the winter switch for a cold-climate figure.</p>',
        faq_block(gas_faqs),
        sources_block(energy, regions, vehicles),
    ]
    write("/gas-cost-calculator/", render_page(
        "/gas-cost-calculator/", "Petrol Cost Calculator (2026)",
        "Estimate the monthly and annual fuel cost of a petrol car at your mileage and local fuel price.",
        "".join(content),
        jsonld=_ld_app_faq("Petrol Cost Calculator", "/gas-cost-calculator/",
                           "Estimate petrol car running costs by monthly mileage and fuel price.", gas_faqs)), out_root)
    routes.append("/gas-cost-calculator/")

    # ---------------- four-way flagship ----------------
    four = [first_of(["ev"]), first_of(["phev"]), first_of(["hev"]), first_of(["gas"])]
    four_faqs = [
        ("Which drivetrain is cheapest to run?", "Usually a battery-electric car charged at home. "
         "The ranking can change if you rely on public fast charging or drive mostly on the highway."),
        ("What is a utility factor?", "For plug-in hybrids, the EPA's estimate of the share of "
         "miles driven on electricity."),
        ("Why is my plug-in hybrid so expensive here?", "Check the home charging switch — without "
         "home charging a PHEV runs mostly on petrol."),
        ("Do you include the purchase price?", "No — running cost only."),
        ("Can I share this?", "Yes, via the URL."),
        ("Is this a quote?", "No, an estimate."),
        ("Does winter change the ranking?", "It compresses it — cold weather hurts electric range "
         "more than petrol economy. Use the winter switch to see."),
    ]
    content = [
        '<p class="eyebrow">Free · No signup · Runs in your browser</p>',
        '<h1>EV vs PHEV vs Hybrid vs Petrol — Running Cost Comparison</h1>',
        '<p class="lede">Four drivetrains, one set of assumptions. Pick one of each and see what they '
        'cost per month, per year and per mile at your mileage and your local prices.</p>',
        rates_strip(energy, regions, f'<span><b>Rates updated:</b> {esc(el_period)}</span>'),
        calc_widget({"mode": "four", "groups": json.dumps([["ev"], ["phev"], ["hev"], ["gas"]]),
                     "vehicle-a": four[0]["slug"], "vehicle-b": four[1]["slug"],
                     "vehicle-c": four[2]["slug"], "vehicle-d": four[3]["slug"],
                     "state": "", "show": ALL_SHOW},
                    prerender_compare([(v, monthly_cost(v, p0)) for v in four], p0)),
        '<h2>How to read this</h2>',
        '<p>All four are costed on the same mileage, the same electricity price, the same fuel price and '
        'the same city/highway mix. That is the point — it removes the usual apples-to-oranges problem '
        'where each car is quoted on different assumptions.</p>',
        '<p>It is still a <strong>running-cost</strong> comparison. It does not include purchase price, '
        'finance, insurance, maintenance, depreciation, tax or incentives, and it is not a '
        'whole-life ownership cost figure.</p>',
        faq_block(four_faqs),
        sources_block(energy, regions, vehicles),
    ]
    write("/ev-vs-phev-vs-hybrid-vs-gas/", render_page(
        "/ev-vs-phev-vs-hybrid-vs-gas/",
        "EV vs PHEV vs Hybrid vs Petrol — Running Cost Comparison (2026)",
        "Compare the monthly running cost of battery-electric, plug-in hybrid, hybrid and petrol cars "
        "on identical assumptions.", "".join(content),
        jsonld=_ld_app_faq("EV vs PHEV vs Hybrid vs Petrol Comparison", "/ev-vs-phev-vs-hybrid-vs-gas/",
                           "Compare monthly costs across EV, PHEV, hybrid and petrol cars.", four_faqs)), out_root)
    routes.append("/ev-vs-phev-vs-hybrid-vs-gas/")

    # ---------------- unit converter ----------------
    content = [
        '<p class="eyebrow">Free tool</p>',
        '<h1>MPG ↔ L/100 km Converter</h1>',
        '<p class="lede">Convert between US miles per gallon and litres per 100 kilometres in both '
        'directions. Useful because fuel economy is quoted in opposite directions on either side of the '
        'Atlantic — bigger is better in MPG, smaller is better in L/100 km.</p>',
        '<div class="converter beam" id="converter">',
        '<div class="field--row">',
        '<div class="field"><label for="c-mpg">US MPG</label>'
        '<input type="number" id="c-mpg" step="0.01" min="0" value="30"></div>',
        '<div class="field"><label for="c-l100">L / 100 km</label>'
        '<input type="number" id="c-l100" step="0.01" min="0"></div>',
        '</div>',
        '<p class="field__hint">Type in either box. The conversion constant is 235.214583 '
        '(100 km ÷ 1.609344 km/mi × 3.785411784 L/gal).</p>',
        '</div>',
        '<h2>Common conversions</h2>',
        '<div class="table-scroll"><table><thead><tr><th>US MPG</th><th>L/100 km</th>'
        '<th>US MPG</th><th>L/100 km</th></tr></thead><tbody>',
    ]
    for m in [20, 25, 30, 35, 40, 45, 50, 55, 60]:
        content.append(f'<tr><td>{m}</td><td>{235.214583 / m:.2f}</td>'
                       f'<td>{m + 5}</td><td>{235.214583 / (m + 5):.2f}</td></tr>')
    conv_faqs = [
        ("Which MPG does this use?", "US miles per gallon. Imperial (UK) gallons are about "
         "20% larger, so UK MPG figures are not directly comparable."),
        ("Why is L/100 km better for comparing cars?", "Because it is proportional to fuel "
         "consumed. Differences in L/100 km map linearly to fuel bought, whereas MPG does not."),
        ("How do I convert electric efficiency?", "Electric cars are usually quoted in "
         "kWh per 100 miles or miles per kWh. The calculators on this site handle that directly."),
        ("Is the conversion exact?", "Yes — it is a fixed constant, not an estimate."),
        ("Can I use this for diesel?", "Yes, the unit conversion is fuel-agnostic."),
        ("Do you convert cost as well?", "Not here — use the calculators, which price fuel "
         "and electricity directly."),
    ]
    content += ['</tbody></table></div>',
                faq_block(conv_faqs),
                sources_block(energy, regions, vehicles)]
    write("/unit-converter/mpg-l100km/", render_page(
        "/unit-converter/mpg-l100km/", "MPG to L/100 km Converter",
        "Convert US MPG to litres per 100 km and back, with a reference table.",
        "".join(content),
        jsonld=_ld_app_faq("MPG to L/100 km Converter", "/unit-converter/mpg-l100km/",
                           "Convert US MPG to litres per 100 km and back.", conv_faqs)), out_root)
    routes.append("/unit-converter/mpg-l100km/")

    # ---------------- 50-state leaderboard hub ----------------
    ev_ref = first_of(["ev"], "tesla-model-y-long-range-rwd")
    gas_ref = first_of(["gas"], "toyota-rav4") or first_of(["gas"])

    sorted_states = sorted(states.items(), key=lambda item: item[1]["usdPerKwh"])
    cheapest_code, cheapest_st = sorted_states[0]
    priciest_code, priciest_st = sorted_states[-1]

    cheapest_ev_m = monthly_cost(ev_ref, base_p(cheapest_code))["monthly"]
    priciest_ev_m = monthly_cost(ev_ref, base_p(priciest_code))["monthly"]
    us_ev_m = monthly_cost(ev_ref, p0)["monthly"]
    us_gas_m = monthly_cost(gas_ref, p0)["monthly"]
    us_annual_save = (us_gas_m - us_ev_m) * 12

    summary_cards = (
        '<div class="leaderboard-summary">'
        '<div class="leaderboard-stat is-highlight">'
        '<div class="leaderboard-stat__label">Lowest Electricity Rate</div>'
        f'<div class="leaderboard-stat__value">{esc(cheapest_st["name"])}</div>'
        f'<div class="leaderboard-stat__sub">{money(cheapest_st["usdPerKwh"], "$", 4)}/kWh · ~{money(cheapest_ev_m)}/mo</div>'
        '</div>'
        '<div class="leaderboard-stat">'
        '<div class="leaderboard-stat__label">US National Average</div>'
        f'<div class="leaderboard-stat__value">{money(us_kwh, "$", 4)}</div>'
        f'<div class="leaderboard-stat__sub">~{money(us_ev_m)}/mo ({esc(ev_ref["name"])})</div>'
        '</div>'
        '<div class="leaderboard-stat">'
        '<div class="leaderboard-stat__label">Highest Electricity Rate</div>'
        f'<div class="leaderboard-stat__value">{esc(priciest_st["name"])}</div>'
        f'<div class="leaderboard-stat__sub">{money(priciest_st["usdPerKwh"], "$", 4)}/kWh · ~{money(priciest_ev_m)}/mo</div>'
        '</div>'
        '<div class="leaderboard-stat is-highlight">'
        '<div class="leaderboard-stat__label">Average Annual EV Savings</div>'
        f'<div class="leaderboard-stat__value">+{money(us_annual_save)}/yr</div>'
        f'<div class="leaderboard-stat__sub">vs {esc(gas_ref["name"])} at {money(us_gas)}/gal</div>'
        '</div>'
        '</div>'
    )

    tbl_rows = []
    for rank, (code, st) in enumerate(sorted_states, 1):
        p_st = base_p(code)
        r_ev_st = monthly_cost(ev_ref, p_st)
        r_gas_st = monthly_cost(gas_ref, p_st)
        save_yr = (r_gas_st["monthly"] - r_ev_st["monthly"]) * 12
        rank_badge = f'<span class="rank-badge{" top-3" if rank <= 3 else ""}">{rank}</span>'
        tbl_rows.append(
            f'<tr>'
            f'<td>{rank_badge}</td>'
            f'<td><a href="/charging-cost/{code.lower()}/"><strong>{esc(st["name"])}</strong> ({code})</a></td>'
            f'<td><code>{money(st["usdPerKwh"], "$", 4)}</code></td>'
            f'<td>{money(r_ev_st["monthly"])}/mo</td>'
            f'<td>{money(r_gas_st["monthly"])}/mo</td>'
            f'<td class="win">+{money(save_yr)}/yr</td>'
            f'</tr>'
        )

    hub_faqs = [
        ("Which US state is the cheapest for EV charging?",
         f"According to the latest EIA data, {cheapest_st['name']} has the lowest residential electricity rate at "
         f"{money(cheapest_st['usdPerKwh'], '$', 4)} per kWh. Driving 1,000 miles a month in a {ev_ref['name']} "
         f"costs only about {money(cheapest_ev_m)} per month."),
        ("Which US state has the most expensive electricity?",
         f"{priciest_st['name']} has the highest residential rate at {money(priciest_st['usdPerKwh'], '$', 4)} per kWh. "
         f"Even in high-cost states, off-peak time-of-use (TOU) tariffs can significantly reduce home charging expenses."),
        ("How much does the average American save by driving an EV?",
         f"At the US national average of {money(us_kwh, '$', 4)}/kWh for electricity and {money(us_gas)}/gal for petrol, "
         f"an EV saves approximately {money(us_annual_save)} per year in fuel over 12,000 miles compared to a 30 MPG petrol car."),
        ("Where does this electricity pricing data come from?",
         "All electricity rates are sourced from the U.S. Energy Information Administration (EIA) Form 861M "
         "monthly electric utility sales reports."),
    ]

    hub_content = [
        '<p class="eyebrow">Data & Rankings · 2026 Analysis</p>',
        '<h1>EV Charging Cost & Electricity Rates by State: All 50 States Ranked (2026)</h1>',
        f'<p class="lede">Residential electricity prices vary dramatically across America — from '
        f'<strong>{money(cheapest_st["usdPerKwh"], "$", 4)}/kWh in {esc(cheapest_st["name"])}</strong> to '
        f'<strong>{money(priciest_st["usdPerKwh"], "$", 4)}/kWh in {esc(priciest_st["name"])}</strong>. '
        f'Here is the complete ranking of all 50 states and DC, showing what 1,000 miles per month costs in '
        f'a {esc(ev_ref["name"])} compared to petrol.</p>',
        rates_strip(energy, regions, f'<span><b>Rates updated:</b> {esc(el_period)}</span>'),
        summary_cards,
        '<h2>State-by-state electricity rates & charging cost comparison</h2>',
        '<p>Ranked from lowest residential electricity rate to highest. Click any state to open its dedicated calculator '
        'prefilled with that state\'s exact EIA rate and compare any electric or hybrid vehicle.</p>',
        '<div class="table-scroll"><table class="table-state-rank">'
        '<thead><tr><th>#</th><th>State</th><th>Electricity Rate</th><th>Monthly EV Cost</th><th>Monthly Petrol Cost</th><th>Annual Savings</th></tr></thead>'
        f'<tbody>{"".join(tbl_rows)}</tbody></table></div>',
        faq_block(hub_faqs),
        '<h2>Popular calculators</h2>',
        card_grid([
            ('/ev-vs-gas-cost-calculator/', 'EV vs Gas Calculator', 'Head-to-head comparison'),
            ('/tesla-charging-cost-calculator/', 'Tesla Charging Cost', 'Every current Tesla model'),
            ('/ev-vs-phev-vs-hybrid-vs-gas/', 'Compare All Four', 'EV, PHEV, Hybrid and Petrol'),
            ('/phev-charging-cost-calculator/', 'PHEV Calculator', 'Utility factor calculator'),
        ]),
        sources_block(energy, regions, vehicles),
    ]

    hub_route = "/charging-cost/"
    write(hub_route, render_page(
        hub_route, "EV Charging Cost & Electricity Rates by State (2026) — All 50 States Ranked",
        "Ranked leaderboard of all 50 US states and DC by residential electricity rates, monthly EV charging costs, and annual petrol fuel savings.",
        "".join(hub_content),
        jsonld=_ld_app_faq("EV Charging Cost & Electricity Rates by State — All 50 States Ranked", hub_route,
                           "Compare EV charging costs and residential electricity rates across all 50 US states.",
                           hub_faqs)), out_root)
    routes.append(hub_route)

    # ---------------- state pages (all 51 US states + DC) ----------------
    state_rank_map = {c: idx + 1 for idx, (c, _) in enumerate(sorted_states)}
    v_slug_map = by_slug(vehicles)

    for code in sorted(states.keys()):
        st = states[code]
        p_st = base_p(code)
        ev = first_of(["ev"], "tesla-model-y-long-range-rwd")
        gas = first_of(["gas"], "toyota-rav4") or first_of(["gas"])
        r_ev, r_gas = monthly_cost(ev, p_st), monthly_cost(gas, p_st)
        nat = states[code]["usdPerKwh"] / us_kwh - 1
        cmp_txt = ("above" if nat > 0 else "below") if abs(nat) > 0.005 else "in line with"
        diff_pct = nat * 100
        diff_sign = "+" if diff_pct > 0 else ""

        rank = state_rank_map[code]
        if rank <= 5:
            rank_tier = "Top 5 lowest in US"
        elif rank <= 13:
            rank_tier = "Lowest quartile (Q1)"
        elif rank <= 26:
            rank_tier = "Lower mid-range (Q2)"
        elif rank <= 38:
            rank_tier = "Upper mid-range (Q3)"
        elif rank <= 46:
            rank_tier = "Highest quartile (Q4)"
        else:
            rank_tier = "Top 5 highest in US"

        ann_save = max(0, (r_gas["monthly"] - r_ev["monthly"]) * 12)

        # Hero Stat Cards
        hero_grid = (
            f'<div class="state-hero-grid">'
            f'<div class="state-stat">'
            f'<div class="state-stat__label">Electricity Rate</div>'
            f'<div class="state-stat__value">{money(st["usdPerKwh"], "$", 4)}<span style="font-size:var(--fs-xs);font-weight:normal;">/kWh</span></div>'
            f'<div class="state-stat__sub">EIA Form 861M average</div>'
            f'</div>'
            f'<div class="state-stat">'
            f'<div class="state-stat__label">National Rank</div>'
            f'<div class="state-stat__value">#{rank} <span style="font-size:var(--fs-xs);font-weight:normal;">of 51</span></div>'
            f'<div class="state-stat__sub">{rank_tier}</div>'
            f'</div>'
            f'<div class="state-stat">'
            f'<div class="state-stat__label">Vs US Average</div>'
            f'<div class="state-stat__value">{diff_sign}{diff_pct:.1f}%</div>'
            f'<div class="state-stat__sub">US avg: {money(us_kwh, "$", 4)}/kWh</div>'
            f'</div>'
            f'<div class="state-stat is-highlight">'
            f'<div class="state-stat__label">Est. Monthly EV Cost</div>'
            f'<div class="state-stat__value">{money(r_ev["monthly"])}<span style="font-size:var(--fs-xs);font-weight:normal;">/mo</span></div>'
            f'<div class="state-stat__sub">1,000 mi ({esc(ev["name"])})</div>'
            f'</div>'
            f'<div class="state-stat is-highlight">'
            f'<div class="state-stat__label">Est. Annual Fuel Savings</div>'
            f'<div class="state-stat__value">+{money(ann_save)}<span style="font-size:var(--fs-xs);font-weight:normal;">/yr</span></div>'
            f'<div class="state-stat__sub">vs 30 MPG petrol car</div>'
            f'</div>'
            f'</div>'
        )

        # Cross-State Quick Switcher with adjacent rank links
        prev_tuple = sorted_states[rank - 2] if rank > 1 else None
        next_tuple = sorted_states[rank] if rank < len(sorted_states) else None

        switcher_options = []
        for c, s in sorted(states.items(), key=lambda x: x[1]["name"]):
            c_rank = state_rank_map[c]
            sel = ' selected="selected"' if c == code else ''
            switcher_options.append(
                f'<option value="/charging-cost/{c.lower()}/"{sel}>{esc(s["name"])} ({money(s["usdPerKwh"], "$", 4)}/kWh · #{c_rank})</option>'
            )

        adjacent_links = []
        if prev_tuple:
            p_code, p_st_obj = prev_tuple
            adjacent_links.append(f'<a href="/charging-cost/{p_code.lower()}/">← #{rank - 1} {esc(p_st_obj["name"])} ({money(p_st_obj["usdPerKwh"], "$", 4)}/kWh)</a>')
        adjacent_links.append('<a href="/charging-cost/">All 51 States Ranked</a>')
        if next_tuple:
            n_code, n_st_obj = next_tuple
            adjacent_links.append(f'<a href="/charging-cost/{n_code.lower()}/">#{rank + 1} {esc(n_st_obj["name"])} ({money(n_st_obj["usdPerKwh"], "$", 4)}/kWh) →</a>')
        adjacent_html = f'<div class="state-switcher-adjacent">{"".join(adjacent_links)}</div>'

        switcher_html = (
            f'<div class="state-switcher-card">'
            f'<div class="state-switcher-inner">'
            f'<div class="state-switcher-label">'
            f'<span>Switch State:</span>'
            f'<select class="state-switcher-select" aria-label="Select state" onchange="if(this.value) window.location.href=this.value">'
            f'{"".join(switcher_options)}'
            f'</select>'
            f'</div>'
            f'<div><a href="/charging-cost/" class="state-stat__sub" style="font-weight:600; text-decoration:underline;">View Complete 51-State Rankings →</a></div>'
            f'</div>'
            f'{adjacent_html}'
            f'</div>'
        )

        # Multi-model cost table
        compare_rows = []
        for v_slug, v_label in COMPARE_VEHICLE_SLUGS:
            veh = v_slug_map.get(v_slug)
            if not veh:
                continue
            r_v = monthly_cost(veh, p_st)
            m_cost = r_v["monthly"]
            y_cost = m_cost * 12
            pm_cost = m_cost / (p_st.get("milesPerMonth") or 1)
            cat = veh["category"]
            cat_badge = f'<span class="badge-powertrain {cat}">{esc(v_label)}</span>'
            compare_rows.append(
                f'<tr>'
                f'<td><strong>{esc(veh["name"])}</strong></td>'
                f'<td>{cat_badge}</td>'
                f'<td><strong>{money(m_cost)}</strong>/mo</td>'
                f'<td>{money(y_cost)}/yr</td>'
                f'<td>{money(pm_cost, "$", 3)}/mi</td>'
                f'</tr>'
            )

        model_table_html = (
            f'<h2>{esc(st["name"])} Charging Costs Across 7 Popular Vehicle Types</h2>'
            f'<p>Estimated monthly and annual costs for 1,000 miles per month at {esc(st["name"])}\'s average residential electricity rate '
            f'({money(st["usdPerKwh"], "$", 4)}/kWh) and petrol price ({money(us_gas)}/gal):</p>'
            f'<div class="table-scroll"><table class="model-cost-table">'
            f'<thead><tr><th>Vehicle Model</th><th>Type</th><th>Est. Monthly</th><th>Est. Annual</th><th>Cost Per Mile</th></tr></thead>'
            f'<tbody>{"".join(compare_rows)}</tbody>'
            f'</table></div>'
        )

        # Local Utilities & Charging Guidance Card
        utilities = STATE_UTILITIES.get(code, [])
        util_tags = "".join(f'<span class="utility-tag">{esc(u)}</span>' for u in utilities)
        utility_card_html = (
            f'<div class="utility-card">'
            f'<h3>Major Electric Utilities in {esc(st["name"])}</h3>'
            f'<p>Residential electricity rates vary across service areas. Primary electric utilities serving {esc(st["name"])} include:</p>'
            f'<div class="utility-tags">{util_tags}</div>'
            f'<p class="utility-tip">'
            f'<strong>Tip:</strong> Many utilities in {esc(st["name"])} offer specialized time-of-use tariffs or off-peak EV charging schedules. '
            f'Charging overnight during off-peak hours (commonly 11 PM to 6 AM) can lower your home charging expenses significantly '
            f'compared to the state average residential tariff of {money(st["usdPerKwh"], "$", 4)}/kWh. '
            f'Check with your electric utility provider to explore available EV-friendly rate plans.'
            f'</p>'
            f'</div>'
        )

        # Localized FAQs
        st_faqs = [
            (f'What is the average residential electricity rate in {esc(st["name"])}?',
             f'{money(st["usdPerKwh"], "$", 4)} per kWh, according to U.S. EIA Form 861M data '
             f'for {esc(period_label(energy["sources"]["electricity"]["period"]))}. '
             f'This ranks {esc(st["name"])} #{rank} out of 51 jurisdictions nationwide ({rank_tier.lower()}).'),
            (f'How much does it cost to charge an electric car monthly in {esc(st["name"])}?',
             f'Around {money(r_ev["monthly"])} a month for 1,000 miles in a {esc(ev["name"])} at '
             f'{esc(st["name"])}\'s average rate of {money(st["usdPerKwh"], "$", 4)}/kWh, before any off-peak utility discounts.'),
            (f'How does EV charging compare to petrol fuel costs in {esc(st["name"])}?',
             f'Driving 1,000 miles in an electric vehicle in {esc(st["name"])} costs about {money(r_ev["monthly"])}, '
             f'compared to approximately {money(r_gas["monthly"])} in a 30 MPG petrol car at {money(us_gas)}/gallon — '
             f'saving roughly {money(ann_save)} per year.'),
            (f'Which electric utilities serve {esc(st["name"])}?',
             f'Major electric providers in {esc(st["name"])} include {", ".join(utilities[:3])}'
             + (f' and others.' if len(utilities) > 3 else '.') +
             f' Many offer off-peak EV charging incentives and time-of-use tariffs.'),
            (f'Can I calculate with my own electricity tariff?',
             'Yes — you can enter your exact utility bill rate into the interactive calculator above to see your customized monthly estimate.'),
            (f'Are public fast charging prices included in this state average?',
             f'No. Residential rates reflect home charging ({money(st["usdPerKwh"], "$", 4)}/kWh). Public DC fast charging networks '
             f'typically average around {money(dcfc)}/kWh nationwide and vary by network and station location.'),
        ]

        # Other states cards
        other_states_cards = [
            ('/charging-cost/', 'All 50 States Ranked', 'Complete US electricity & EV cost leaderboard'),
        ] + [(f'/charging-cost/{o.lower()}/', states[o]['name'],
              f"{money(states[o]['usdPerKwh'], '$', 4)}/kWh")
             for o in STATES_10 if o != code][:5]

        content = [
            '<p class="eyebrow">Free · No signup · Runs in your browser</p>',
            f'<h1>{esc(st["name"])} EV Charging Costs (2026)</h1>',
            f'<p class="lede">The average residential electricity price in {esc(st["name"])} is '
            f'<strong>{money(st["usdPerKwh"], "$", 4)} per kWh</strong> — '
            f'{abs(nat) * 100:.0f}% {cmp_txt} the US average of {money(us_kwh, "$", 4)}/kWh (Ranked <strong>#{rank} of 51</strong>). '
            f'Here is how much it costs to charge an electric car in {esc(st["name"])} per month and per year.</p>',
            rates_strip(energy, regions, f'<span><b>Rates updated:</b> {esc(el_period)}</span>'),
            hero_grid,
            switcher_html,
            calc_widget({"mode": "compare", "groups": json.dumps([["ev"], ["gas"]]),
                         "vehicle-a": ev["slug"], "vehicle-b": gas["slug"],
                         "state": code, "show": ALL_SHOW},
                        prerender_compare([(ev, r_ev), (gas, r_gas)], p_st)),
            f'<h2>Charging an EV in {esc(st["name"])}</h2>',
            f'<p>At {money(st["usdPerKwh"], "$", 4)}/kWh, the {esc(ev["name"])} costs about '
            f'{money(r_ev["monthly"])} a month over 1,000 miles — roughly '
            f'{money(r_ev["monthly"] / 1000, "$", 3)} per mile. The same distance in the '
            f'{esc(gas["name"])} at {money(us_gas)}/gallon costs about {money(r_gas["monthly"])}.</p>',
            model_table_html,
            utility_card_html,
            '<h2>What public fast charging costs here</h2>',
            f'<p>Public DC fast charging is priced by the network, not by the state, and a '
            f'representative US average is around {money(dcfc)}/kWh. Some states require per-minute '
            f'pricing instead of per-kWh, and most networks add idle or session fees — so treat this as '
            f'an estimate rather than a quote.</p>',
            faq_block(st_faqs),
            '<h2>Compare with other states</h2>',
            card_grid(other_states_cards),
            '<h2>Go further</h2>',
            card_grid([
                ('/charging-cost/', 'All 50 States Ranked', 'See where your state stands nationwide'),
                ('/ev-vs-gas-cost-calculator/', 'EV vs Gas', f'The same comparison for {st["name"]}'),
                ('/tesla-charging-cost-calculator/', 'Tesla charging cost', 'Model by model'),
                ('/', 'EV charging cost calculator', 'National average starting point'),
            ]),
            sources_block(energy, regions, vehicles),
        ]
        route = f"/charging-cost/{code.lower()}/"
        write(route, render_page(
            route, f"{st['name']} EV Charging Costs (2026) — Rates & Monthly Cost",
            f"Average residential electricity price in {st['name']} is "
            f"{money(st['usdPerKwh'], '$', 4)}/kWh (Rank #{rank} of 51). Compare 7 EV and gas models and estimate monthly charging costs.",
            "".join(content),
            jsonld=_ld_state_page(
                st['name'], route,
                f"EIA Form 861M residential electricity price and EV charging cost estimate for {st['name']}.",
                st_faqs)), out_root)
        routes.append(route)

    # ---------------- country pages ----------------
    for c in regions["countries"]:
        ev = first_of(["ev"], "tesla-model-y-long-range-rwd")
        p_c = dict(p0)
        p_c["homeRateUsdKwh"] = c["ratePerKwh"]
        # No verified local DC fast-charging price is held for these markets, so
        # the page is costed as 100% home charging rather than blending an
        # unverified public rate (or a USD one) into a local-currency result.
        p_c["homeSharePct"] = 100
        p_c["publicRateUsdKwh"] = c["ratePerKwh"]
        r_ev = monthly_cost(ev, p_c)
        mpk = mi_per_kwh(ev, 55, False)
        kwh100km = 100 / (mpk * 1.609344) if mpk else 0
        c_faqs = [
            (f'What is the average electricity price in {esc(c["name"])}?',
             f'About {esc(c["rateDisplay"])} per kWh for residential customers, per '
             f'{esc(c["source"])} ({esc(c["asOf"])}).'),
            (f'How much does it cost to charge an EV in {esc(c["name"])}?',
             f'Around {esc(c["symbol"])}{r_ev["monthly"]:.2f} a month over 1,000 miles at the '
             f'average rate, depending on the car and your tariff.'),
            ("Why are the car figures from the US EPA?", "Because it is the published, verifiable "
             "dataset available to us. Override the rate and mileage with your own values."),
            ("Can I use my own tariff?", "Yes — every price field is editable."),
            ("Is this a quote?", "No. It is an estimate from published averages."),
            ("Do you include standing charges?", f'No. {esc(c["name"])} tariffs commonly include a '
             "daily standing charge that is not part of the unit rate."),
        ]
        content = [
            f'<p class="eyebrow">Free · No signup · Runs in your browser</p>',
            f'<h1>EV Charging Cost {esc(c["name"])}</h1>',
            f'<p class="lede">The average residential electricity price in {esc(c["name"])} is about '
            f'<strong>{esc(c["rateDisplay"])}/kWh</strong>. Here is what that costs per month, in '
            f'{esc(c["currency"])}.</p>',
            '<div class="notice notice--plain"><p><strong>About this page.</strong> Vehicle efficiency '
            'figures are U.S. EPA-published ratings, because that is the dataset we can verify. '
            'Local vehicle ratings may differ. Electricity prices are local, and every field below can '
            'be overridden with your own tariff.</p></div>',
            rates_strip(energy, regions, f'<span><b>Price source:</b> {esc(c["source"])} '
                                        f'({esc(c["asOf"])})</span>'),
            calc_widget({"mode": "single", "groups": json.dumps([["ev"]]),
                         "vehicle-a": ev["slug"], "state": "",
                         "rate": f'{c["ratePerKwh"]:.4f}', "home-share": "100",
                         "symbol": c["symbol"],
                         "show": ["gasPrice", "loss", "city", "winter"]},
                        prerender_single(ev, p_c, c["symbol"])),
            f'<h2>What an EV costs to run in {esc(c["name"])}</h2>',
            f'<p>At {esc(c["rateDisplay"])}/kWh and the {esc(ev["name"])}\'s '
            f'{mpk:.2f} mi/kWh ({kwh100km:.1f} kWh/100 km), 1,000 miles a month costs about '
            f'{esc(c["symbol"])}{r_ev["monthly"]:.2f}.</p>',
            f'<p class="field__hint">{esc(c["note"])}</p>',
            faq_block(c_faqs),
            '<h2>Other countries</h2>',
            card_grid([(f"/ev-charging-cost/{o['code']}/", o['name'],
                        f"{o['rateDisplay']}/kWh")
                       for o in regions['countries'] if o['code'] != c['code']]),
            '<h2>Go further</h2>',
            card_grid([
                ('/', 'EV charging cost calculator', 'US state prices and the full model list'),
                ('/ev-vs-gas-cost-calculator/', 'EV vs Gas', 'Running cost against petrol'),
                ('/unit-converter/mpg-l100km/', 'MPG \u2194 L/100 km', 'Convert between units'),
            ]),
            sources_block(energy, regions, vehicles),
        ]
        route = f"/ev-charging-cost/{c['code']}/"
        write(route, render_page(
            route, f"EV Charging Cost {c['name']} ({c['rateDisplay']}/kWh)",
            f"Estimate EV charging cost in {c['name']} at the average residential rate of "
            f"{c['rateDisplay']}/kWh.", "".join(content),
            jsonld=_ld_app_faq(f"EV Charging Cost {c['name']}", route,
                               f"Estimate EV charging cost in {c['name']}.", c_faqs)), out_root)
        routes.append(route)

    return routes
