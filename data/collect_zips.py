#!/usr/bin/env python3
"""Build the ZIP -> state lookup used by the calculator (PRD §8 MVP-4).

Design constraints:
  * Privacy: the ZIP never leaves the browser and never enters the URL
    (04-compliance P1-1 / decision K6). The lookup therefore runs entirely
    client-side against a small static table.
  * Size: a 42k-row table is far too heavy to inline, so we collapse it to
    3-digit ZIP prefixes. A prefix is emitted only when >=90% of its ZIPs
    agree on one state; ambiguous prefixes are dropped and the UI says so.

Source: _raw/uszips.csv — republished USPS ZIP Code data
        (https://github.com/midwire/free_zipcode_data), derived from the U.S.
        Census Bureau ZCTA/TIGER products. Validated against known ZIPs below
        before use; a ZIP is a routing area, not a polygon, so border ZIPs can
        legitimately disagree.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "_raw" / "uszips.csv"
OUT = ROOT / "zips.json"

# Hand-checked ZIPs used as a correctness gate. If any of these fails the
# build aborts rather than shipping a wrong table.
KNOWN = {
    "00501": "NY", "10001": "NY", "94105": "CA", "90001": "CA", "77002": "TX",
    "60601": "IL", "98101": "WA", "80201": "CO", "85001": "AZ", "30301": "GA",
    "28201": "NC", "33101": "FL", "02101": "MA", "19101": "PA", "48201": "MI",
    "89101": "NV", "97201": "OR", "20001": "DC", "96801": "HI", "99501": "AK",
    "55401": "MN", "63101": "MO", "46201": "IN", "37201": "TN", "21201": "MD",
    "53201": "WI", "73101": "OK", "70112": "LA", "02139": "MA", "94301": "CA",
}
MIN_SHARE = 0.90


def main(force: bool = False) -> int:
    if not RAW.exists():
        print(f"missing {RAW} — download it first", file=sys.stderr)
        return 1

    rows: dict[str, str] = {}
    with RAW.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            code = (r.get("code") or "").strip()
            state = (r.get("state") or "").strip().upper()
            if len(code) == 5 and len(state) == 2:
                rows[code] = state
    print(f"read {len(rows):,} ZIP codes")

    # --- correctness gate ------------------------------------------------
    bad = {z: (rows.get(z), s) for z, s in KNOWN.items() if rows.get(z) != s}
    if bad:
        print("FAIL  ZIP table disagrees with known values:", file=sys.stderr)
        for z, (got, want) in sorted(bad.items()):
            print(f"  {z}: got {got}, expected {want}", file=sys.stderr)
        return 1
    print(f"OK  all {len(KNOWN)} known ZIPs resolve correctly")

    # --- collapse to 3-digit prefixes ------------------------------------
    prefixes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for code, state in rows.items():
        prefixes[code[:3]][state] += 1

    table: dict[str, str] = {}
    dropped = 0
    for pfx, counts in sorted(prefixes.items()):
        total = sum(counts.values())
        state, n = max(counts.items(), key=lambda kv: kv[1])
        if n / total >= MIN_SHARE:
            table[pfx] = state
        else:
            dropped += 1

    # sanity: every state (+DC) must be reachable from the table
    reachable = set(table.values())
    missing_states = sorted({s for s in rows.values()} - reachable)
    if missing_states:
        print(f"WARN  {len(missing_states)} states unreachable by prefix: "
              f"{', '.join(missing_states)}", file=sys.stderr)

    payload = {
        "_comment": ("3-digit ZIP prefix -> state. Built from USPS ZIP Code data; a prefix is "
                     "included only when >=90% of its ZIPs share one state. Lookup runs entirely "
                     "in the browser; the ZIP is never transmitted or written to the URL."),
        "source": "USPS ZIP Code data (github.com/midwire/free_zipcode_data, Census-derived)",
        "sourceUrl": "https://github.com/midwire/free_zipcode_data",
        "builtFrom": "uszips.csv",
        "zipCount": len(rows),
        "prefixCount": len(table),
        "ambiguousPrefixesDropped": dropped,
        "minAgreementShare": MIN_SHARE,
        "validatedAgainst": len(KNOWN),
        "prefixes": table,
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
                   encoding="utf-8")
    size = OUT.stat().st_size
    print(f"wrote {OUT.name} — {len(table)} prefixes, "
          f"{dropped} ambiguous dropped, {size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main("--force" in sys.argv))
