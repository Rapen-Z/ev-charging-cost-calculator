/* ============================================================
   DOM smoke test — runs the BUILT pages in jsdom and drives the
   calculator the way a visitor would.
   ------------------------------------------------------------
   Covers PRD acceptance T1–T8 plus the motion layer (T9).
   Run: node tests/smoke_dom.mjs
   Requires: jsdom (NODE_PATH=<managed node workspace>/node_modules)
   ============================================================ */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

// jsdom lives in the managed node workspace, not next to this file; CJS
// resolution (which honours NODE_PATH) is the reliable way to reach it.
const require = createRequire(import.meta.url);
let JSDOM;
try {
  JSDOM = require('jsdom').JSDOM;
} catch (e) {
  console.error('jsdom is required. Set NODE_PATH to the workspace that has it, e.g.\n' +
    '  NODE_PATH="C:/Users/<you>/.workbuddy/binaries/node/workspace/node_modules" node tests/smoke_dom.mjs');
  process.exit(2);
}

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SITE = path.resolve(HERE, '..');
const BASE = 'https://evchargecost.test';

const failures = [];
let checked = 0;
function ok(cond, msg) {
  checked++;
  if (!cond) failures.push(msg);
}

function loadPage(route, query = '') {
  const rel = route === '/' ? 'index.html' : route.replace(/^\//, '').replace(/\/$/, '') + '/index.html';
  const file = path.join(SITE, rel);
  if (!fs.existsSync(file)) throw new Error(`missing built page: ${rel}`);
  let html = fs.readFileSync(file, 'utf8');
  const read = (f) => fs.readFileSync(path.join(SITE, 'assets', f), 'utf8');
  // NB: replacement must be a function — the inlined source contains "$'"
  // sequences that String.replace would otherwise treat as special patterns.
  html = html
    .replace(/<script[^>]*src="\/assets\/calc\.js"[^>]*><\/script>/,
             () => '<script>' + read('calc.js') + '</script>')
    .replace(/<script[^>]*src="\/assets\/fuel-data\.js"[^>]*><\/script>/,
             () => '<script>' + read('fuel-data.js') + '</script>')
    .replace(/<script[^>]*src="\/assets\/app\.js"[^>]*><\/script>/,
             () => '<script>' + read('app.js') + '</script>')
    .replace(/<script[^>]*src="\/assets\/orb\.js"[^>]*><\/script>/,
             () => '<script>' + read('orb.js') + '</script>')
    // consent.js is loaded but non-essential; keep it out of the smoke run so a
    // consent-banner quirk cannot mask a calculator failure.
    .replace(/<script[^>]*src="\/assets\/consent\.js"[^>]*><\/script>/, '');
  return new JSDOM(html, {
    url: BASE + route + query, runScripts: 'dangerously', pretendToBeVisual: true,
    // jsdom has no network stack; serve the first-party ZIP table from disk so
    // the lazy lookup is exercised for real rather than stubbed out.
    beforeParse(window) {
      // jsdom ships no 2D canvas. Returning null deterministically (instead of
      // emitting a "not implemented" error) drives orb.js down its fallback
      // branch, which is the contract we can actually assert here. The canvas
      // paint path is verified visually, not in jsdom.
      window.HTMLCanvasElement.prototype.getContext = function () { return null; };
      window.fetch = (url) => {
        const file = String(url).replace(/^https?:\/\/[^/]+/, '').replace(/^\//, '');
        const p = path.join(SITE, file);
        if (!fs.existsSync(p)) return Promise.resolve({ ok: false });
        return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(fs.readFileSync(p, 'utf8'))) });
      };
    }
  });
}

function settle(ms = 120) { return new Promise((r) => setTimeout(r, ms)); }

function numOf(s) {
  const m = String(s).replace(/[^0-9.\-]/g, '');
  return parseFloat(m);
}

function leadValue(doc) {
  const el = doc.querySelector('.calc__results .result-lead');
  return el ? numOf(el.textContent) : null;
}

function fieldByLabel(root, labelStart) {
  const labels = root.querySelectorAll('.calc__inputs label');
  for (const l of labels) {
    if (l.textContent.trim().startsWith(labelStart)) {
      const id = l.getAttribute('for');
      const input = id ? root.ownerDocument.getElementById(id) : null;
      if (input) return input;
    }
  }
  return null;
}

async function run() {
  /* ---------- T1: home page renders a number with JavaScript off AND on ---- */
  {
    const dom = await loadPage('/');
    const pre = leadValue(dom.window.document);          // server pre-render
    await settle();
    const live = leadValue(dom.window.document);         // after app.js boots
    ok(pre !== null && pre > 0, `T1 home pre-rendered result missing (got ${pre})`);
    ok(live !== null && live > 0, `T1 home live result missing (got ${live})`);
    ok(pre !== null && live !== null && Math.abs(pre - live) < 0.02,
       `T1 pre-render ${pre} != live ${live} — engines disagree on the same page`);
    const selects = dom.window.document.querySelectorAll('.calc__inputs select');
    ok(selects.length >= 3, `T1 expected vehicle A/B + state selects, got ${selects.length}`);
    dom.window.close();
  }

  /* ---------- T2: changing an input updates the result and the URL -------- */
  {
    const dom = await loadPage('/');
    await settle();
    const doc = dom.window.document;
    const before = leadValue(doc);
    const miles = fieldByLabel(doc.querySelector('.calc'), 'Miles per month');
    ok(!!miles, 'T2 miles input not found');
    if (miles) {
      miles.value = '2500';
      miles.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
      await settle(30);
      const after = leadValue(doc);
      ok(after > before, `T2 result did not rise with mileage (${before} -> ${after})`);
      ok(dom.window.location.search.includes('mi=2500'),
         `T2 URL not updated: ${dom.window.location.search}`);
    }
    dom.window.close();
  }

  /* ---------- T3: EV vs gas comparison shows both rows -------------------- */
  {
    const dom = await loadPage('/ev-vs-gas-cost-calculator/');
    await settle();
    const rows = dom.window.document.querySelectorAll('.calc__results .compare tbody tr');
    ok(rows.length === 2, `T3 expected 2 comparison rows, got ${rows.length}`);
    const evCell = rows[0] ? rows[0].children[2].textContent : '';
    const gasCell = rows[1] ? rows[1].children[2].textContent : '';
    ok(numOf(evCell) > 0 && numOf(gasCell) > 0, `T3 costs not computed (${evCell} / ${gasCell})`);
    ok(numOf(evCell) < numOf(gasCell),
       `T3 EV should beat petrol on 80% home charging (${evCell} vs ${gasCell})`);
    dom.window.close();
  }

  /* ---------- T4: PHEV home-charging switch (T7) -------------------------- */
  {
    const dom = await loadPage('/phev-charging-cost-calculator/');
    await settle();
    const doc = dom.window.document;
    const box = Array.from(doc.querySelectorAll('.calc__inputs input[type=checkbox]'))
      .find((c) => c.closest('label').textContent.includes('Home charging'));
    ok(!!box, 'T4 home-charging checkbox not found');
    if (box) {
      const withHome = leadValue(doc);
      box.checked = false;
      box.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
      await settle(30);
      const withoutHome = leadValue(doc);
      ok(withoutHome > withHome,
         `T4 PHEV should cost more without home charging (${withHome} -> ${withoutHome})`);
      const flags = doc.querySelector('.calc__results').textContent;
      ok(/Heads up|petrol only|charge-sustaining/i.test(flags),
         'T4 PHEV without home charging must explain the switch to petrol-only');
      ok(dom.window.location.search.includes('hc=0'),
         `T4 homeCharging not written to URL: ${dom.window.location.search}`);
    }
    dom.window.close();
  }

  /* ---------- T5: country page uses local currency and rate --------------- */
  {
    const dom = await loadPage('/ev-charging-cost/uk/');
    await settle();
    const doc = dom.window.document;
    const lead = doc.querySelector('.calc__results .result-lead');
    ok(!!lead && lead.textContent.includes('£'),
       `T5 UK page should price in GBP, got "${lead && lead.textContent.trim()}"`);
    const homeRate = fieldByLabel(doc.querySelector('.calc'), 'Home rate');
    ok(!!homeRate && Math.abs(parseFloat(homeRate.value) - 0.2611) < 0.0002,
       `T5 UK home rate should default to 0.2611, got ${homeRate && homeRate.value}`);
    // no US state selector on a non-US page
    const stateSel = Array.from(doc.querySelectorAll('.calc__inputs select'))
      .find((s) => s.closest('.field').textContent.startsWith('State'));
    ok(!stateSel, 'T5 UK page should not offer a US state selector');
    dom.window.close();
  }

  /* ---------- T6: shared URL restores state ------------------------------- */
  {
    const dom = await loadPage('/', '?mi=2200&hs=40&wn=1');
    await settle();
    const doc = dom.window.document;
    const miles = fieldByLabel(doc.querySelector('.calc'), 'Miles per month');
    ok(miles && miles.value === '2200', `T6 miles not restored from URL (got ${miles && miles.value})`);
    const winter = Array.from(doc.querySelectorAll('.calc__inputs input[type=checkbox]'))
      .find((c) => c.closest('label').textContent.includes('winter'));
    ok(winter && winter.checked, 'T6 winter flag not restored from URL');
    const share = fieldByLabel(doc.querySelector('.calc'), 'Charging at home');
    ok(share && share.value === '40', `T6 home share not restored (got ${share && share.value})`);
    dom.window.close();
  }

  /* ---------- T7: state page prefills that state's EIA rate --------------- */
  {
    const dom = await loadPage('/charging-cost/ca/');
    await settle();
    const doc = dom.window.document;
    const homeRate = fieldByLabel(doc.querySelector('.calc'), 'Home rate');
    const stateSel = Array.from(doc.querySelectorAll('.calc__inputs select'))
      .find((s) => s.closest('.field').textContent.startsWith('State'));
    ok(stateSel && stateSel.value === 'CA', `T7 state select should be CA, got ${stateSel && stateSel.value}`);
    // compare against the dataset, not a hardcoded number, so refreshing EIA
    // data cannot make this test lie
    const caRate = JSON.parse(fs.readFileSync(path.join(SITE, '..', 'data', 'energy.json'), 'utf8'))
      .states.CA.usdPerKwh;
    ok(homeRate && Math.abs(parseFloat(homeRate.value) - caRate) < 0.0002,
       `T7 CA rate should prefill ${caRate} from EIA, got ${homeRate && homeRate.value}`);
    dom.window.close();
  }

  /* ---------- T8: ZIP -> state lookup, and ZIP never enters the URL ------- */
  {
    const dom = await loadPage('/');
    await settle();
    const doc = dom.window.document;
    const zip = fieldByLabel(doc.querySelector('.calc'), 'ZIP code');
    ok(!!zip, 'T8 ZIP input not found');
    if (zip) {
      zip.value = '94105';
      zip.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
      await settle(120);
      const stateSel = Array.from(doc.querySelectorAll('.calc__inputs select'))
        .find((s) => s.closest('.field').textContent.startsWith('State'));
      ok(stateSel && stateSel.value === 'CA',
         `T8 ZIP 94105 should select CA, got ${stateSel && stateSel.value}`);
      ok(!/zip/i.test(dom.window.location.search),
         `T8 ZIP must never be written to the URL: ${dom.window.location.search}`);
      const hint = doc.querySelector('.calc__inputs .field__hint');
      const hints = Array.from(doc.querySelectorAll('.calc__inputs .field__hint'))
        .map((h) => h.textContent).join(' | ');
      ok(/California/.test(hints), `T8 expected a California match hint, got: ${hints}`);
    }
    dom.window.close();
  }

  /* ---------- T9: motion layer --------------------------------------------
     The beam and the thinking orb are progressive enhancement. They must
     never cost the pre-rendered result, and the orb may only appear where
     the wait is real — here, the ZIP lookup. */
  {
    const dom = await loadPage('/');
    await settle();
    const doc = dom.window.document;
    const win = dom.window;

    // 9a — beam classes reach the instrument, its buttons and the index grids
    ok(!!doc.querySelector('.calc.beam'), 'T9a calculator should carry the beam class');
    const actionBtns = doc.querySelectorAll('.calc__actions .btn-sm.beam');
    ok(actionBtns.length === 2,
       `T9a expected 2 beam action buttons, got ${actionBtns.length}`);
    ok(doc.querySelectorAll('.card-grid a.beam').length > 0,
       'T9a index links should carry the beam class');
    ok(doc.querySelectorAll('.faq details.beam').length > 0,
       'T9a FAQ panels should carry the beam class');

    // 9b — the preparing state is gone the moment the binder has mounted
    ok(!doc.querySelector('[data-boot]'),
       'T9b preparing state must be removed once inputs are mounted');

    // 9c — orbs mount; with no 2D context they must fall back, not throw
    ok(!!win.ThinkingOrb, 'T9c ThinkingOrb API should be exposed');
    const orbs = doc.querySelectorAll('.orb[data-orb]');
    ok(orbs.length >= 1, `T9c expected at least the status orb, got ${orbs.length}`);
    ok(doc.querySelectorAll('.orb--fallback').length === orbs.length,
       'T9c every orb should take the fallback path without a 2D context');
    ok(typeof win.ThinkingOrb.setState === 'function',
       'T9c ThinkingOrb.setState should be callable');

    // 9d — the motion layer must not cost the pre-rendered result, and the
    //      flash must not fire on first paint (asserted here, before any
    //      interaction can legitimately trigger a recompute)
    ok(leadValue(doc) > 0, 'T9d result must still render with the motion layer on');
    const results = doc.querySelector('[data-results]');
    ok(!!results && !results.classList.contains('is-updated'),
       'T9d first paint must not flash the result panel');

    // 9e — the ZIP lookup drives the status chip, then resolves it
    const status = doc.querySelector('.calc__head .status');
    ok(!!status, 'T9e status chip not found');
    if (status) {
      ok(status.hidden, 'T9e status chip should start hidden');
      const zip = fieldByLabel(doc.querySelector('.calc'), 'ZIP code');
      ok(!!zip, 'T9e ZIP input not found');
      if (zip) {
        zip.value = '94105';
        zip.dispatchEvent(new win.Event('input', { bubbles: true }));
        await settle(180);
        ok(!status.hidden, 'T9e status chip should be visible after a ZIP lookup');
        ok(/Matched CA/.test(status.textContent),
           `T9e expected a resolved CA match, got "${status.textContent}"`);
        ok(status.className.indexOf('status--done') !== -1,
           `T9e expected the resolved state class, got "${status.className}"`);
      }
    }

    // 9f — editing a value flashes the result panel
    const miles = fieldByLabel(doc.querySelector('.calc'), 'Miles per month');
    ok(!!miles, 'T9f miles field missing');
    if (results && miles) {
      results.classList.remove('is-updated');   // the ZIP step already fired one
      // The flash is throttled to one per 260ms so dragging a slider cannot
      // queue dozens of animations — wait out the window the ZIP step opened.
      await settle(320);
      miles.value = '1800';
      miles.dispatchEvent(new win.Event('input', { bubbles: true }));
      await settle(180);
      ok(results.classList.contains('is-updated'),
         'T9f a value change should flash the result panel');

      // and the throttle holds: a second edit inside the window must not re-fire
      results.classList.remove('is-updated');
      miles.value = '1900';
      miles.dispatchEvent(new win.Event('input', { bubbles: true }));
      await settle(120);
      ok(!results.classList.contains('is-updated'),
         'T9f the flash must stay throttled under rapid edits');
    }

    dom.window.close();
  }

  /* ---------- unit converter ---------------------------------------------- */
  {
    const dom = await loadPage('/unit-converter/mpg-l100km/');
    await settle();
    const mpg = dom.window.document.getElementById('c-mpg');
    const l = dom.window.document.getElementById('c-l100');
    ok(mpg && l && Math.abs(parseFloat(l.value) - 7.84) < 0.02,
       `converter: 30 MPG should be ~7.84 L/100km, got ${l && l.value}`);
    dom.window.close();
  }

  console.log(`checked ${checked} assertions`);
  if (failures.length) {
    console.error(`\nFAIL  ${failures.length} problem(s):`);
    failures.forEach((f) => console.error('  - ' + f));
    process.exit(1);
  }
  console.log('DOM SMOKE OK — T1..T9 all pass');
}

run().catch((e) => { console.error(e); process.exit(1); });
