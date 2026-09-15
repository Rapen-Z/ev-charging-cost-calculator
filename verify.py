#!/usr/bin/env python3
"""One command to verify the whole site: build, self-check, then both test suites.

    python verify.py

Exit code 0 means: pages built, no broken links, no banned expressions,
calc.js and gen.py produce identical numbers, and every acceptance task
T1–T9 passes in a DOM.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
PY = sys.executable


def _node_candidates() -> list[str]:
    """Prefer node on PATH, else the newest managed runtime. Discovered at run
    time so a runtime bump does not silently break verification."""
    found = [n for n in (shutil.which("node"),) if n]
    versions = Path.home() / ".workbuddy" / "binaries" / "node" / "versions"
    if versions.is_dir():
        found += [str(p / "node.exe") for p in sorted(versions.iterdir(), reverse=True)]
    return found


# The DOM suite needs jsdom, which is not installed next to the site.
NODE_CANDIDATES = _node_candidates()
JSDOM_PATH = str(Path.home() / ".workbuddy" / "binaries" / "node" / "workspace" / "node_modules")


def run(cmd, cwd, env=None, label=""):
    print(f"\n--- {label or ' '.join(cmd)} ---")
    r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    print(out.rstrip())
    return r.returncode, out


def main() -> int:
    failures = []

    # 1. build + self-check
    code, out = run([PY, "build.py"], SITE, label="build + self-check")
    if code != 0 or "SELF-CHECK PASSED" not in out:
        failures.append("build/self-check")

    # 2. engine parity (JS vs Python)
    node = next((n for n in NODE_CANDIDATES if n and Path(n).exists()), None)
    if not node:
        print("\n!! node not found — skipping JS test suites")
        failures.append("node missing")
        return 1

    code, out = run([node, "tests/verify_engine.mjs"], SITE, label="engine parity")
    if code != 0 or "ENGINE PARITY OK" not in out:
        failures.append("engine parity")

    # 3. DOM smoke (T1–T9)
    env = dict(os.environ, NODE_PATH=JSDOM_PATH)
    code, out = run([node, "tests/smoke_dom.mjs"], SITE, env=env, label="DOM smoke T1-T9")
    if code != 0 or "DOM SMOKE OK" not in out:
        failures.append("DOM smoke")

    print("\n" + "=" * 58)
    if failures:
        print("VERIFY FAILED: " + ", ".join(failures))
        return 1
    print("VERIFY PASSED — build, self-check, engine parity, T1–T9")
    return 0


if __name__ == "__main__":
    sys.exit(main())
