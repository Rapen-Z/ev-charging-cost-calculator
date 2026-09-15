#!/usr/bin/env python3
"""Generate the calculator pages of the site from real EPA / EIA data.

Counterpart of src/calc.js — the monthlyCost() formula below is a deliberate
mirror of the JS implementation. tests/verify_engine.mjs asserts that both
produce identical numbers.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DATA = ROOT.parent / "data"

# Serialised browser payload; set by gen_pages.build() before any page render.
DATA_JSON = "{}"

# PRD §8: "/charging-cost/{state}/ ✅ 首版 10 州"
# Selection rationale: ten largest US light-duty EV markets / most populous
# states, so the first ten pages carry real search demand rather than being
# thin filler. Expanding to all 51 is a one-line change (see STATES_10).
STATES_10 = ["CA", "TX", "FL", "NY", "WA", "IL", "CO", "AZ", "GA", "NC"]

W = DEFAULTS = {
    "milesPerMonth": 1000,
    "homeSharePct": 80,
    "chargingLossPct": 10,
    "citySharePct": 55,
    "winter": False,
    "winterFactor": 0.85,
    "homeCharging": True,
}


# --------------------------------------------------------------- data loading
def load():
    vehicles = json.loads((DATA / "vehicles.json").read_text(encoding="utf-8"))
    energy = json.loads((DATA / "energy.json").read_text(encoding="utf-8"))
    regions = json.loads((DATA / "regions.json").read_text(encoding="utf-8"))
    return vehicles, energy, regions


def browser_payload(vehicles, energy, regions):
    """Trimmed dataset inlined into every calculator page."""
    vs = []
    for v in vehicles["vehicles"]:
        vs.append({
            "s": v["slug"], "n": v["name"], "m": v["make"], "c": v["category"],
            "vc": v.get("vClass", ""),
            "mpk": v.get("miPerKwh") or 0,
            "kC": v.get("kwhPer100MiCity") or 0,
            "kH": v.get("kwhPer100MiHighway") or 0,
            "kX": v.get("kwhPer100MiCombined") or 0,
            "gC": v.get("mpgCity") or 0,
            "gH": v.get("mpgHighway") or 0,
            "gX": v.get("mpgCombined") or 0,
            "uf": v.get("utilityFactor") or 0,
            "er": v.get("evRangeMi") or 0,
        })
    return {
        "vehicles": vs,
        "states": {k: {"n": v["name"], "r": v["usdPerKwh"]} for k, v in energy["states"].items()},
        "usAvgKwh": energy["usAverageUsdPerKwh"],
        "usGas": energy["usAverageGasolineUsdPerGal"],
        "dcfc": regions["dcFastCharging"]["usdPerKwh"],
        "countries": regions["countries"],
        "defaults": {k: DEFAULTS[k] for k in
                     ("milesPerMonth", "homeSharePct", "chargingLossPct",
                      "citySharePct", "winterFactor")},
        "meta": {
            "elecPeriod": energy["sources"]["electricity"]["period"],
            "gasWeek": energy["sources"]["gasoline"]["weekEnding"],
            "vehicleYear": vehicles["dataYear"],
            "fetchedAt": energy["fetchedAt"][:10],
        },
    }


# ------------------------------------------------- formula (mirror of calc.js)
def _num(v, fb=0.0):
    try:
        n = float(v)
        return n if math.isfinite(n) else fb
    except (TypeError, ValueError):
        return fb


def mi_per_kwh(v, city_share=55, winter=False):
    s = max(0.0, min(100.0, _num(city_share, 55))) / 100.0
    city, hwy, comb = _num(v.get("kwhPer100MiCity")), _num(v.get("kwhPer100MiHighway")), _num(v.get("kwhPer100MiCombined"))
    if city > 0 and hwy > 0:
        k = city * s + hwy * (1 - s)
    elif comb > 0:
        k = comb
    else:
        return 0.0
    if winter:
        k = k / DEFAULTS["winterFactor"]
    return 100.0 / k if k > 0 else 0.0


def mpg_of(v, city_share=55, winter=False):
    s = max(0.0, min(100.0, _num(city_share, 55))) / 100.0
    city, hwy, comb = _num(v.get("mpgCity")), _num(v.get("mpgHighway")), _num(v.get("mpgCombined"))
    m = (city * s + hwy * (1 - s)) if (city > 0 and hwy > 0) else comb
    if winter:
        m = m * DEFAULTS["winterFactor"]
    return m if m > 0 else 0.0


def monthly_cost(v, p):
    """Mirror of FuelCost.monthlyCost() in src/calc.js."""
    miles = max(0.0, min(100000.0, _num(p.get("milesPerMonth"), 1000)))
    loss = max(0.0, min(40.0, _num(p.get("chargingLossPct"), 10))) / 100.0
    winter = bool(p.get("winter"))
    home_share = max(0.0, min(100.0, _num(p.get("homeSharePct"), 80))) / 100.0
    out = {"monthly": 0.0, "kwh": 0.0, "gallons": 0.0,
           "electricMiles": 0.0, "gasMiles": 0.0, "note": ""}

    if v.get("category") == "ev":
        mpk = mi_per_kwh(v, p.get("citySharePct"), winter)
        if mpk <= 0:
            return out
        kwh = miles / mpk
        blended = _num(p.get("homeRateUsdKwh")) * home_share + _num(p.get("publicRateUsdKwh")) * (1 - home_share)
        out.update(kwh=kwh, monthly=kwh * blended * (1 + loss), electricMiles=miles)
        return out

    if v.get("category") == "phev":
        uf = _num(v.get("utilityFactor"))
        if winter:
            uf *= DEFAULTS["winterFactor"]
        has_home = p.get("homeCharging", True) is not False
        e_share = uf if has_home else 0.0
        e_miles, g_miles = miles * e_share, miles - miles * e_share
        mpk = mi_per_kwh(v, p.get("citySharePct"), winter)
        mpgp = mpg_of(v, p.get("citySharePct"), winter)
        kwh = e_miles / mpk if mpk > 0 else 0.0
        gal = g_miles / mpgp if mpgp > 0 else 0.0
        blended = _num(p.get("homeRateUsdKwh")) * home_share + _num(p.get("publicRateUsdKwh")) * (1 - home_share)
        out.update(electricMiles=e_miles, gasMiles=g_miles, kwh=kwh, gallons=gal,
                   monthly=kwh * blended * (1 + loss) + gal * _num(p.get("gasUsdPerGal")))
        if not has_home:
            out["note"] = ("Home charging assumed unavailable, so the plug-in hybrid is costed on "
                           f"petrol only at its charge-sustaining economy ({mpgp:.1f} MPG) — i.e. as a conventional hybrid.")
        return out

    m = mpg_of(v, p.get("citySharePct"), winter)
    if m <= 0:
        return out
    gal = miles / m
    out.update(gallons=gal, gasMiles=miles, monthly=gal * _num(p.get("gasUsdPerGal")))
    return out


# ------------------------------------------------------------------ rendering
def money(x, sym="$", dp=2):
    return f"{sym}{x:,.{dp}f}"


def esc(s):
    return html.escape(str(s), quote=True)


def by_slug(vehicles):
    return {v["slug"]: v for v in vehicles["vehicles"]}


def cat_label(c):
    return {"ev": "Battery electric", "phev": "Plug-in hybrid",
            "hev": "Hybrid", "gas": "Petrol"}.get(c, c)


def period_label(period):
    """'2026-06' -> 'June 2026'"""
    try:
        y, m = period.split("-")
        names = ["January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"]
        return f"{names[int(m) - 1]} {y}"
    except Exception:
        return period


def rates_strip(energy, regions, extra=""):
    el = energy["sources"]["electricity"]
    ga = energy["sources"]["gasoline"]
    return (
        '<div class="rates">'
        f'<span><b>Electricity:</b> EIA Form 861M, {esc(period_label(el["period"]))}</span>'
        f'<span><b>Petrol:</b> EIA weekly, week ending {esc(ga["weekEnding"])}</span>'
        f'<span><b>DC fast charging:</b> ${regions["dcFastCharging"]["usdPerKwh"]:.2f}/kWh (network average)</span>'
        f'{extra}</div>'
    )


def sources_block(energy, regions, vehicles):
    return (
        '<div class="sources"><p><strong>Data sources.</strong> '
        'Vehicle efficiency: '
        f'<a href="https://www.fueleconomy.gov/" rel="nofollow noopener" target="_blank">U.S. EPA / DOE fueleconomy.gov</a> '
        f'({esc(str(vehicles["dataYear"]))} model year). '
        'Electricity prices: <a href="https://www.eia.gov/electricity/data/state/" rel="nofollow noopener" target="_blank">'
        f'U.S. EIA Form 861M</a> (residential, {esc(period_label(energy["sources"]["electricity"]["period"]))}). '
        'Fuel prices: <a href="https://www.eia.gov/dnav/pet/pet_pri_gnd_dcus_nus_w.htm" rel="nofollow noopener" target="_blank">'
        f'U.S. EIA weekly retail</a> (week ending {esc(energy["sources"]["gasoline"]["weekEnding"])}). '
        'All figures are estimates, not quotes.</p></div>'
    )


def faq_block(items):
    if not items:
        return ""
    out = ['<div class="faq"><h2>Frequently asked questions</h2>']
    for q, a in items:
        out.append(f'<details class="beam beam--mono"><summary>{esc(q)}</summary><p>{a}</p></details>')
    out.append("</div>")
    return "".join(out)


def calc_widget(spec, results_html):
    """Shell around the calculator. Inputs are rendered by app.js from data-*
    attributes so every page shares one implementation.

    Two progressive-enhancement hooks beyond the pre-rendered result:
      .beam        light travelling the panel border (pure CSS, no JS)
      [data-boot]  the preparing state. It is only visible while JS is on
                   (`.js` is set in <head> before first paint) and is removed
                   by app.js the moment the real inputs are mounted — so it
                   describes a real wait rather than decorating a fast one.
      [data-status]  in-head status line driven by the thinking orb.
    """
    attrs = " ".join(f'data-{k}="{esc(v)}"' for k, v in spec.items() if k != "show")
    show = ",".join(spec.get("show", []))
    return (
        f'<div class="calc beam" data-calc {attrs} data-show="{esc(show)}">'
        '<div class="calc__head"><h2>Your numbers</h2>'
        '<span class="rates" style="border:0;margin:0;padding:0">'
        'Change any value — results update instantly</span>'
        '<span class="status" data-status hidden>'
        '<span class="orb" data-orb="working" data-orb-size="20"></span>'
        '<span class="status__text"></span>'
        '</span></div>'
        '<div class="calc__body">'
        '<div class="calc__inputs" data-inputs>'
        '<div class="calc__boot" data-boot>'
        '<span class="orb" data-orb="working" data-orb-size="64" role="img" '
        'aria-label="Loading the calculator"></span>'
        '<p>Preparing the calculator…</p>'
        '</div>'
        '</div>'
        f'<div class="calc__results" data-results>{results_html}</div>'
        "</div></div>"
    )


# =========================================================== page construction
def render_page(route, title, description, content, tesla=False, jsonld=None,
                extra_head=""):
    tpl = (SRC / "page.html").read_text(encoding="utf-8")
    cfg = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
    ld = jsonld or {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": title, "url": cfg["base"] + route,
        "applicationCategory": "UtilityApplication",
        "operatingSystem": "Any (web browser)",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "description": description,
    }
    return (tpl
            .replace("{{TITLE}}", esc(title))
            .replace("{{DESCRIPTION}}", esc(description))
            .replace("{{CANONICAL}}", route)
            .replace("{{BASE}}", cfg["base"].rstrip("/"))
            .replace("{{SITE_NAME}}", cfg["siteName"])
            .replace("{{SITE_NAME_FIRST}}", cfg["siteNameFirst"])
            .replace("{{SITE_NAME_REST}}", cfg["siteNameRest"])
            .replace("{{YEAR}}", cfg["buildDate"][:4])
            .replace("{{OPERATING_ENTITY}}", esc(cfg["operatingEntity"]))
            .replace("{{CONTENT}}", content)
            .replace("{{TESLA_NOTICE}}", TESLA_NOTICE if tesla else "")
            .replace("{{JSONLD}}",
                     '<script type="application/ld+json">' +
                     json.dumps(ld, ensure_ascii=False) + "</script>")
            # The payload is NOT inlined: 24.5 KB × 52 identical copies made it
            # 62% of every page. It ships once as a cacheable asset instead.
            .replace("{{DATA_SCRIPT}}", '<script defer src="/assets/fuel-data.js"></script>')
            + extra_head)


TESLA_NOTICE = (
    '<div class="tm-notice"><p><strong>Not affiliated with Tesla, Inc.</strong> '
    '"Tesla", "Model 3", "Model Y" and other vehicle names are trademarks or registered '
    'trademarks of their respective owners and are used here for identification and '
    'descriptive purposes only. Use of these names does not imply affiliation, sponsorship '
    'or endorsement.</p></div>'
)


def write(route, html_text, out_root):
    if route == "/":
        p = out_root / "index.html"
    else:
        p = out_root / route.strip("/") / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html_text, encoding="utf-8")
    return p
