/* ============================================================
   Engine parity test — asserts src/calc.js and gen.py agree.
   ------------------------------------------------------------
   Fixture: tests/cases.json, produced by tests/gen_cases.py
   (Python engine is the reference). Run: node tests/verify_engine.mjs
   ============================================================ */
'use strict';

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SITE = path.resolve(HERE, '..');

/* --- load calc.js into a fake window --- */
const sandbox = { window: {}, globalThis: null };
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(SITE, 'src', 'calc.js'), 'utf8'), sandbox, {
  filename: 'calc.js'
});
const FC = sandbox.window.FuelCost;
if (!FC) { console.error('FAIL  calc.js did not expose window.FuelCost'); process.exit(1); }

const cases = JSON.parse(fs.readFileSync(path.join(HERE, 'cases.json'), 'utf8'));
const TOL = 1e-9;

let checked = 0;
const failures = [];

function close(a, b) {
  if (!isFinite(a) && !isFinite(b)) return true;
  return Math.abs(a - b) <= TOL * Math.max(1, Math.abs(a), Math.abs(b));
}

for (const c of cases) {
  const label = `${c.vehicle.slug || c.vehicle.s}`;

  // (a) canonical record shape
  const gotCanonical = FC.monthlyCost(c.vehicle, c.params);
  // (b) browser payload shape — must produce the identical number
  const gotShort = FC.monthlyCost(c.short, c.params);

  for (const [shape, got] of [['canonical', gotCanonical], ['short', gotShort]]) {
    for (const key of Object.keys(c.expect)) {
      const want = c.expect[key];
      const actual = got[key] === undefined ? 0 : got[key];
      checked++;
      if (!close(want, actual)) {
        failures.push(
          `${label} [${shape}] ${key}: python=${want} js=${actual} ` +
          `(miles=${c.params.milesPerMonth}, winter=${c.params.winter}, ` +
          `home=${c.params.homeSharePct}%, hc=${c.params.homeCharging})`);
      }
    }
  }
}

/* --- unit conversions (pure maths, but worth pinning) --- */
const unitChecks = [
  ['mpgToL100km', FC.mpgToL100km(30), 235.214583 / 30],
  ['l100kmToMpg', FC.l100kmToMpg(7.84), 235.214583 / 7.84],
  ['miPerKwhToKwh100km', FC.miPerKwhToKwh100km(3.5), 100 / (3.5 * 1.609344)],
];
for (const [name, got, want] of unitChecks) {
  checked++;
  if (!close(got, want)) failures.push(`unit ${name}: got ${got} want ${want}`);
}
// money() returns a formatted string, not a number
checked++;
if (FC.money(12.3456, '$', 2) !== '$12.35') {
  failures.push(`unit money: got ${FC.money(12.3456, '$', 2)} want '$12.35'`);
}
checked++;
if (FC.money(1234.5, '£', 2) !== '£1,234.50') {
  failures.push(`unit money: got ${FC.money(1234.5, '£', 2)} want '£1,234.50'`);
}

/* --- PHEV T7: home charging off must cost the PHEV on petrol only --- */
{
  const phev = cases.map(c => c.vehicle).find(v => v.category === 'phev');
  if (phev) {
    const base = {
      milesPerMonth: 1000, homeRateUsdKwh: 0.19, publicRateUsdKwh: 0.47,
      gasUsdPerGal: 4.0, homeSharePct: 80, chargingLossPct: 10,
      citySharePct: 55, winter: false
    };
    const withHome = FC.monthlyCost(phev, Object.assign({}, base, { homeCharging: true }));
    const noHome = FC.monthlyCost(phev, Object.assign({}, base, { homeCharging: false }));
    checked += 3;
    if (!(withHome.kwh > 0)) failures.push('T7: PHEV with home charging should use electricity');
    if (noHome.kwh !== 0) failures.push(`T7: PHEV without home charging should use 0 kWh, got ${noHome.kwh}`);
    if (!noHome.note) failures.push('T7: PHEV without home charging must carry an explanatory note');
  }
}

console.log(`checked ${checked} assertions across ${cases.length} cases`);
if (failures.length) {
  console.error(`\nFAIL  ${failures.length} mismatch(es):`);
  failures.slice(0, 25).forEach(f => console.error('  - ' + f));
  if (failures.length > 25) console.error(`  … and ${failures.length - 25} more`);
  process.exit(1);
}
console.log('ENGINE PARITY OK — calc.js and gen.py agree');
