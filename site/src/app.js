/* ============================================================
   Calculator UI binder — one implementation for every page.
   ------------------------------------------------------------
   Contract: any element with [data-calc] is turned into a live
   calculator. Configuration comes from data-* attributes:
     data-mode   single | compare | four
     data-groups JSON array of allowed categories per selector
     data-vehicle-a / -b / -c / -d   default vehicle slugs
     data-state  default state code ("" = US average)
     data-show   comma list of optional controls

   URL parameters: v1..v4, st, mi, hr, pr, hs, gp, ls, cs, wn, hc
   NOTE: never a ZIP code — see PRD-04 P1-1 / decision K6.
   ============================================================ */
(function () {
  'use strict';

  var D = window.FUEL_DATA;
  if (!D) { return; }
  var FC = window.FuelCost;
  var VEH = {};
  D.vehicles.forEach(function (v) { VEH[v.s] = v; });

  function q(sel, root) { return (root || document).querySelector(sel); }
  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt !== undefined) e.textContent = txt;
    return e;
  }
  /* Currency symbol for the widget currently being rendered (country pages
     override it via data-symbol). Single-widget pages, so a module-level
     variable is sufficient — and it is set before the first render(). */
  var SYM = '$';
  function money(n, sym, dp) { return FC.money(n, sym || SYM, dp === undefined ? 2 : dp); }

  /* Lazy ZIP -> state table. Loaded on first use so pages stay light; it is
     a first-party static file, so no consent is involved and nothing personal
     is requested. */
  var ZIP_PROMISE = null;
  function loadZips(cb) {
    if (typeof fetch !== 'function') { cb(null); return; }
    if (!ZIP_PROMISE) {
      ZIP_PROMISE = fetch('/assets/zips.json')
        .then(function (r) { return r.ok ? r.json() : null; })
        .catch(function () { return null; });
    }
    ZIP_PROMISE.then(cb);
  }

  function vehiclesIn(cats, make) {
    return D.vehicles.filter(function (v) {
      if (cats && cats.indexOf(v.c) === -1) return false;
      if (make && v.m !== make) return false;
      return true;
    });
  }

  function defaultFor(cats, preferred) {
    if (preferred && VEH[preferred]) return preferred;
    var list = vehiclesIn(cats);
    return list.length ? list[0].s : null;
  }

  /* ---------------- URL state ---------------- */
  var PARAM = { v1: 'v1', v2: 'v2', v3: 'v3', v4: 'v4', st: 'st', mi: 'mi', hr: 'hr',
                pr: 'pr', hs: 'hs', gp: 'gp', ls: 'ls', cs: 'cs', wn: 'wn', hc: 'hc' };

  function readUrl() {
    var p = new URLSearchParams(location.search), s = {};
    Object.keys(PARAM).forEach(function (k) {
      var v = p.get(PARAM[k]);
      if (v !== null && v !== '') s[k] = v;
    });
    return s;
  }

  function writeUrl(st) {
    var p = new URLSearchParams();
    Object.keys(PARAM).forEach(function (k) {
      if (st[k] !== undefined && st[k] !== '' && st[k] !== null) p.set(PARAM[k], st[k]);
    });
    var qs = p.toString();
    var url = location.pathname + (qs ? '?' + qs : '') + location.hash;
    try { history.replaceState(null, '', url); } catch (e) { /* file:// etc. */ }
    return location.origin + url;
  }

  /* ---------------- control builders ---------------- */
  function selectField(label, opts, value, onchange) {
    var wrap = el('div', 'field field--beam');
    var lab = el('label', null, label);
    var sel = el('select');
    opts.forEach(function (o) {
      var op = el('option', null, o.label);
      op.value = o.value;
      if (o.group) op.setAttribute('data-group', o.group);
      sel.appendChild(op);
    });
    sel.value = value;
    sel.addEventListener('change', onchange);
    lab.setAttribute('for', 'f-' + label.replace(/\W+/g, ''));
    sel.id = lab.getAttribute('for');
    wrap.appendChild(lab); wrap.appendChild(sel);
    return { wrap: wrap, input: sel };
  }

  /* ---- vehicle picker: live search + custom entry ------------------------ */
  function fieldText(label, value, ph) {
    var wrap = el('div', 'field field--beam vehicle-field__cf');
    var lab = el('label', null, label);
    var inp = el('input'); inp.type = 'text'; inp.value = value || '';
    if (ph) inp.placeholder = ph;
    lab.setAttribute('for', 'cf-' + label.replace(/\W+/g, '') + Math.random().toString(36).slice(2, 5));
    inp.id = lab.getAttribute('for');
    wrap.appendChild(lab); wrap.appendChild(inp);
    return { wrap: wrap, input: inp };
  }
  function fieldSelect(label, pairs) {
    var wrap = el('div', 'field field--beam vehicle-field__cf');
    var lab = el('label', null, label);
    var sel = el('select');
    pairs.forEach(function (p) { var o = el('option', null, p[1]); o.value = p[0]; sel.appendChild(o); });
    lab.setAttribute('for', 'cf-' + label.replace(/\W+/g, '') + Math.random().toString(36).slice(2, 5));
    sel.id = lab.getAttribute('for');
    wrap.appendChild(lab); wrap.appendChild(sel);
    return { wrap: wrap, input: sel };
  }

  /* Build a synthetic vehicle record from the custom-entry form. Returns null
     when the name is blank so render() simply shows nothing until typed. */
  function buildCustomVehicle(name, type, eff, er, uf) {
    if (!name || !name.trim()) return null;
    var v = { s: '__custom', n: name.trim(), m: 'Custom', c: type, vc: 'Custom',
              mpk: 0, kC: 0, kH: 0, kX: 0, gC: 0, gH: 0, gX: 0, uf: 0, er: 0 };
    var e = parseFloat(eff);
    if (type === 'ev' || type === 'phev') {
      v.mpk = isFinite(e) ? e : 0;
      v.kC = v.kH = v.kX = v.mpk > 0 ? 100 / v.mpk : 0;
    } else {
      v.gC = v.gH = v.gX = isFinite(e) ? e : 0;
    }
    if (type === 'phev') {
      v.uf = Math.min(1, Math.max(0, parseFloat(uf) || 0));
      v.er = parseFloat(er) || 0;
    }
    return v;
  }

  function vehicleField(label, opts, value, onchange, list) {
    var wrap = el('div', 'field field--beam vehicle-field');
    var lab = el('label', null, label);

    var search = null;
    if (list && list.length > 6) {
      search = el('input');
      search.type = 'text';
      search.placeholder = 'Search ' + list.length + ' models…';
      search.setAttribute('autocomplete', 'off');
      search.className = 'vehicle-field__search';
      search.setAttribute('aria-label', label + ' search');
    }

    var sel = el('select');
    opts.forEach(function (o) { var op = el('option', null, o.label); op.value = o.value; sel.appendChild(op); });
    var customOp = el('option', null, '＋ Add your own vehicle…'); customOp.value = '__custom';
    sel.appendChild(customOp);
    sel.value = value;

    // custom-entry form (revealed when the user picks the trailing option)
    var custom = el('div', 'vehicle-field__custom'); custom.hidden = true;
    var nameF = fieldText('Vehicle name', '');
    var typeF = fieldSelect('Powertrain',
      [['ev', 'Electric (BEV)'], ['phev', 'Plug-in hybrid'], ['hev', 'Hybrid'], ['gas', 'Petrol']]);
    var effF = fieldText('Efficiency (mi/kWh)', '');
    var erF = fieldText('Electric range (mi)', '');
    var ufF = fieldText('Utility factor (0–1)', '');
    function effLabel() {
      var t = typeF.input.value;
      effF.wrap.querySelector('label').textContent =
        (t === 'ev' || t === 'phev') ? 'Efficiency (mi/kWh)' : 'Fuel economy (MPG combined)';
      erF.wrap.hidden = (t !== 'phev');
      ufF.wrap.hidden = (t !== 'phev');
    }
    function sync() {
      VEH['__custom'] = buildCustomVehicle(nameF.input.value, typeF.input.value,
        effF.input.value, erF.input.value, ufF.input.value);
      onchange();
    }
    [nameF, typeF, effF, erF, ufF].forEach(function (f) {
      f.input.addEventListener('input', sync);
      f.input.addEventListener('change', sync);
    });
    typeF.input.addEventListener('change', effLabel);
    effLabel();
    custom.appendChild(nameF.wrap); custom.appendChild(typeF.wrap);
    custom.appendChild(effF.wrap); custom.appendChild(erF.wrap); custom.appendChild(ufF.wrap);

    function applyFilter(q) {
      if (!search) return;
      q = q.trim().toLowerCase();
      Array.prototype.forEach.call(sel.options, function (op) {
        if (op.value === '__custom') { op.style.display = ''; return; }
        var v = VEH[op.value]; if (!v) { op.style.display = ''; return; }
        var hay = ((v.n || '') + ' ' + (v.m || '') + ' ' + (v.vc || '')).toLowerCase();
        op.style.display = (!q || hay.indexOf(q) !== -1) ? '' : 'none';
      });
    }
    if (search) search.addEventListener('input', function () { applyFilter(search.value); });
    sel.addEventListener('change', function () {
      if (sel.value === '__custom') { custom.hidden = false; sync(); }
      else { custom.hidden = true; delete VEH['__custom']; }
      onchange();
    });

    lab.setAttribute('for', 'f-' + label.replace(/\W+/g, ''));
    sel.id = lab.getAttribute('for');
    wrap.appendChild(lab);
    if (search) wrap.appendChild(search);
    wrap.appendChild(sel);
    wrap.appendChild(custom);
    return { wrap: wrap, input: sel };
  }

  /* Side panel that turns the empty right half of the instrument into
     on-topic reference content. Static + enhancement-only. */
  function asidePanel() {
    var a = el('div', 'calc__aside');
    a.appendChild(el('h3', null, 'Reading the numbers'));
    var dl = el('dl', 'aside-legend');
    [['mi/kWh', 'miles per kWh of electricity — a higher number is more efficient.'],
     ['MPGe', "the EPA's petrol-equivalent efficiency rating for electric cars."],
     ['kWh / mo', 'the estimated electricity a vehicle uses each month.']].forEach(function (r) {
      dl.appendChild(el('dt', null, r[0])); dl.appendChild(el('dd', null, r[1]));
    });
    a.appendChild(dl);
    var tip = el('div', 'aside-tip');
    tip.innerHTML = '<strong>Tip.</strong> Home charging typically costs about a third of public ' +
      'DC fast charging. Set your home/public split to match how you actually charge.';
    a.appendChild(tip);
    return a;
  }

  function numberField(label, value, step, onchange, hint) {
    var wrap = el('div', 'field field--beam');
    var lab = el('label', null, label);
    var inp = el('input');
    inp.type = 'number'; inp.value = value; inp.step = step; inp.min = '0';
    inp.addEventListener('input', onchange);
    lab.setAttribute('for', 'f-' + label.replace(/\W+/g, '') + '-' + Math.random().toString(36).slice(2, 6));
    inp.id = lab.getAttribute('for');
    wrap.appendChild(lab); wrap.appendChild(inp);
    if (hint) wrap.appendChild(el('p', 'field__hint', hint));
    return { wrap: wrap, input: inp };
  }

  function rangeField(label, value, onchange) {
    var wrap = el('div', 'field field--beam');
    var lab = el('label', null, label + ' ');
    var val = el('span', 'range-val', value + '%');
    lab.appendChild(val);
    var inp = el('input');
    inp.type = 'range'; inp.min = '0'; inp.max = '100'; inp.step = '1'; inp.value = value;
    inp.addEventListener('input', function () { val.textContent = inp.value + '%'; onchange(); });
    lab.setAttribute('for', 'f-' + label.replace(/\W+/g, '') + '-' + Math.random().toString(36).slice(2, 6));
    inp.id = lab.getAttribute('for');
    wrap.appendChild(lab); wrap.appendChild(inp);
    return { wrap: wrap, input: inp };
  }

  function checkField(label, checked, onchange, hint) {
    var wrap = el('label', 'check');
    var inp = el('input');
    inp.type = 'checkbox'; inp.checked = !!checked;
    inp.addEventListener('change', onchange);
    wrap.appendChild(inp);
    var box = el('span');
    box.appendChild(el('span', null, label));
    if (hint) box.appendChild(el('span', 'field__hint', ' ' + hint));
    wrap.appendChild(box);
    return { wrap: wrap, input: inp };
  }

  /* ---------------- result rendering ---------------- */
  function resultSingle(v, r, p, url) {
    var mpk = v.c === 'ev' || v.c === 'phev' ? FC.miPerKwh(v, p.citySharePct, p.winter) : 0;
    var perMile = r.monthly / (p.milesPerMonth || 1);
    var out = [];
    out.push('<p class="result-lead">' + money(r.monthly) + '<small> / month</small></p>');
    out.push('<p class="result-sub">' + esc(v.n) + ' · ' + esc(catLabel(v.c)) +
             ' · ' + Math.round(p.milesPerMonth).toLocaleString() + ' miles/month</p>');
    out.push('<dl class="result-grid">');
    out.push(cell('Per mile', money(perMile, null, 3)));
    out.push(cell('Per year', money(r.monthly * 12)));
    if (mpk > 0) out.push(cell('Efficiency', mpk.toFixed(2) + ' mi/kWh'));
    if (v.c !== 'gas') out.push(cell('Energy used', Math.round(r.kwh).toLocaleString() + ' kWh/mo'));
    if (r.gallons > 0) out.push(cell('Fuel used', r.gallons.toFixed(1) + ' gal/mo'));
    out.push('</dl>');
    if (v.c === 'phev') {
      out.push('<div class="flag"><strong>Plug-in hybrid split.</strong> ' +
        Math.round(r.electricMiles).toLocaleString() + ' miles on electricity (' +
        Math.round((v.uf || 0) * (p.homeCharging === false ? 0 : 1) * 100) + '%), ' +
        Math.round(r.gasMiles).toLocaleString() + ' miles on petrol.</div>');
    }
    if (r.note) out.push('<div class="flag"><strong>Heads up.</strong> ' + esc(r.note) + '</div>');
    out.push(formulaBlock(v, p));
    out.push(actionsBlock(url, v, r, p));
    return out.join('');
  }

  function costChart(list) {
    if (!list || list.length < 2) return '';
    var max_m = list.reduce(function (m, it) { return Math.max(m, it.r.monthly); }, 0) || 1;
    var best = list.reduce(function (a, b) { return (a && a.r.monthly <= b.r.monthly) ? a : b; }, null);
    var bars = list.map(function (it) {
      var pct = Math.max(12, Math.min(100, Math.round((it.r.monthly / max_m) * 100)));
      var isWin = it === best;
      var badge = isWin ? '<span class="cost-bar__badge">Lowest</span>' : '';
      return '<div class="cost-bar' + (isWin ? ' is-winner' : '') + '">' +
        '<div class="cost-bar__header">' +
        '<span class="cost-bar__name">' + esc(it.v.n) + ' ' + badge + '</span>' +
        '<span class="cost-bar__val">' + money(it.r.monthly) + '/mo</span>' +
        '</div>' +
        '<div class="cost-bar__track">' +
        '<div class="cost-bar__fill" style="width:' + pct + '%"></div>' +
        '</div>' +
        '</div>';
    });
    return '<div class="cost-chart"><div class="cost-chart__title">Monthly Cost Comparison</div>' + bars.join('') + '</div>';
  }

  function resultCompare(list, p, url) {
    /* list: [{v, r}] */
    var out = [];
    var best = list.reduce(function (a, b) { return (a && a.r.monthly <= b.r.monthly) ? a : b; }, null);
    out.push('<p class="result-lead">' + money(best.r.monthly) + '<small> / month</small></p>');
    out.push('<p class="result-sub">Cheapest option: ' + esc(best.v.n) + '</p>');
    out.push(costChart(list));
    out.push('<div class="compare"><table><thead><tr><th>Vehicle</th><th>Type</th>' +
             '<th>Month</th><th>Year</th><th>Per mile</th></tr></thead><tbody>');
    list.forEach(function (it) {
      var isBest = it === best;
      out.push('<tr><td>' + esc(it.v.n) + '</td><td>' + esc(catLabel(it.v.c)) + '</td>' +
        '<td' + (isBest ? ' class="win"' : '') + '>' + money(it.r.monthly) + '</td>' +
        '<td>' + money(it.r.monthly * 12) + '</td>' +
        '<td>' + money(it.r.monthly / (p.milesPerMonth || 1), null, 3) + '</td></tr>');
    });
    out.push('</tbody></table></div>');

    if (list.length >= 2) {
      var a = list[0], b = list[1];
      var diff = b.r.monthly - a.r.monthly;
      if (Math.abs(diff) > 0.5) {
        var cheaper = diff > 0 ? a.v.n : b.v.n;
        var dearer = diff > 0 ? b.v.n : a.v.n;
        out.push('<div class="savings"><strong>' + esc(cheaper) + '</strong> costs about ' +
          money(Math.abs(diff)) + '/month (' + money(Math.abs(diff) * 12) + '/year) less to run than ' +
          esc(dearer) + ' at ' + Math.round(p.milesPerMonth).toLocaleString() + ' miles/month.</div>');
      } else {
        out.push('<div class="savings">These two are within about $0.50/month of each other at these inputs.</div>');
      }
    }
    list.forEach(function (it) { if (it.r.note) out.push('<div class="flag"><strong>Heads up.</strong> ' + esc(it.r.note) + '</div>'); });
    out.push(formulaBlock(null, p));
    out.push(actionsBlock(url, best.v, best.r, p));
    return out.join('');
  }

  function cell(dt, dd) { return '<div class="result-cell"><dt>' + dt + '</dt><dd>' + dd + '</dd></div>'; }

  function catLabel(c) {
    return { ev: 'Battery electric', phev: 'Plug-in hybrid', hev: 'Hybrid', gas: 'Petrol' }[c] || c;
  }

  function formulaBlock(v, p) {
    var txt = 'monthly cost = miles ÷ efficiency × price × (1 + charging loss)\n' +
      '  miles            = ' + Math.round(p.milesPerMonth).toLocaleString() + '\n' +
      '  home rate        = ' + SYM + ' ' + (p.homeRateUsdKwh || 0).toFixed(4) + '/kWh  (' + Math.round(p.homeSharePct) + '% of charging)\n' +
      '  public DC rate   = ' + SYM + ' ' + (p.publicRateUsdKwh || 0).toFixed(4) + '/kWh  (' + (100 - Math.round(p.homeSharePct)) + '%)\n' +
      '  charging loss    = ' + Math.round(p.chargingLossPct) + '%' +
      (p.winter ? '\n  winter correction = ON (efficiency × 0.85)' : '');
    return '<div class="formula"><strong>How this is worked out</strong><code>' + esc(txt) + '</code></div>';
  }

  function actionsBlock(url, v, r, p) {
    return '<div class="calc__actions">' +
      '<button type="button" class="btn-sm beam" data-copy-link>Copy link to this result</button>' +
      '<button type="button" class="btn-sm beam" data-copy-summary>Copy summary</button>' +
      '<button type="button" class="btn-sm btn--reddit" data-copy-reddit>Copy for Reddit</button>' +
      '</div>';
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function flash(btn, msg) {
    var old = btn.textContent;
    btn.textContent = msg;
    setTimeout(function () { btn.textContent = old; }, 1600);
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); resolve(); } catch (e) { reject(e); }
      document.body.removeChild(ta);
    });
  }

  /* ---------------- per-widget wiring ---------------- */
  function initCalc(root) {
    var mode = root.getAttribute('data-mode') || 'single';
    var groups;
    try { groups = JSON.parse(root.getAttribute('data-groups') || '[]'); } catch (e) { groups = []; }
    var show = (root.getAttribute('data-show') || '').split(',').filter(Boolean);
    var url0 = readUrl();

    // Per-page defaults. data-rate lets a page pin the starting electricity
    // price (country pages use their local residential rate); data-home-share
    // pins the home/public split (country pages are home-only because we hold
    // no verified local DC fast-charging price).
    SYM = root.getAttribute('data-symbol') || '$';
    var attrNum = function (name, fallback) {
      var raw = root.getAttribute(name);
      if (raw === null || raw === '') return fallback;
      var n = parseFloat(raw);
      return isFinite(n) ? n : fallback;
    };
    var defRate = attrNum('data-rate', null);
    var defShare = attrNum('data-home-share', D.defaults.homeSharePct);
    var defPublic = attrNum('data-public-rate', D.dcfc);

    var state = {
      st: url0.st !== undefined ? url0.st : (root.getAttribute('data-state') || ''),
      mi: url0.mi !== undefined ? url0.mi : D.defaults.milesPerMonth,
      hr: url0.hr !== undefined ? url0.hr : defRate,
      pr: url0.pr !== undefined ? url0.pr : defPublic,
      hs: url0.hs !== undefined ? url0.hs : defShare,
      gp: url0.gp !== undefined ? url0.gp : D.usGas,
      ls: url0.ls !== undefined ? url0.ls : D.defaults.chargingLossPct,
      cs: url0.cs !== undefined ? url0.cs : D.defaults.citySharePct,
      wn: url0.wn === '1' || url0.wn === 'true',
      hc: !(url0.hc === '0' || url0.hc === 'false')
    };

    var nSel = mode === 'four' ? 4 : (mode === 'compare' ? 2 : 1);
    var vehSlugs = [];
    for (var i = 0; i < nSel; i++) {
      var key = 'v' + (i + 1);
      var attr = root.getAttribute('data-vehicle-' + 'abcd'[i]);
      vehSlugs.push(url0[key] || defaultFor(groups[i] || null, attr));
    }

    var inputsHost = q('[data-inputs]', root);
    var resultsHost = q('[data-results]', root);
    if (!inputsHost || !resultsHost) return;

    /* ---- status line, driven by the thinking orb ---------------------
       Mounted only for genuinely asynchronous work (the ZIP lookup is a
       real fetch). Synchronous actions such as copying get plain text
       feedback instead — a thinking indicator on an instant operation
       would be theatre, not feedback. */
    var statusEl = q('[data-status]', root);
    var statusText = statusEl ? q('.status__text', statusEl) : null;
    var statusOrb = statusEl ? q('.orb', statusEl) : null;
    var statusTimer = null;
    var STATUS_CLASS = { busy: 'status--busy', done: 'status--done', fail: 'status--fail' };

    function setStatus(state, text, kind) {
      if (!statusEl) return;
      if (statusTimer) { clearTimeout(statusTimer); statusTimer = null; }
      if (!state) { statusEl.hidden = true; return; }
      statusEl.hidden = false;
      statusEl.className = 'status' + (kind && STATUS_CLASS[kind] ? ' ' + STATUS_CLASS[kind] : '');
      if (statusText) statusText.textContent = text || '';
      if (statusOrb && window.ThinkingOrb) window.ThinkingOrb.setState(statusOrb, state);
    }
    function flashStatus(state, text, kind, ms) {
      setStatus(state, text, kind);
      statusTimer = setTimeout(function () { setStatus(null); }, ms || 2400);
    }

    /* The preparing state has done its job the moment the real inputs can be
       built. It is removed further down, once the fields exist. */
    var bootEl = q('[data-boot]', inputsHost);

    /* ---- build inputs ---- */
    var stateOpts = [{ value: '', label: 'US average (' + D.usAvgKwh.toFixed(4) + '/kWh)' }];
    Object.keys(D.states).sort(function (a, b) {
      return D.states[a].n.localeCompare(D.states[b].n);
    }).forEach(function (k) {
      stateOpts.push({ value: k, label: D.states[k].n + ' ($' + D.states[k].r.toFixed(4) + '/kWh)' });
    });

    var selRefs = [];
    var makeFilter = root.getAttribute('data-make') || '';
    for (var s = 0; s < nSel; s++) {
      var cats = groups[s] || null;
      // per-selector make override: data-make-a / -b / -c / -d
      var mk = root.getAttribute('data-make-' + 'abcd'[s]) || makeFilter;
      var list = vehiclesIn(cats, mk);
      var opts = list.map(function (v) { return { value: v.s, label: v.n }; });
      var label = nSel > 1 ? (['Vehicle A', 'Vehicle B', 'Vehicle C', 'Vehicle D'][s]) : 'Vehicle';
      var f = vehicleField(label, opts, vehSlugs[s], function () { syncFromInputs(); }, list);
      inputsHost.appendChild(f.wrap);
      selRefs.push(f.input);
    }

    // Reference panel fills the previously-empty right half of the instrument.
    var asideEl = asidePanel();
    var bodyEl = q('.calc__body', root);
    if (bodyEl) bodyEl.appendChild(asideEl);

    // State selector only appears on pages that price electricity (fuel-only
    // pages and non-US country pages have no US state rate to apply).
    var stF = null;
    if (show.indexOf('state') !== -1) {
      stF = selectField('State / region', stateOpts, state.st, function () {
        // choosing a state resets the home rate to that state's EIA average
        hrF.input.value = stateRate().toFixed(4);
        syncFromInputs();
      });
      inputsHost.appendChild(stF.wrap);
    }

    function stateRate() {
      return (state.st && D.states[state.st]) ? D.states[state.st].r : D.usAvgKwh;
    }

    var miF = numberField('Miles per month', state.mi, '50', function () { syncFromInputs(); });
    inputsHost.appendChild(miF.wrap);

    // Optional ZIP -> state lookup (PRD §8 MVP-4). The ZIP is used only to
    // pick a state in this browser: it is never transmitted, never stored and
    // deliberately never written into the shareable URL (04-compliance P1-1).
    if (show.indexOf('zip') !== -1) {
      var zipF = numberField('ZIP code (optional)', '', '1', function () {
        var digits = (zipF.input.value || '').replace(/\D/g, '').slice(0, 5);
        zipHint.textContent = 'Stays in your browser — never saved, never in the link.';
        if (digits.length < 3) { setStatus(null); return; }
        setStatus('working', 'Looking up ZIP ' + digits + '…', 'busy');
        loadZips(function (z) {
          if (!z || !z.prefixes) {
            zipHint.textContent = 'ZIP lookup unavailable — pick your state below.';
            flashStatus('fail', 'ZIP lookup unavailable', 'fail', 2800);
            return;
          }
          var st2 = z.prefixes[digits.slice(0, 3)];
          if (!st2) {
            zipHint.textContent = 'No state match for that ZIP — pick your state below.';
            flashStatus('fail', 'No match for ' + digits, 'fail', 2600);
            return;
          }
          state.st = st2;
          if (stF) stF.input.value = st2;
          if (hrF) hrF.input.value = stateRate().toFixed(4);
          syncFromInputs();
          var name = (D.states[st2] && D.states[st2].n) || st2;
          zipHint.textContent = 'Matched ' + st2 + ' (' + name + ') — rate updated.';
          flashStatus('done', 'Matched ' + st2 + ' — rate updated', 'done', 2400);
        });
      }, 'Stays in your browser — never saved, never in the link.');
      var zipHint = zipF.wrap.querySelector('.field__hint');
      zipF.input.type = 'text';
      zipF.input.inputMode = 'numeric';
      zipF.input.setAttribute('pattern', '[0-9]*');
      zipF.input.setAttribute('autocomplete', 'off');
      zipF.input.removeAttribute('step');
      zipF.input.removeAttribute('min');
      inputsHost.insertBefore(zipF.wrap, miF.wrap.nextSibling);
    }

    var hrF = numberField('Home rate (' + SYM + '/kWh)',
      (state.hr !== null ? state.hr : stateRate()).toFixed(4), '0.001',
      function () { syncFromInputs(); }, 'Your utility rate — check your bill.');
    inputsHost.appendChild(hrF.wrap);

    if (show.indexOf('publicRate') !== -1) {
      var prF = numberField('Public DC fast rate (' + SYM + '/kWh)', Number(state.pr).toFixed(4), '0.001',
        function () { syncFromInputs(); });
      inputsHost.appendChild(prF.wrap);
    }
    if (show.indexOf('homeShare') !== -1) {
      var hsF = rangeField('Charging at home', state.hs, function () { syncFromInputs(); });
      inputsHost.appendChild(hsF.wrap);
    }
    if (show.indexOf('gasPrice') !== -1) {
      var gpF = numberField('Petrol price (' + SYM + '/gal)', Number(state.gp).toFixed(3), '0.001',
        function () { syncFromInputs(); });
      inputsHost.appendChild(gpF.wrap);
    }
    if (show.indexOf('loss') !== -1) {
      var lsF = numberField('Charging loss (%)', state.ls, '1', function () { syncFromInputs(); });
      inputsHost.appendChild(lsF.wrap);
    }
    if (show.indexOf('city') !== -1) {
      var csF = rangeField('City driving', state.cs, function () { syncFromInputs(); });
      inputsHost.appendChild(csF.wrap);
    }
    if (show.indexOf('winter') !== -1) {
      var wnF = checkField('Apply winter correction', state.wn, function () { syncFromInputs(); },
        'Efficiency ×0.85 (PHEV utility factor ×0.85).');
      inputsHost.appendChild(wnF.wrap);
    }
    if (show.indexOf('homeCharging') !== -1) {
      var hcF = checkField('Home charging available', state.hc, function () { syncFromInputs(); },
        'Turn off if you cannot plug in at home.');
      inputsHost.appendChild(hcF.wrap);
    }

    // Inputs are built — drop the preparing state now that it is true.
    if (bootEl && bootEl.parentNode) bootEl.parentNode.removeChild(bootEl);

    function syncFromInputs() {
      if (stF) state.st = stF.input.value;
      state.mi = miF.input.value;
      state.hr = hrF.input.value;
      if (typeof prF !== 'undefined') state.pr = prF.input.value;
      if (typeof hsF !== 'undefined') state.hs = hsF.input.value;
      if (typeof gpF !== 'undefined') state.gp = gpF.input.value;
      if (typeof lsF !== 'undefined') state.ls = lsF.input.value;
      if (typeof csF !== 'undefined') state.cs = csF.input.value;
      if (typeof wnF !== 'undefined') state.wn = wnF.input.checked;
      if (typeof hcF !== 'undefined') state.hc = hcF.input.checked;
      render();
    }

    var lastUrl = '';
    var booted = false;

    /* Recompute feedback: one light sweep across the top rule of the result
       panel. It fires on state change (the visitor edited a value), never on
       first paint, and is throttled so dragging a slider cannot queue dozens
       of animations. `animationend` clears the class so nothing accumulates. */
    var flashAt = 0;
    resultsHost.addEventListener('animationend', function (e) {
      if (e.target === resultsHost && e.animationName === 'beam-flash') {
        resultsHost.classList.remove('is-updated');
      }
    });
    function flashResults() {
      var now = Date.now();
      if (now - flashAt < 260) return;
      flashAt = now;
      resultsHost.classList.remove('is-updated');
      requestAnimationFrame(function () { resultsHost.classList.add('is-updated'); });
    }

    function render() {
      var p = {
        milesPerMonth: FC.num(state.mi, 1000),
        homeRateUsdKwh: FC.num(state.hr, stateRate()),
        publicRateUsdKwh: FC.num(state.pr, D.dcfc),
        homeSharePct: FC.num(state.hs, 80),
        gasUsdPerGal: FC.num(state.gp, D.usGas),
        chargingLossPct: FC.num(state.ls, 10),
        citySharePct: FC.num(state.cs, 55),
        winter: state.wn,
        homeCharging: state.hc
      };

      var picks = selRefs.map(function (sel) { return VEH[sel.value]; }).filter(Boolean);
      if (!picks.length) return;

      var st = {
        v1: selRefs[0] ? selRefs[0].value : '', v2: selRefs[1] ? selRefs[1].value : '',
        v3: selRefs[2] ? selRefs[2].value : '', v4: selRefs[3] ? selRefs[3].value : '',
        st: state.st, mi: p.milesPerMonth, hr: p.homeRateUsdKwh.toFixed(4),
        pr: p.publicRateUsdKwh.toFixed(4), hs: p.homeSharePct, gp: p.gasUsdPerGal.toFixed(3),
        ls: p.chargingLossPct, cs: p.citySharePct,
        wn: state.wn ? '1' : '0', hc: state.hc ? '1' : '0'
      };
      lastUrl = writeUrl(st);

      if (mode === 'single') {
        var v = picks[0];
        resultsHost.innerHTML = resultSingle(v, FC.monthlyCost(v, p), p, lastUrl);
      } else {
        var list = picks.map(function (v) { return { v: v, r: FC.monthlyCost(v, p) }; });
        resultsHost.innerHTML = resultCompare(list, p, lastUrl);
      }

      if (booted) { flashResults(); } else { booted = true; }
      if (window.ThinkingOrb) window.ThinkingOrb.scan(resultsHost);

      var cl = q('[data-copy-link]', resultsHost);
      var cs2 = q('[data-copy-summary]', resultsHost);
      var cr = q('[data-copy-reddit]', resultsHost);
      if (cl) cl.addEventListener('click', function () { copyText(lastUrl).then(function () { flash(cl, 'Link copied'); }); });
      if (cs2) cs2.addEventListener('click', function () {
        var v0 = picks[0], r0 = FC.monthlyCost(v0, p);
        var txt = v0.n + ': about ' + money(r0.monthly) + '/month (' +
          money(r0.monthly / (p.milesPerMonth || 1), null, 3) + '/mile) at ' +
          Math.round(p.milesPerMonth).toLocaleString() + ' miles/month, ' +
          p.homeRateUsdKwh.toFixed(4) + '/kWh. Estimate — ' + lastUrl;
        copyText(txt).then(function () { flash(cs2, 'Summary copied'); });
      });
      if (cr) cr.addEventListener('click', function () {
        var lines = [];
        lines.push('### ' + (mode === 'single' ? picks[0].n + ' Cost Estimate' : 'EV Charging & Fuel Cost Comparison'));
        lines.push('*Assumptions: ' + Math.round(p.milesPerMonth).toLocaleString() + ' mi/mo | $' + p.homeRateUsdKwh.toFixed(4) + '/kWh electricity | $' + p.gasUsdPerGal.toFixed(2) + '/gal gas*');
        lines.push('');
        if (mode === 'single') {
          var v0 = picks[0], r0 = FC.monthlyCost(v0, p);
          lines.push('| Metric | Value |');
          lines.push('| :--- | :--- |');
          lines.push('| **Vehicle** | ' + v0.n + ' (' + catLabel(v0.c) + ') |');
          lines.push('| **Monthly Cost** | **' + money(r0.monthly) + '** |');
          lines.push('| **Annual Cost** | ' + money(r0.monthly * 12) + ' |');
          lines.push('| **Per Mile** | ' + money(r0.monthly / (p.milesPerMonth || 1), null, 3) + ' |');
          if (v0.c !== 'gas') lines.push('| **Energy Used** | ' + Math.round(r0.kwh).toLocaleString() + ' kWh/mo |');
          if (r0.gallons > 0) lines.push('| **Fuel Used** | ' + r0.gallons.toFixed(1) + ' gal/mo |');
        } else {
          lines.push('| Vehicle | Type | Monthly | Annual | Per Mile |');
          lines.push('| :--- | :--- | :--- | :--- | :--- |');
          var best = picks.reduce(function (a, b) {
            var ra = FC.monthlyCost(a, p), rb = FC.monthlyCost(b, p);
            return (a && ra.monthly <= rb.monthly) ? a : b;
          }, null);
          picks.forEach(function (v) {
            var r = FC.monthlyCost(v, p);
            var isBest = v === best;
            var name = isBest ? '**' + v.n + ' 🏆**' : v.n;
            var m = isBest ? '**' + money(r.monthly) + '**' : money(r.monthly);
            var a = isBest ? '**' + money(r.monthly * 12) + '**' : money(r.monthly * 12);
            var pm = money(r.monthly / (p.milesPerMonth || 1), null, 3);
            lines.push('| ' + name + ' | ' + catLabel(v.c) + ' | ' + m + ' | ' + a + ' | ' + pm + ' |');
          });
        }
        lines.push('');
        lines.push('*Generated via [EV Charging Cost Calculator](' + lastUrl + ')*');
        copyText(lines.join('\n')).then(function () { flash(cr, 'Reddit table copied'); });
      });
    }

    render();
  }

  function boot() {
    var nodes = document.querySelectorAll('[data-calc]');
    for (var i = 0; i < nodes.length; i++) initCalc(nodes[i]);

    // unit converter
    var conv = document.getElementById('converter');
    if (conv) initConverter(conv);
  }

  function initConverter(root) {
    var mpgI = q('#c-mpg', root), lI = q('#c-l100', root);
    if (!mpgI || !lI) return;
    function fromMpg() {
      var v = parseFloat(mpgI.value);
      lI.value = v > 0 ? (235.214583 / v).toFixed(2) : '';
    }
    function fromL() {
      var v = parseFloat(lI.value);
      mpgI.value = v > 0 ? (235.214583 / v).toFixed(2) : '';
    }
    mpgI.addEventListener('input', fromMpg);
    lI.addEventListener('input', fromL);
    mpgI.value = 30; fromMpg();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else { boot(); }
})();
