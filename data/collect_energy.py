#!/usr/bin/env python3
"""Collect real US energy prices from U.S. EIA public data files.

- State residential electricity price : EIA Form 861M "Monthly-States" (cents/kWh)
- Retail gasoline price (US average)  : EIA weekly "All Grades All Formulations" ($/gal)

Outputs data/energy.json with provenance. No figure is invented: anything that
cannot be read from the EIA file is reported as an error, not guessed.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = HERE / "_raw"
OUT = HERE / "energy.json"

EIA_861M = "https://www.eia.gov/electricity/data/state/xls/861m/HS861M%202010-.xlsx"
EIA_GAS = "https://www.eia.gov/dnav/pet/hist_xls/EMM_EPM0_PTE_NUS_DPGw.xls"

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

UA = {"User-Agent": "Mozilla/5.0 (fuel-cost-calc)"}

# approximate residential share used only for weighting notes, never for prices
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


def download(url: str, dest: Path, tries: int = 4) -> Path:
    if dest.exists() and dest.stat().st_size > 10000:
        return dest
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120, context=_ctx) as r:
                data = r.read()
            if len(data) < 10000 or data[:4] == b"<!DO" or data[:5] == b"<!doc":
                raise ValueError("not a spreadsheet (got HTML)")
            dest.write_bytes(data)
            return dest
        except Exception as e:
            last = e
    raise RuntimeError(f"download failed {url}: {last}")


def excel_serial_to_date(n: float) -> str:
    return (dt.date(1899, 12, 30) + dt.timedelta(days=int(n))).isoformat()


def parse_electricity(path: Path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Monthly-States"]
    rows = ws.iter_rows(values_only=True)

    header = None
    for i, r in enumerate(rows):
        if r and any(str(c).strip().upper() == "RESIDENTIAL" for c in r if c is not None):
            header = i
            break
    if header is None:
        raise RuntimeError("could not locate RESIDENTIAL header row")
    # rows: header = sector band, header+1 = Revenue/Sales/Customers/Price, header+2 = units
    price_col = None
    band = None
    wb2 = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws2 = wb2["Monthly-States"]
    all_rows = list(ws2.iter_rows(values_only=True))
    band = all_rows[header]
    sub = all_rows[header + 1]
    for idx, sec in enumerate(band):
        if sec and str(sec).strip().upper() == "RESIDENTIAL":
            for j in range(idx, min(idx + 4, len(sub))):
                if sub[j] and str(sub[j]).strip().lower() == "price":
                    price_col = j
                    break
            break
    if price_col is None:
        raise RuntimeError("could not locate residential Price column")

    latest: dict[str, dict] = {}
    for r in all_rows[header + 3:]:
        if not r or len(r) <= price_col:
            continue
        year, month = r[0], r[1]
        st = r[2]
        price = r[price_col]
        if not isinstance(st, str) or len(st) != 2:
            continue
        try:
            y, m, p = int(year), int(month), float(price)
        except (TypeError, ValueError):
            continue
        if p <= 0:
            continue
        key = (y, m)
        cur = latest.get(st)
        if cur is None or key > (cur["year"], cur["month"]):
            latest[st] = {"year": y, "month": m, "centsPerKwh": round(p, 2)}

    out = {}
    for st, v in sorted(latest.items()):
        out[st] = {
            "code": st,
            "name": STATE_NAMES.get(st, st),
            "usdPerKwh": round(v["centsPerKwh"] / 100.0, 4),
            "centsPerKwh": v["centsPerKwh"],
            "period": f"{v['year']}-{v['month']:02d}",
        }
    period = max((v["period"] for v in out.values()), default="")
    return out, period


def parse_gasoline(path: Path):
    import xlrd
    b = xlrd.open_workbook(str(path))
    sh = b.sheet_by_name("Data 1")
    last_row = None
    for r in range(sh.nrows - 1, 0, -1):
        try:
            v = float(sh.cell_value(r, 1))
        except (TypeError, ValueError):
            continue
        d = sh.cell_value(r, 0)
        try:
            d = float(d)
        except (TypeError, ValueError):
            continue
        last_row = (d, v)
        break
    if not last_row:
        raise RuntimeError("no gasoline data rows")
    serial, value = last_row
    return round(value, 3), excel_serial_to_date(serial)


def main() -> int:
    TMP.mkdir(exist_ok=True)
    print("Downloading EIA Form 861M (state electricity prices) …")
    epath = download(EIA_861M, TMP / "861m.xlsx")
    print("Downloading EIA weekly retail gasoline prices …")
    gpath = download(EIA_GAS, TMP / "gas.xls")

    states, period = parse_electricity(epath)
    gas_price, gas_date = parse_gasoline(gpath)

    payload = {
        "sources": {
            "electricity": {
                "name": "U.S. EIA — Form 861M, Electric Power Sales & Revenue (state, monthly)",
                "url": "https://www.eia.gov/electricity/data/state/",
                "file": EIA_861M,
                "sector": "Residential",
                "unit": "cents per kWh (converted to USD/kWh)",
                "period": period,
            },
            "gasoline": {
                "name": "U.S. EIA — Weekly Retail Gasoline and Diesel Prices, U.S. All Grades All Formulations",
                "url": "https://www.eia.gov/dnav/pet/pet_pri_gnd_dcus_nus_w.htm",
                "file": EIA_GAS,
                "unit": "USD per gallon",
                "weekEnding": gas_date,
            },
        },
        "fetchedAt": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "usAverageUsdPerKwh": round(sum(s["usdPerKwh"] for s in states.values()) / len(states), 4),
        "usAverageGasolineUsdPerGal": gas_price,
        "stateCount": len(states),
        "states": states,
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nStates parsed : {len(states)}  (period {period})")
    print(f"US avg        : ${payload['usAverageUsdPerKwh']}/kWh")
    print(f"Gasoline      : ${gas_price}/gal  (week ending {gas_date})")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
