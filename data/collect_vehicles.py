#!/usr/bin/env python3
"""Collect real vehicle efficiency data from the official U.S. EPA fueleconomy.gov API.

Source : U.S. Environmental Protection Agency / U.S. DOE — fueleconomy.gov web services
Docs   : https://www.fueleconomy.gov/feg/ws/index.shtml
No API key required for these endpoints.

Outputs data/vehicles.json with provenance (source, sourceUrl, fetchedAt, dataYear).
Nothing in this file invents numbers: every figure comes from the EPA response.
"""
from __future__ import annotations

import json
import sys
import re
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://www.fueleconomy.gov/ws/rest"
OUT = Path(__file__).resolve().parent / "vehicles.json"

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def get(url: str, tries: int = 4) -> str:
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (fuel-cost-calc)"})
            with urllib.request.urlopen(req, timeout=45, context=_ctx) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:          # transient SSL EOF happens on this host
            last = e
            time.sleep(1.0 * (i + 1))
    raise last


def f(xml: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", xml, re.S)
    return m.group(1).strip() if m else ""


def num(xml: str, tag: str) -> float:
    v = f(xml, tag)
    try:
        return float(v)
    except ValueError:
        return 0.0


def models(make: str, year: int) -> list[str]:
    u = f"{BASE}/vehicle/menu/model?year={year}&make={urllib.parse.quote(make)}"
    return re.findall(r"<value>(.*?)</value>", get(u))


def trims(year: int, make: str, model: str):
    u = (f"{BASE}/vehicle/menu/options?year={year}"
         f"&make={urllib.parse.quote(make)}&model={urllib.parse.quote(model)}")
    return re.findall(r"<menuItem><text>(.*?)</text><value>(.*?)</value></menuItem>", get(u), re.S)


# ---- curated list -----------------------------------------------------------
# (make, model regex, category, display name, slug)   category: ev | phev | hev | gas
SPEC: list[tuple[str, str, str, str, str]] = [
    # ---------- BEV ----------
    ("Tesla", r"^Model Y Long Range RWD$", "ev", "Tesla Model Y Long Range RWD", "tesla-model-y-long-range-rwd"),
    ("Tesla", r"^Model Y Long Range AWD$", "ev", "Tesla Model Y Long Range AWD", "tesla-model-y-long-range-awd"),
    ("Tesla", r"^Model Y Standard RWD \(19in Wheels\)$", "ev", "Tesla Model Y Standard RWD", "tesla-model-y-standard-rwd"),
    ("Tesla", r"^Model Y Performance AWD$", "ev", "Tesla Model Y Performance AWD", "tesla-model-y-performance-awd"),
    ("Tesla", r"^Model 3 Premium RWD$", "ev", "Tesla Model 3 Premium RWD", "tesla-model-3-premium-rwd"),
    ("Tesla", r"^Model 3 Premium AWD$", "ev", "Tesla Model 3 Premium AWD", "tesla-model-3-premium-awd"),
    ("Tesla", r"^Model 3 Performance AWD$", "ev", "Tesla Model 3 Performance AWD", "tesla-model-3-performance-awd"),
    ("Tesla", r"^Model S$", "ev", "Tesla Model S", "tesla-model-s"),
    ("Tesla", r"^Model X$", "ev", "Tesla Model X", "tesla-model-x"),
    ("Tesla", r"^Cybertruck AWD$", "ev", "Tesla Cybertruck AWD", "tesla-cybertruck-awd"),
    ("Ford", r"^Mustang Mach-E RWD$", "ev", "Ford Mustang Mach-E RWD", "ford-mustang-mach-e-rwd"),
    ("Hyundai", r"^Ioniq 5 RWD$", "ev", "Hyundai Ioniq 5 RWD", "hyundai-ioniq-5-rwd"),
    ("Hyundai", r"^Ioniq 5 AWD \(19inch Wheels\)$", "ev", "Hyundai Ioniq 5 AWD", "hyundai-ioniq-5-awd"),
    ("Hyundai", r"^Ioniq 9 RWD$", "ev", "Hyundai Ioniq 9 RWD", "hyundai-ioniq-9-rwd"),
    ("Kia", r"^EV6 Long Range RWD$", "ev", "Kia EV6 Long Range RWD", "kia-ev6-long-range-rwd"),
    ("Kia", r"^EV9 Long Range RWD$", "ev", "Kia EV9 Long Range RWD", "kia-ev9-long-range-rwd"),
    ("Kia", r"^Niro Electric$", "ev", "Kia Niro Electric", "kia-niro-electric"),
    ("Chevrolet", r"^Equinox EV FWD$", "ev", "Chevrolet Equinox EV FWD", "chevrolet-equinox-ev-fwd"),
    ("Chevrolet", r"^Blazer EV FWD$", "ev", "Chevrolet Blazer EV FWD", "chevrolet-blazer-ev-fwd"),
    ("Nissan", r"^LEAF 75kWh \(18 inch alloy Wheels\)$", "ev", "Nissan LEAF 75kWh", "nissan-leaf-75kwh"),
    ("Nissan", r"^ARIYA FWD 87kWh$", "ev", "Nissan ARIYA FWD 87kWh", "nissan-ariya-fwd-87kwh"),
    ("Rivian", r"^R1S Dual Large \(20in\)$", "ev", "Rivian R1S Dual Large", "rivian-r1s-dual-large"),
    ("Rivian", r"^R1T Dual Large \(20in\)$", "ev", "Rivian R1T Dual Large", "rivian-r1t-dual-large"),
    ("Honda", r"^Prologue FWD$", "ev", "Honda Prologue FWD", "honda-prologue-fwd"),
    ("BMW", r"^i4 eDrive40 Gran Coupe \(18 inch wheels\)$", "ev", "BMW i4 eDrive40", "bmw-i4-edrive40"),
    ("Polestar", r"^3 Long Range Single Motor \(20 Inch Wheels\)$", "ev", "Polestar 3 Long Range Single Motor", "polestar-3-long-range"),
    ("Lucid", r"^Air Pure RWD with 19 inch wheels$", "ev", "Lucid Air Pure RWD", "lucid-air-pure-rwd"),
    ("Volvo", r"^EX30 Single motor extended range$", "ev", "Volvo EX30 Single Motor Extended Range", "volvo-ex30-single-motor"),
    ("Genesis", r"^GV60 RWD$", "ev", "Genesis GV60 RWD", "genesis-gv60-rwd"),
    ("Toyota", r"^bZ AWD$", "ev", "Toyota bZ AWD", "toyota-bz-awd"),
    ("Subaru", r"^Solterra AWD$", "ev", "Subaru Solterra AWD", "subaru-solterra-awd"),
    ("Audi", r"^Q4 45 e-tron$", "ev", "Audi Q4 45 e-tron", "audi-q4-45-e-tron"),
    ("Volkswagen", r"^ID\.4$", "ev", "Volkswagen ID.4", "volkswagen-id-4"),

    # ---------- PHEV ----------
    ("Kia", r"^Niro Plug-in Hybrid$", "phev", "Kia Niro Plug-in Hybrid", "kia-niro-phev"),
    ("Kia", r"^Sportage Plug-in Hybrid$", "phev", "Kia Sportage Plug-in Hybrid", "kia-sportage-phev"),
    ("Kia", r"^Sorento Plug-in Hybrid$", "phev", "Kia Sorento Plug-in Hybrid", "kia-sorento-phev"),
    ("Jeep", r"^Wrangler 4dr 4xe$", "phev", "Jeep Wrangler 4xe", "jeep-wrangler-4xe"),
    ("Jeep", r"^Grand Cherokee 4xe$", "phev", "Jeep Grand Cherokee 4xe", "jeep-grand-cherokee-4xe"),
    ("Chrysler", r"^Pacifica Hybrid$", "phev", "Chrysler Pacifica Hybrid", "chrysler-pacifica-hybrid"),
    ("Ford", r"^Escape FWD PHEV$", "phev", "Ford Escape Plug-in Hybrid", "ford-escape-phev"),
    ("Hyundai", r"^Tucson Plug-in Hybrid$", "phev", "Hyundai Tucson Plug-in Hybrid", "hyundai-tucson-phev"),
    ("Volvo", r"^XC60 T8 AWD$", "phev", "Volvo XC60 T8 AWD", "volvo-xc60-t8-awd"),
    ("Volvo", r"^XC90 T8 AWD$", "phev", "Volvo XC90 T8 AWD", "volvo-xc90-t8-awd"),
    ("BMW", r"^X5 xDrive50e$", "phev", "BMW X5 xDrive50e", "bmw-x5-xdrive50e"),
    ("Subaru", r"^Crosstrek Hybrid AWD$", "phev", "Subaru Crosstrek Hybrid AWD", "subaru-crosstrek-hybrid"),

    # ---------- HEV ----------
    ("Toyota", r"^Camry HEV FF LE$", "hev", "Toyota Camry Hybrid LE", "toyota-camry-hybrid-le"),
    ("Toyota", r"^Corolla Hybrid$", "hev", "Toyota Corolla Hybrid", "toyota-corolla-hybrid"),
    ("Toyota", r"^Prius$", "hev", "Toyota Prius", "toyota-prius"),
    ("Toyota", r"^RAV4 Hybrid AWD Woodland Edition$", "hev", "Toyota RAV4 Hybrid AWD", "toyota-rav4-hybrid-awd"),
    ("Toyota", r"^Highlander Hybrid AWD$", "hev", "Toyota Highlander Hybrid AWD", "toyota-highlander-hybrid-awd"),
    ("Honda", r"^Accord Hybrid$", "hev", "Honda Accord Hybrid", "honda-accord-hybrid"),
    ("Hyundai", r"^Elantra Hybrid$", "hev", "Hyundai Elantra Hybrid", "hyundai-elantra-hybrid"),
    ("Hyundai", r"^Tucson Hybrid$", "hev", "Hyundai Tucson Hybrid", "hyundai-tucson-hybrid"),
    ("Kia", r"^Sportage Hybrid FWD$", "hev", "Kia Sportage Hybrid", "kia-sportage-hybrid"),
    ("Kia", r"^Niro$", "hev", "Kia Niro Hybrid", "kia-niro-hybrid"),
    ("Ford", r"^Maverick HEV FWD$", "hev", "Ford Maverick Hybrid", "ford-maverick-hybrid"),
    ("Ford", r"^Escape AWD HEV$", "hev", "Ford Escape Hybrid AWD", "ford-escape-hybrid-awd"),
    ("Lexus", r"^NX 350h AWD$", "hev", "Lexus NX 350h AWD", "lexus-nx-350h-awd"),

    # ---------- Gasoline ----------
    ("Toyota", r"^Corolla$", "gas", "Toyota Corolla", "toyota-corolla"),
    ("Toyota", r"^RAV4$", "gas", "Toyota RAV4", "toyota-rav4"),
    ("Toyota", r"^Highlander AWD$", "gas", "Toyota Highlander AWD", "toyota-highlander-awd"),
    ("Honda", r"^Civic 4Dr$", "gas", "Honda Civic Sedan", "honda-civic-sedan"),
    ("Honda", r"^CR-V AWD$", "gas", "Honda CR-V AWD", "honda-cr-v-awd"),
    ("Honda", r"^Accord$", "gas", "Honda Accord", "honda-accord"),
    ("Ford", r"^Escape AWD$", "gas", "Ford Escape AWD", "ford-escape-awd"),
    ("Ford", r"^Explorer AWD$", "gas", "Ford Explorer AWD", "ford-explorer-awd"),
    ("Hyundai", r"^Tucson FWD$", "gas", "Hyundai Tucson FWD", "hyundai-tucson-fwd"),
    ("Kia", r"^Sportage AWD$", "gas", "Kia Sportage AWD", "kia-sportage-awd"),
    ("Nissan", r"^Rogue AWD$", "gas", "Nissan Rogue AWD", "nissan-rogue-awd"),
    ("Subaru", r"^Forester AWD$", "gas", "Subaru Forester AWD", "subaru-forester-awd"),
    ("Chevrolet", r"^Equinox FWD$", "gas", "Chevrolet Equinox FWD", "chevrolet-equinox-fwd"),
    ("Mazda", r"^CX-5 4WD$", "gas", "Mazda CX-5 AWD", "mazda-cx-5-awd"),
    ("Volkswagen", r"^Tiguan$", "gas", "Volkswagen Tiguan", "volkswagen-tiguan"),
    ("Jeep", r"^Grand Cherokee 2WD$", "gas", "Jeep Grand Cherokee 2WD", "jeep-grand-cherokee-2wd"),
]

# Some models are absent from the 2026 dataset — fall back to an earlier model year.
# Format: (year, make, model regex, category, display name, slug)
SPEC_LEGACY: list[tuple[int, str, str, str, str, str]] = [
    (2024, "Ford", r"^F-150 Lightning 4WD$", "ev", "Ford F-150 Lightning 4WD", "ford-f150-lightning-4wd"),
]

# ---- expansion set: more brands & trims (user request: broader coverage) ----
# Broad regexes are intentional — collect_vehicles picks the first matching trim
# and re-classifies from the EPA response, so a miss simply logs and is skipped.
SPEC_EXT: list[tuple[str, str, str, str, str]] = [
    # ---------- BEV (more brands) ----------
    ("Cadillac", r"LYRIQ", "ev", "Cadillac LYRIQ", "cadillac-lyriq"),
    ("Cadillac", r"OPTIQ", "ev", "Cadillac OPTIQ", "cadillac-optiq"),
    ("Cadillac", r"Escalade IQ", "ev", "Cadillac Escalade IQ", "cadillac-escalade-iq"),
    ("Mercedes-Benz", r"EQE 350\+", "ev", "Mercedes-Benz EQE 350+", "mercedes-eqe-350"),
    ("Mercedes-Benz", r"EQS 450", "ev", "Mercedes-Benz EQS 450+", "mercedes-eqs-450"),
    ("Mercedes-Benz", r"EQB 250\+", "ev", "Mercedes-Benz EQB 250+", "mercedes-eqb-250"),
    ("Porsche", r"Taycan", "ev", "Porsche Taycan", "porsche-taycan"),
    ("GMC", r"Hummer EV Pickup", "ev", "GMC Hummer EV Pickup", "gmc-hummer-ev-pickup"),
    ("GMC", r"Hummer EV SUV", "ev", "GMC Hummer EV SUV", "gmc-hummer-ev-suv"),
    ("GMC", r"Sierra EV", "ev", "GMC Sierra EV", "gmc-sierra-ev"),
    ("Mini", r"Cooper SE", "ev", "MINI Cooper SE", "mini-cooper-se"),
    ("Acura", r"ZDX", "ev", "Acura ZDX", "acura-zdx"),
    ("Lexus", r"RZ 450e", "ev", "Lexus RZ 450e", "lexus-rz-450e"),
    ("Lexus", r"RZ 300e", "ev", "Lexus RZ 300e", "lexus-rz-300e"),
    ("Volvo", r"EX40", "ev", "Volvo EX40", "volvo-ex40"),
    ("Volvo", r"EC40", "ev", "Volvo EC40", "volvo-ec40"),
    ("Volvo", r"EX90", "ev", "Volvo EX90", "volvo-ex90"),
    ("BMW", r"iX", "ev", "BMW iX", "bmw-ix"),
    ("BMW", r"i5", "ev", "BMW i5", "bmw-i5"),
    ("BMW", r"i7", "ev", "BMW i7", "bmw-i7"),
    ("Audi", r"Q8 e-tron", "ev", "Audi Q8 e-tron", "audi-q8-etron"),
    ("Audi", r"e-tron GT", "ev", "Audi e-tron GT", "audi-etron-gt"),
    ("Audi", r"A6 e-tron", "ev", "Audi A6 e-tron", "audi-a6-etron"),
    ("Hyundai", r"Kona Electric", "ev", "Hyundai Kona Electric", "hyundai-kona-electric"),
    ("Hyundai", r"Ioniq 6", "ev", "Hyundai Ioniq 6", "hyundai-ioniq-6"),
    ("Kia", r"EV3", "ev", "Kia EV3", "kia-ev3"),
    ("Kia", r"Soul Electric", "ev", "Kia Soul EV", "kia-soul-ev"),
    ("Genesis", r"GV70 Electrified", "ev", "Genesis GV70 Electrified", "genesis-gv70-electric"),
    ("Genesis", r"Electrified G80", "ev", "Genesis Electrified G80", "genesis-g80-electric"),
    ("Chevrolet", r"Silverado EV", "ev", "Chevrolet Silverado EV", "chevrolet-silverado-ev"),
    ("Toyota", r"bZ4X", "ev", "Toyota bZ4X", "toyota-bz4x"),
    ("VinFast", r"VF 8", "ev", "VinFast VF 8", "vinfast-vf8"),
    ("VinFast", r"VF 9", "ev", "VinFast VF 9", "vinfast-vf9"),

    # ---------- PHEV ----------
    ("Mazda", r"CX-90 PHEV", "phev", "Mazda CX-90 PHEV", "mazda-cx-90-phev"),
    ("Mazda", r"CX-70 PHEV", "phev", "Mazda CX-70 PHEV", "mazda-cx-70-phev"),
    ("BMW", r"XM", "phev", "BMW XM", "bmw-xm"),
    ("Toyota", r"RAV4 Plug-in Hybrid", "phev", "Toyota RAV4 Plug-in Hybrid", "toyota-rav4-phev"),
    ("Toyota", r"Prius Prime", "phev", "Toyota Prius Prime", "toyota-prius-prime"),
    ("Volvo", r"XC90 T8", "phev", "Volvo XC90 T8 AWD", "volvo-xc90-t8-phev"),

    # ---------- HEV ----------
    ("Honda", r"CR-V Hybrid", "hev", "Honda CR-V Hybrid", "honda-crv-hybrid"),
    ("Hyundai", r"Santa Fe Hybrid", "hev", "Hyundai Santa Fe Hybrid", "hyundai-santa-fe-hybrid"),
    ("Lexus", r"RX 350h", "hev", "Lexus RX 350h", "lexus-rx-350h"),
    ("Toyota", r"Sienna", "hev", "Toyota Sienna", "toyota-sienna-hybrid"),
    ("Kia", r"Sportage Hybrid", "hev", "Kia Sportage Hybrid", "kia-sportage-hybrid"),

    # ---------- Gasoline ----------
    ("Kia", r"Telluride", "gas", "Kia Telluride", "kia-telluride"),
    ("Subaru", r"Outback", "gas", "Subaru Outback", "subaru-outback"),
    ("Lexus", r"RX 350", "gas", "Lexus RX 350", "lexus-rx-350"),
    ("BMW", r"X3", "gas", "BMW X3", "bmw-x3"),
    ("Audi", r"Q5", "gas", "Audi Q5", "audi-q5"),
    ("Mercedes-Benz", r"GLC 300", "gas", "Mercedes-Benz GLC 300", "mercedes-glc-300"),
    ("Volvo", r"XC40", "gas", "Volvo XC40", "volvo-xc40"),
    ("Nissan", r"Sentra", "gas", "Nissan Sentra", "nissan-sentra"),
    ("Volkswagen", r"Jetta", "gas", "Volkswagen Jetta", "vw-jetta"),
    ("Honda", r"HR-V", "gas", "Honda HR-V", "honda-hrv"),
    ("Mazda", r"CX-50", "gas", "Mazda CX-50", "mazda-cx-50"),
]
SPEC = SPEC + SPEC_EXT


def classify(atv: str, fuel1: str) -> str:
    a = atv.lower()
    if "plug-in" in a:
        return "phev"
    if a == "ev" or "electricity" in fuel1.lower():
        return "ev"
    if "hybrid" in a:
        return "hev"
    return "gas"


def fetch_one(make: str, model_re: str, year: int):
    try:
        ms = models(make, year)
    except Exception as e:
        return None, f"model list failed: {e}"
    match = [m for m in ms if re.search(model_re, m)]
    if not match:
        return None, f"no model matching /{model_re}/ for {make} {year}"
    model = match[0]
    try:
        tr = trims(year, make, model)
    except Exception as e:
        return None, f"options failed: {e}"
    if not tr:
        return None, "no trims"
    vid = tr[0][1]
    try:
        xml = get(f"{BASE}/vehicle/{vid}")
    except Exception as e:
        return None, f"detail failed: {e}"

    atv = f(xml, "atvType")
    fuel1 = f(xml, "fuelType1")
    cat = classify(atv, fuel1)

    comb_e = num(xml, "combE")            # kWh/100 mi
    city_e = num(xml, "cityE")
    hwy_e = num(xml, "highwayE")
    rec = {
        "epaId": vid,
        "year": int(num(xml, "year")) or year,
        "make": f(xml, "make") or make,
        "epaModel": f(xml, "model") or model,
        "vClass": f(xml, "VClass"),
        "drive": f(xml, "drive"),
        "atvType": atv,
        "fuelType1": fuel1,
        "fuelType2": f(xml, "fuelType2"),
        "category": cat,
        # gasoline-side
        "mpgCity": num(xml, "city08"),
        "mpgHighway": num(xml, "highway08"),
        "mpgCombined": num(xml, "comb08"),
        # electricity-side
        "kwhPer100MiCombined": comb_e,
        "kwhPer100MiCity": city_e,
        "kwhPer100MiHighway": hwy_e,
        "miPerKwh": round(100.0 / comb_e, 4) if comb_e > 0 else 0.0,
        "mpgeCombined": num(xml, "combA08") if cat == "phev" else num(xml, "comb08"),
        "mpgeCity": num(xml, "cityA08") if cat == "phev" else num(xml, "city08"),
        # PHEV only
        "utilityFactor": num(xml, "combinedUF"),
        "utilityFactorCity": num(xml, "cityUF"),
        "utilityFactorHighway": num(xml, "highwayUF"),
        "evRangeMi": num(xml, "rangeA") if cat == "phev" else num(xml, "range"),
        "totalRangeMi": num(xml, "range"),
        "charge240Hours": num(xml, "charge240"),
        "sourceUrl": f"https://www.fueleconomy.gov/feg/PowerSearch.do?action=noform&path=1&year1={year}&make1={urllib.parse.quote(make)}&model1={urllib.parse.quote(model)}",
    }
    return rec, None


def main() -> int:
    force = "--force" in sys.argv
    out, errors, seen = [], [], set()

    # Incremental: keep everything already collected, only fetch what is missing.
    cached: dict[str, dict] = {}
    if OUT.exists() and not force:
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
            cached = {v["slug"]: v for v in prev.get("vehicles", [])}
        except Exception:
            cached = {}
    for slug, rec in cached.items():
        out.append(rec)
        seen.add(slug)

    jobs = [(s, 2026) for s in SPEC]
    jobs += [(s[1:], s[0]) for s in SPEC_LEGACY]

    for (make, model_re, _cat, display, slug), year in jobs:
        if slug in seen:
            continue
        rec, err = fetch_one(make, model_re, year)
        if err:
            errors.append(f"{display}: {err}")
            print(f"  MISS  {display} — {err}")
            continue
        rec["name"] = display
        rec["slug"] = slug
        out.append(rec)
        seen.add(slug)
        print(f"  OK    {rec['category']:5} {display:42} "
              f"{'mi/kWh ' + str(rec['miPerKwh']) if rec['miPerKwh'] else str(rec['mpgCombined']) + ' MPG combined'}"
              + (f"  UF={rec['utilityFactor']}" if rec["utilityFactor"] else ""))
        time.sleep(0.15)

    payload = {
        "source": "U.S. EPA / U.S. DOE — fueleconomy.gov official web services",
        "sourceUrl": "https://www.fueleconomy.gov/feg/ws/index.shtml",
        "license": "U.S. Government work — public data",
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataYear": 2026,
        "count": len(out),
        "vehicles": out,
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(out)} vehicles -> {OUT}")
    if errors:
        print(f"{len(errors)} unresolved:")
        for e in errors:
            print("  -", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
