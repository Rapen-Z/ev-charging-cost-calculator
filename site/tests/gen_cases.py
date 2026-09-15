#!/usr/bin/env python3
"""Emit formula test cases from the Python engine for the JS engine to match.

The calculator exists twice on purpose: calc.js for the live page and gen.py
for build-time pre-rendering. This script produces tests/cases.json — the
shared fixture that lets tests/verify_engine.mjs prove the two agree.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent
sys.path.insert(0, str(SITE))          # gen.py lives one level up, in site/

import gen  # noqa: E402


def short(v):
    """Canonical record -> browser payload shape (see gen.browser_payload)."""
    return {
        "s": v["slug"], "n": v["name"], "m": v["make"], "c": v["category"],
        "kC": v.get("kwhPer100MiCity") or 0,
        "kH": v.get("kwhPer100MiHighway") or 0,
        "kX": v.get("kwhPer100MiCombined") or 0,
        "gC": v.get("mpgCity") or 0,
        "gH": v.get("mpgHighway") or 0,
        "gX": v.get("mpgCombined") or 0,
        "uf": v.get("utilityFactor") or 0,
    }


def main():
    vehicles, energy, regions = gen.load()
    vs = vehicles["vehicles"]

    # one of each category, plus a spread across the catalogue
    picks = []
    for cat in ("ev", "phev", "hev", "gas"):
        picks += [v for v in vs if v["category"] == cat][:3]
    rnd = random.Random(20260910)
    picks += rnd.sample(vs, min(20, len(vs)))

    # deterministic + randomised parameter sets
    params = [
        {"milesPerMonth": 1000, "homeRateUsdKwh": 0.1942, "publicRateUsdKwh": 0.47,
         "gasUsdPerGal": 4.295, "homeSharePct": 80, "chargingLossPct": 10,
         "citySharePct": 55, "winter": False, "homeCharging": True},
        {"milesPerMonth": 1500, "homeRateUsdKwh": 0.55, "publicRateUsdKwh": 0.47,
         "gasUsdPerGal": 5.10, "homeSharePct": 0, "chargingLossPct": 15,
         "citySharePct": 100, "winter": True, "homeCharging": True},
        {"milesPerMonth": 250, "homeRateUsdKwh": 0.11, "publicRateUsdKwh": 0.35,
         "gasUsdPerGal": 2.90, "homeSharePct": 100, "chargingLossPct": 0,
         "citySharePct": 0, "winter": True, "homeCharging": False},
        {"milesPerMonth": 3000, "homeRateUsdKwh": 0.2611, "publicRateUsdKwh": 0.2611,
         "gasUsdPerGal": 3.10, "homeSharePct": 55, "chargingLossPct": 12,
         "citySharePct": 30, "winter": False, "homeCharging": False},
    ]
    for _ in range(60):
        params.append({
            "milesPerMonth": rnd.choice([0, 1, 250, 750, 1000, 1375, 2000, 5000]),
            "homeRateUsdKwh": round(rnd.uniform(0.08, 0.60), 4),
            "publicRateUsdKwh": round(rnd.uniform(0.20, 0.80), 4),
            "gasUsdPerGal": round(rnd.uniform(2.0, 6.5), 3),
            "homeSharePct": rnd.randint(0, 100),
            "chargingLossPct": rnd.randint(0, 40),
            "citySharePct": rnd.randint(0, 100),
            "winter": rnd.random() < 0.5,
            "homeCharging": rnd.random() < 0.7,
        })

    cases = []
    for v in picks:
        for p in params:
            r = gen.monthly_cost(v, p)
            cases.append({
                "vehicle": v,
                "short": short(v),
                "params": p,
                "expect": {
                    "monthly": r["monthly"], "kwh": r["kwh"], "gallons": r["gallons"],
                    "electricMiles": r["electricMiles"], "gasMiles": r["gasMiles"],
                },
            })

    out = ROOT / "cases.json"
    out.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out.relative_to(SITE)} — {len(cases)} cases "
          f"({len(picks)} vehicles x {len(params)} parameter sets)")


if __name__ == "__main__":
    main()
