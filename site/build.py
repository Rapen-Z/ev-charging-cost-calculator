#!/usr/bin/env python3
"""Build the compliance/legal static site for Cloudflare Pages.

Single source of truth for legal copy is ../legal/*.md (plus src/home.md).
This script renders them into static HTML, emits Cloudflare config files
(_redirects / _headers), robots.txt, sitemap.xml, a 404 page, and then runs a
route/link self-check so that "footer/legal route never 404s" is verified
rather than assumed.

Usage:
    python build.py            # build + self-check
    python build.py --check    # self-check only
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
LEGAL_DIR = ROOT.parent / "legal"
CONFIG = json.loads((SRC / "config.json").read_text(encoding="utf-8"))

BASE = CONFIG["base"].rstrip("/")
DOMAIN = CONFIG["domain"]
SITE_NAME = CONFIG["siteName"]
YEAR = CONFIG["buildDate"][:4]

# Canonical routes (see 04-compliance/04-legal-route-contract.md 搂4.1)
LEGAL_PAGES = ["privacy.md", "terms.md", "cookie-policy.md", "disclaimer.md", "about.md", "contact.md"]

# Alias -> canonical, 308 permanent (see 搂4.2)
REDIRECTS = {
    "/privacy-policy": "/privacy",
    "/privacy-policy/": "/privacy",
    "/privacypolicy": "/privacy",
    "/terms-of-service": "/terms",
    "/terms-and-conditions": "/terms",
    "/terms-of-use": "/terms",
    "/tos": "/terms",
    "/cookie": "/cookie-policy",
    "/cookies": "/cookie-policy",
    "/cookie-notice": "/cookie-policy",
    "/legal-disclaimer": "/disclaimer",
    "/contact-us": "/contact",
    "/about-us": "/about",
    "/refund": "/terms#no-purchases",
    "/refund-policy": "/terms#no-purchases",
    "/returns": "/terms#no-purchases",
}

# ---------------------------------------------------------------- markdown ---

HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
ANCHOR_RE = re.compile(r"\s*\{#([a-z0-9\-]+)\}\s*$")


def slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^\w\s\-]", "", t)
    t = re.sub(r"[\s_]+", "-", t)
    return t.strip("-")


def inline(s: str) -> str:
    """Minimal inline markdown: links, bold, italic, code."""
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def render_markdown(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # fenced code
        if line.strip().startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(html.escape(lines[i], quote=False))
                i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue

        # raw HTML passthrough (used sparingly, e.g. <div class="notice">)
        if line.strip().startswith("<"):
            buf = [line]
            i += 1
            while i < n and lines[i].strip() != "":
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue

        # blank
        if not line.strip():
            i += 1
            continue

        # heading
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            anchor = None
            am = ANCHOR_RE.search(text)
            if am:
                anchor = am.group(1)
                text = ANCHOR_RE.sub("", text)
            else:
                anchor = slugify(text)
            out.append(f'<h{level} id="{anchor}">{inline(text)}</h{level}>')
            i += 1
            continue

        # table
        if line.strip().startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            body = []
            header = rows[0]
            start = 1
            if len(rows) > 1 and all(re.fullmatch(r":?-{2,}:?", c) for c in rows[1]):
                start = 2
            body.append("<div class=\"table-scroll\"><table><thead><tr>")
            body.append("".join(f"<th>{inline(c)}</th>" for c in header))
            body.append("</tr></thead><tbody>")
            for r in rows[start:]:
                body.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            body.append("</tbody></table></div>")
            out.append("".join(body))
            continue

        # blockquote
        if line.strip().startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + render_markdown("\n\n".join(buf)) + "</blockquote>")
            continue

        # lists
        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            buf = []
            while i < n:
                cur = lines[i]
                if not cur.strip():
                    # allow continuation only if next line is indented
                    if i + 1 < n and re.match(r"^\s{2,}\S", lines[i + 1]):
                        i += 1
                        continue
                    break
                mo = re.match(r"^\s*\d+\.\s+(.*)$", cur) if ordered else re.match(r"^\s*[-*]\s+(.*)$", cur)
                if mo:
                    buf.append(mo.group(1))
                    i += 1
                elif re.match(r"^\s{2,}\S", cur) and buf:
                    buf[-1] += " " + cur.strip()
                    i += 1
                else:
                    break
            tag = "ol" if ordered else "ul"
            out.append(f'<{tag}>' + "".join(f"<li>{inline(b)}</li>" for b in buf) + f"</{tag}>")
            continue

        # paragraph
        buf = []
        while i < n and lines[i].strip() and not HEADING_RE.match(lines[i]) \
                and not lines[i].strip().startswith(("|", ">", "<", "```")) \
                and not re.match(r"^\s*[-*]\s+", lines[i]) and not re.match(r"^\s*\d+\.\s+", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append("<p>" + inline(" ".join(buf)) + "</p>")
        continue

    return "\n".join(out)


def parse_frontmatter(text: str):
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n", 1)
    rest = parts[1] if len(parts) > 1 else ""
    end = rest.find("\n---")
    if end == -1:
        return {}, text
    fm_raw = rest[:end]
    body = rest[end + 4:].lstrip("\n")
    fm = {}
    for line in fm_raw.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


# ------------------------------------------------------------------ render ---

LAYOUT = (SRC / "layout.html").read_text(encoding="utf-8")


def jsonld(title: str, route: str, description: str, is_contact: bool) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": f"{BASE}{route}",
        "inLanguage": "en",
        "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": f"{BASE}/"},
        "publisher": {"@type": "Organization", "name": CONFIG["operatingEntity"]},
    }
    if is_contact:
        data["about"] = {
            "@type": "ContactPoint",
            "contactType": "customer support",
            "email": CONFIG["contactEmail"],
            "url": f"{BASE}/contact",
        }
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


TESLA_NOTICE = (
    '<div class="tm-notice"><p><strong>Not affiliated with Tesla, Inc.</strong> '
    '"Tesla", "Model 3", "Model Y" and other vehicle names are trademarks or registered trademarks '
    "of their respective owners and are used here for identification and descriptive purposes only. "
    "Use of these names does not imply affiliation, sponsorship or endorsement.</p></div>"
)


def render_page(title, route, description, updated, content, tesla=False, is_contact=False, extra_head=""):
    canonical = route
    head = LAYOUT
    html_out = (
        LAYOUT.replace("{{TITLE}}", html.escape(title, quote=False))
        .replace("{{DESCRIPTION}}", html.escape(description, quote=False))
        .replace("{{CANONICAL}}", canonical)
        .replace("{{BASE}}", BASE)
        .replace("{{SITE_NAME}}", SITE_NAME)
        .replace("{{SITE_NAME_FIRST}}", CONFIG["siteNameFirst"])
        .replace("{{SITE_NAME_REST}}", CONFIG["siteNameRest"])
        .replace("{{YEAR}}", YEAR)
        .replace("{{OPERATING_ENTITY}}", html.escape(CONFIG["operatingEntity"], quote=False))
        .replace("{{CONTACT_EMAIL}}", CONFIG["contactEmail"])
        .replace("[CONTACT EMAIL]", CONFIG["contactEmail"])
        .replace("{{CONTENT}}", content)
        .replace("{{TESLA_NOTICE}}", TESLA_NOTICE if tesla else "")
        .replace("{{JSONLD}}", jsonld(title, route, description, is_contact) + extra_head)
    )
    return html_out


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


# -------------------------------------------------------------------- build ---

def build() -> None:
    print("Building site 鈥?)

    # assets
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for f in ("styles.css", "consent.js", "calc.js", "app.js", "orb.js", "favicon.svg"):
        shutil.copyfile(SRC / f, assets / f)
        print(f"  wrote assets/{f}")

    # ZIP -> state table (PRD 搂8 MVP-4); optional, build must not break without it
    zips_src = ROOT.parent / "data" / "zips.json"
    if zips_src.exists():
        shutil.copyfile(zips_src, assets / "zips.json")
        print("  wrote assets/zips.json")
    else:
        print("  WARN  data/zips.json missing 鈥?ZIP lookup disabled")

    routes = []

    # NOTE: "/" and every calculator route are generated by gen_pages.py.

    # legal pages
    for fname in LEGAL_PAGES:
        src = LEGAL_DIR / fname
        fm, body = parse_frontmatter(src.read_text(encoding="utf-8"))
        route = fm.get("route", "/" + src.stem)
        title = fm.get("title", src.stem.title())
        content = render_markdown(body)
        meta = (
            f'<p class="eyebrow">{html.escape(SITE_NAME, quote=False)}</p>'
            f'<div class="meta"><span><b>Last updated:</b> {fm.get("updated", CONFIG["buildDate"])}</span>'
            f'<span><b>Applies to:</b> all pages on this site</span></div>'
        )
        is_contact = route == "/contact"
        write(ROOT / route.strip("/") / "index.html", render_page(
            title, route, fm.get("description", ""), fm.get("updated", ""),
            meta + content, tesla=fm.get("tesla") == "true", is_contact=is_contact))
        routes.append(route)

    # calculator pages (PRD 搂8 routes) 鈥?generated from real EPA/EIA data
    import gen_pages
    data_dir = ROOT.parent / "data"
    vehicles = json.loads((data_dir / "vehicles.json").read_text(encoding="utf-8"))
    energy = json.loads((data_dir / "energy.json").read_text(encoding="utf-8"))
    regions = json.loads((data_dir / "regions.json").read_text(encoding="utf-8"))
    routes += gen_pages.build(vehicles, energy, regions, ROOT)

    # Shared, cacheable calculator payload 鈥?written once, referenced by every
    # calculator page. gen_pages.build() sets gen.DATA_JSON.
    write(assets / "fuel-data.js", "window.FUEL_DATA=" + gen_pages.gen.DATA_JSON + ";\n")

    # 404
    nf = (
        '<p class="eyebrow">Error 404</p><h1>Page not found</h1>'
        '<div class="measure"><p>That page does not exist. It may have been moved, or the link may be wrong.</p>'
        '<ul><li><a href="/">Home</a></li><li><a href="/privacy">Privacy Policy</a></li>'
        '<li><a href="/terms">Terms of Service</a></li><li><a href="/cookie-policy">Cookie Policy</a></li>'
        '<li><a href="/disclaimer">Disclaimer</a></li><li><a href="/about">About</a></li>'
        '<li><a href="/contact">Contact</a></li></ul></div>'
    )
    write(ROOT / "404.html", render_page(
        "Page not found", "/404", "The page you requested could not be found.",
        CONFIG["buildDate"], nf).replace('content="index, follow"', 'content="noindex, follow"'))
    routes.append("/404")

    # _redirects  (308 alias redirects; handled natively by Workers Static Assets)
    # NOTE: do NOT add `/*  /404  404` here 鈥?a 404 status code is invalid in a
    # _redirects file, and the 404 fallback is provided by wrangler.toml
    # `assets.not_found_handling = "404-page"` (serves 404.html with a 404 status).
    lines = [f"{src}  {dst}  308" for src, dst in REDIRECTS.items()]
    write(ROOT / "_redirects", "\n".join(lines) + "\n")

    # _headers  (Referrer-Policy mitigates query-string leakage 鈥?see P1-1 / K7)
    write(ROOT / "_headers", "\n".join([
        "/*",
        "  X-Content-Type-Options: nosniff",
        "  Referrer-Policy: strict-origin-when-cross-origin",
        "  X-Frame-Options: DENY",
        "  Permissions-Policy: geolocation=(), camera=(), microphone=()",
        "  Strict-Transport-Security: max-age=31536000; includeSubDomains",
        "",
    ]))

    # robots.txt
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")

    # IndexNow verification key
    write(ROOT / "8ae5d014253147388f7094b08cca009f.txt", "8ae5d014253147388f7094b08cca009f")

    # llm.txt for AI/LLM indexing and discovery
    llm_lines = [
        f"# {SITE_NAME}",
        "",
        "> Comprehensive EV, PHEV, hybrid, and petrol charging and fuel cost calculator based on official U.S. EPA and EIA Form 861M data across all 50 U.S. states and DC.",
        "",
        "## Overview",
        f"{SITE_NAME} ({BASE}) is a free, real-time web calculator for estimating and comparing electric vehicle charging costs, gas costs, plug-in hybrid (PHEV) fuel splits, and hybrid vehicle operating costs. All energy prices are grounded in U.S. Energy Information Administration (EIA Form 861M residential electricity, weekly retail gasoline) and U.S. Environmental Protection Agency (EPA Model Year 2026 fueleconomy.gov) datasets.",
        "",
        "## Core Calculators",
        f"- [Universal EV Charging Cost Calculator]({BASE}/): Estimate monthly and annual home and public charging costs for any EV, PHEV, hybrid, or gas vehicle. Includes efficiency, electric rates, charging loss, and winter temperature penalty controls.",
        f"- [Tesla Charging Cost Calculator]({BASE}/tesla-charging-cost-calculator/): Specialized charging cost calculator for Tesla Model 3, Model Y, Model S, Model X, and Cybertruck across standard range, long range, and performance trims.",
        f"- [EV vs Gas Cost Calculator]({BASE}/ev-vs-gas-cost-calculator/): Direct side-by-side fuel comparison between battery electric vehicles and gas-powered vehicles with monthly dollar savings and annual fuel economics.",
        f"- [PHEV Charging Cost Calculator]({BASE}/phev-charging-cost-calculator/): Plug-in hybrid calculator implementing the SAE J2841 / EPA Utility Factor curve to split electric miles from gasoline miles.",
        f"- [EV vs PHEV vs Hybrid vs Gas Comparison]({BASE}/ev-vs-phev-vs-hybrid-vs-gas/): Comprehensive 4-way vehicle powertrain comparison for total monthly and annual fuel expenditures.",
        "",
        "## 50-State Electricity & Charging Cost Index",
        f"- [US State EV Charging Cost Leaderboard]({BASE}/charging-cost/): Interactive ranking and comparison of all 50 U.S. states and the District of Columbia by residential electricity rate, monthly EV charging cost per 1,000 miles, and equivalent gas mileage cost.",
        "State profiles:",
    ]
    for code, info in sorted(energy.get("states", {}).items()):
        name = info.get("name", code)
        cents = info.get("centsPerKwh", 0)
        llm_lines.append(f"- [{name} EV Charging Cost]({BASE}/charging-cost/{code.lower()}/): {name} residential electricity rate average of {cents:.2f}垄/kWh.")
    llm_lines += [
        "",
        "## Popular Vehicle Models Included",
        "- Tesla: Model 3 (Standard RWD, Long Range, Performance), Model Y (RWD, Long Range AWD, Performance), Model S (Dual Motor, Plaid), Model X, Cybertruck (AWD, Cyberbeast)",
        "- Ford: Mustang Mach-E (Select, Premium, GT), F-150 Lightning (Pro, Flash, Lariat, Platinum)",
        "- Chevrolet: Bolt EV / EUV, Equinox EV, Blazer EV, Silverado EV",
        "- Hyundai & Kia: Ioniq 5, Ioniq 6, EV6, EV9",
        "- BMW & Mercedes-Benz: BMW i4, BMW iX, Mercedes EQE, EQS",
        "- Rivian: R1T, R1S",
        "- Gasoline & Hybrid Benchmarks: Toyota Camry Hybrid, Honda Accord Hybrid, Toyota RAV4 Hybrid, Toyota RAV4 Prime PHEV, Ford F-150 Gas, Honda Civic",
        "",
        "## Calculation Methodology & Formulas",
        "- Electric Vehicle (EV) Monthly Cost: (Monthly Miles / Efficiency mi_per_kWh) * Blended Electricity Rate * (1 + Charging Loss)",
        "  - Blended Rate = (Home Rate * Home Share %) + (Public Rate * (1 - Home Share %))",
        "  - Default charging efficiency loss: 10% (Level 2 AC wallbox conversion and battery thermal overhead).",
        "  - Winter temperature adjustment: 20% range penalty (winter factor 0.80x) when winter mode is selected.",
        "- Gas Vehicle Monthly Cost: (Monthly Miles / MPG) * Gas Price ($/gal)",
        "- Plug-in Hybrid (PHEV) Cost: Electric miles split via EPA Utility Factor curve; electricity and petrol costs calculated separately and summed.",
        "",
        "## Data Sources & Lineage",
        "- U.S. EPA / DOE Fuel Economy: 2026 Model Year official dynamometer ratings from fueleconomy.gov.",
        f"- U.S. Energy Information Administration (EIA) Form 861M: Monthly Electric Power Industry Report for state-by-state residential retail electricity rates ({energy['sources']['electricity']['period']}).",
        f"- U.S. Energy Information Administration (EIA) Weekly Petroleum Status: Weekly retail regular motor gasoline prices (week ending {energy['sources']['gasoline']['weekEnding']}).",
        f"- Public DC Fast Charging Average: Aggregated national benchmark (${regions['dcFastCharging']['usdPerKwh']:.2f}/kWh).",
        "",
        "## Legal & About",
        f"- [About Us]({BASE}/about): Mission, author, and calculation methodology.",
        f"- [Contact]({BASE}/contact): Inquiries and feedback (support@evchargingcost.online).",
        f"- [Privacy Policy]({BASE}/privacy): In-browser data processing and privacy practices.",
        f"- [Terms of Service]({BASE}/terms): Terms of usage.",
        f"- [Cookie Policy]({BASE}/cookie-policy): Cookie disclosures.",
        f"- [Disclaimer]({BASE}/disclaimer): Disclaimers and estimates notice.",
        "",
    ]
    write(ROOT / "llm.txt", "\n".join(llm_lines))

    # sitemap.xml (canonical only 鈥?no aliases)
    urls = ["/"] + [r for r in dict.fromkeys(routes) if r not in ("/", "/404")]
    LEGAL_ROUTES = {"/privacy", "/terms", "/cookie-policy", "/disclaimer", "/about", "/contact"}

    def priority(u: str) -> str:
        if u == "/":
            return "1.0"
        if u in LEGAL_ROUTES:
            return "0.3"
        if u.count("/") == 2:          # top-level calculator hubs
            return "0.8"
        return "0.6"

    items = "\n".join(
        f"  <url><loc>{BASE}{u}</loc><lastmod>{CONFIG['buildDate']}</lastmod>"
        f"<changefreq>monthly</changefreq><priority>{priority(u)}</priority></url>"
        for u in urls
    )
    write(ROOT / "sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n')

    print(f"Built {len(routes)} routes.")


# -------------------------------------------------------------------- check ---

def check() -> int:
    print("\nSelf-check 鈥?)
    failures: list[str] = []

    # exclude src/ (templates, not build output)
    html_files = sorted(f for f in ROOT.rglob("*.html")
                        if SRC not in f.parents and f.parent != SRC)
    print(f"  {len(html_files)} HTML files found")

    # 1. collect internal links
    internal: set[str] = set()
    for f in html_files:
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r'href="(/[^"#?]*)', text):
            internal.add(m.group(1))

    # 2. verify each resolves
    def resolve(path: str) -> bool:
        p = path.lstrip("/")
        if p == "":
            return (ROOT / "index.html").exists()
        candidates = [ROOT / p, ROOT / p / "index.html", ROOT / (p + ".html")]
        return any(c.exists() for c in candidates)

    missing = sorted(p for p in internal if not resolve(p))
    if missing:
        failures.append("Broken internal links (would 404): " + ", ".join(missing))
    else:
        print(f"  OK  all {len(internal)} internal links resolve (no 404)")

    # 3. canonical routes present
    required = ["/", "/privacy", "/terms", "/cookie-policy", "/disclaimer", "/about", "/contact", "/404"]
    absent = [r for r in required if not resolve(r)]
    if absent:
        failures.append("Missing canonical routes: " + ", ".join(absent))
    else:
        print("  OK  all 8 canonical routes present")

    # 4. footer legal links present on every page
    footer_links = ['/privacy', '/terms', '/cookie-policy', '/disclaimer', '/about', '/contact']
    for f in html_files:
        if f.name == "404.html":
            continue
        t = f.read_text(encoding="utf-8")
        lack = [l for l in footer_links if f'href="{l}"' not in t]
        if lack:
            failures.append(f"{f.name}: footer missing {lack}")
    if not any("footer missing" in x for x in failures):
        print("  OK  footer carries all 6 legal links on every page")

    # 5. redirects complete + single-hop
    rd = (ROOT / "_redirects").read_text(encoding="utf-8")
    for src, dst in REDIRECTS.items():
        if f"{src}  {dst}  308" not in rd:
            failures.append(f"_redirects missing {src} -> {dst}")
    if not any("_redirects missing" in x for x in failures):
        print(f"  OK  {len(REDIRECTS)} alias redirects emit 308")

    # 6. no third-party resource references (decision K4)
    third_party = ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net",
                   "unpkg.com", "cdnjs.cloudflare.com")
    for f in html_files:
        t = f.read_text(encoding="utf-8")
        hits = [d for d in third_party if d in t]
        if hits:
            failures.append(f"{f.name}: third-party resource {hits}")
    if not any("third-party resource" in x for x in failures):
        print("  OK  zero third-party font/CDN references (self-hosted)")

    # 7. trackers disabled in config
    consent = (SRC / "consent.js").read_text(encoding="utf-8")
    if "enabled: false" not in consent:
        failures.append("consent.js: no tag is marked enabled:false")
    else:
        print("  OK  all non-essential tags ship disabled (consent gate)")

    # 8. banned expressions (04-compliance/05-banned-expressions.md A鈥揊, hard gate)
    # A match is excused when it sits inside a disclaimer or negation 鈥?"we are
    # not affiliated with, endorsed by, or sponsored by" is the mandated
    # wording, not a claim. Without this the scanner would fail on the exact
    # sentences the compliance stage requires.
    NEGATION = re.compile(
        r"\b(?:not|never|nor|without|cannot|can not)\b|\bn't\b|\bdo(?:es)? not\b|"
        r"\b(?:is|are|were|was) not\b|\bno\b|\bas if\b|\bmisrepresentation\b|"
        r"\bprohibit(?:ed|s)?\b|\bdo not\b|\bclaim(?:s|ed|ing)?\b", re.I)
    BANNED = [
        ("A trademark/attribution", r"\bofficial(?:ly)?\b|\bapproved by\b|\bcertified by\b|"
                                    r"\bendorsed by\b|\bpartnered with\b|\bofficial partner\b"),
        ("B accuracy claims", r"100\s*%\s*accurate|100\s*%\s*exact|perfectly accurate|"
                              r"\bexact cost\b|exact bill|precise bill|real-time rates|live pricing|"
                              r"up-to-the-minute|official EIA|official EPA|official figures|"
                              r"to the penny|down to the cent|verified by|audited by"),
        ("C promises", r"\bguarantee(?:d|s)?\b|risk-free|\bno risk\b|always free|free forever|"
                       r"\bunlimited\b|\bno limits\b|you will save|\bmost accurate\b"),
        ("D privacy self-certification", r"do not collect any data|collect zero data|"
                                         r"no data is collected|GDPR compliant|CCPA compliant|"
                                         r"fully compliant|bank-level security|military-grade|"
                                         r"never share your data|anonymous by default"),
        # time-of-use is only banned as a *feature promise*; naming it in a
        # caveat ("before any time-of-use discount") is required for honesty.
        ("F project NOT-DO", r"trip planner|route cost|road trip|total cost of ownership|\bTCO\b|"
                             r"insurance cost|maintenance cost|charging station map|"
                             r"find chargers near me|\bAI-powered\b|\bAI-generated\b|\bE85\b|"
                             r"time-of-use (?:rates?|calculator|lookup|pricing plan)"),
    ]
    banned_hits: list[str] = []
    for f in html_files:
        text = f.read_text(encoding="utf-8")
        text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S)   # data payload, not copy
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text)
        for group, pattern in BANNED:
            for m in re.finditer(pattern, text, flags=re.I):
                window = text[max(0, m.start() - 110):m.end() + 110]
                if NEGATION.search(window):
                    continue
                banned_hits.append(f"{f.relative_to(ROOT).as_posix()}: [{group}] "
                                   f"\"{m.group(0)}\" 鈥?鈥window.strip()}鈥?)
    if banned_hits:
        failures.append(f"{len(banned_hits)} banned-expression hit(s):\n      " +
                        "\n      ".join(banned_hits[:20]))
    else:
        print(f"  OK  banned-expression scan clean across {len(html_files)} pages "
              f"({len(BANNED)} groups)")

    # liveness control: a dead gate that passes everything is worse than no gate
    for control in ("100% accurate", "we are endorsed by Tesla", "GDPR compliant",
                    "total cost of ownership"):
        if not any(re.search(p, control, re.I) and not NEGATION.search(control)
                   for _, p in BANNED):
            failures.append(f"banned-expression gate is not catching \"{control}\" 鈥?regex is dead")
    if not any("gate is not catching" in x for x in failures):
        print("  OK  banned-expression gate is live (control phrases are caught)")

    # 8b. placeholder inventory (informational, not a failure)
    ph = re.compile(r"\[[A-Z][A-Z0-9_ ]*\]")
    found: dict[str, set[str]] = {}
    for f in html_files:
        hits = set(ph.findall(f.read_text(encoding="utf-8")))
        if hits:
            found[f.relative_to(ROOT).as_posix()] = hits
    if found:
        print(f"  INFO  {len(found)} pages contain placeholders (must be replaced before launch):")
        for k, v in sorted(found.items()):
            print(f"        {k}: {', '.join(sorted(v))}")

    print()
    if failures:
        for x in failures:
            print("  FAIL  " + x)
        return 1
    print("SELF-CHECK PASSED")
    return 0


# -------------------------------------------------------------------- stage ---

# present in site/ for development, but must never be published. Serving them
# at the site root would expose the build scripts, the templates and the tests.
UNPUBLISHED = {"build.py", "gen.py", "gen_pages.py", "src", "tests", "__pycache__"}


def stage() -> None:
    """Mirror the publishable part of site/ into dist/, which is the directory
    wrangler uploads. Rebuilt from scratch each time, so the deploy artefact is
    exactly the verified site and nothing else."""
    dist = ROOT.parent / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    copied = 0
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if path.is_dir() or rel.parts[0] in UNPUBLISHED or path.suffix in (".py", ".pyc"):
            continue
        target = dist / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        copied += 1
    print(f"\nStaged {copied} publishable files -> dist/")


if __name__ == "__main__":
    if "--check" not in sys.argv:
        build()
    code = check()
    if code == 0 and "--check" not in sys.argv:
        stage()
    sys.exit(code)

