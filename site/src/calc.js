/* ============================================================
   Fuel-cost engine — EV / PHEV / Hybrid / Gas
   ------------------------------------------------------------
   Formula source of truth: PRD v1 §8 MVP-1 and §13 "新增关键因子".
   Mirrored in gen.py (Python) for build-time pre-rendering;
   tests/verify_engine.mjs asserts both implementations agree.

   monthlyCost = miles / efficiency  x  price  x  (1 + loss)
   ------------------------------------------------------------
   No value is hard-coded here: every number comes from the
   inlined window.FUEL_DATA (EPA + EIA) or from the user's own inputs.
   ============================================================ */
(function (global) {
  'use strict';

  var DEFAULTS = {
    milesPerMonth: 1000,
    homeSharePct: 80,      // % of charging done at home
    chargingLossPct: 10,   // PRD §13: 8–12%
    citySharePct: 55,      // EPA combined is ~55% city / 45% highway
    winter: false,         // PRD §13: winter correction
    winterFactor: 0.85,    // efficiency x 0.85 / UF x 0.85
    homeCharging: true     // PHEV: is a home charger available? (T7)
  };

  function clamp(n, lo, hi) { return Math.min(hi, Math.max(lo, n)); }

  function num(v, fallback) {
    var n = parseFloat(v);
    return isFinite(n) ? n : fallback;
  }

  /* ---------------------------------------------------------------
     Vehicle record adapter.
     Two shapes reach this engine:
       (a) canonical  — {category, kwhPer100MiCity, ...}  (gen.py / tests)
       (b) browser    — short keys {c, kC, kH, kX, gC, gH, gX, uf, ...}
                        emitted by gen.py browser_payload() to keep the
                        inlined dataset small.
     view() maps (b) onto (a) so the formula below has a single shape.
     --------------------------------------------------------------- */
  function view(v) {
    if (!v) return {};
    if (v.category !== undefined) return v;          // already canonical
    var o = {}, k;
    for (k in v) { if (Object.prototype.hasOwnProperty.call(v, k)) o[k] = v[k]; }
    o.category = v.c;
    o.kwhPer100MiCity = num(v.kC, 0);
    o.kwhPer100MiHighway = num(v.kH, 0);
    o.kwhPer100MiCombined = num(v.kX, 0);
    o.mpgCity = num(v.gC, 0);
    o.mpgHighway = num(v.gH, 0);
    o.mpgCombined = num(v.gX, 0);
    o.utilityFactor = num(v.uf, 0);
    return o;
  }

  /* --- efficiency in mi/kWh, interpolated between city and highway --- */
  function miPerKwh(rawV, citySharePct, winter) {
    var v = view(rawV);
    var s = clamp(num(citySharePct, DEFAULTS.citySharePct), 0, 100) / 100;
    var city = num(v.kwhPer100MiCity, 0);
    var hwy = num(v.kwhPer100MiHighway, 0);
    var combined = num(v.kwhPer100MiCombined, 0);
    var kwh100;
    if (city > 0 && hwy > 0) {
      kwh100 = city * s + hwy * (1 - s);
    } else if (combined > 0) {
      kwh100 = combined;
    } else {
      return 0;
    }
    if (winter) kwh100 = kwh100 / DEFAULTS.winterFactor;   // worse efficiency
    return kwh100 > 0 ? 100 / kwh100 : 0;
  }

  /* --- gasoline MPG, interpolated between city and highway --- */
  function mpg(rawV, citySharePct, winter) {
    var v = view(rawV);
    var s = clamp(num(citySharePct, DEFAULTS.citySharePct), 0, 100) / 100;
    var city = num(v.mpgCity, 0);
    var hwy = num(v.mpgHighway, 0);
    var comb = num(v.mpgCombined, 0);
    var m;
    if (city > 0 && hwy > 0) m = city * s + hwy * (1 - s);
    else m = comb;
    if (winter) m = m * DEFAULTS.winterFactor;             // worse economy
    return m > 0 ? m : 0;
  }

  /* ---------------------------------------------------------------
     Core: monthly cost for one vehicle.
     p = { milesPerMonth, homeRateUsdKwh, publicRateUsdKwh, homeSharePct,
           gasUsdPerGal, chargingLossPct, citySharePct, winter,
           homeCharging (PHEV only) }
     --------------------------------------------------------------- */
  function monthlyCost(rawV, p) {
    var v = view(rawV);
    var miles = clamp(num(p.milesPerMonth, DEFAULTS.milesPerMonth), 0, 100000);
    var loss = clamp(num(p.chargingLossPct, DEFAULTS.chargingLossPct), 0, 40) / 100;
    var winter = !!p.winter;
    var homeShare = clamp(num(p.homeSharePct, DEFAULTS.homeSharePct), 0, 100) / 100;

    var out = {
      monthly: 0, kwh: 0, gallons: 0,
      electricMiles: 0, gasMiles: 0,
      mode: v.category, note: ''
    };

    if (v.category === 'ev') {
      var mpk = miPerKwh(v, p.citySharePct, winter);
      if (mpk <= 0) return out;
      var kwh = miles / mpk;
      var blendedRate = num(p.homeRateUsdKwh, 0) * homeShare +
                        num(p.publicRateUsdKwh, 0) * (1 - homeShare);
      out.kwh = kwh;
      out.monthly = kwh * blendedRate * (1 + loss);
      out.electricMiles = miles;
      return out;
    }

    if (v.category === 'phev') {
      var uf = num(v.utilityFactor, 0);            // EPA utility factor
      if (winter) uf = uf * DEFAULTS.winterFactor;  // PRD §13: UF x 0.85
      // T7: without home charging a PHEV behaves like a hybrid — it runs on
      // petrol at its charge-sustaining MPG. Recompute and flag it.
      var hasHome = p.homeCharging !== false;
      var eShare = hasHome ? uf : 0;
      var eMiles = miles * eShare;
      var gMiles = miles - eMiles;

      var mpkP = miPerKwh(v, p.citySharePct, winter);
      var mpgP = mpg(v, p.citySharePct, winter);   // charge-sustaining MPG
      var kwhP = mpkP > 0 ? eMiles / mpkP : 0;
      var galP = mpgP > 0 ? gMiles / mpgP : 0;

      var blendedP = num(p.homeRateUsdKwh, 0) * homeShare +
                     num(p.publicRateUsdKwh, 0) * (1 - homeShare);

      out.electricMiles = eMiles;
      out.gasMiles = gMiles;
      out.kwh = kwhP;
      out.gallons = galP;
      out.monthly = kwhP * blendedP * (1 + loss) + galP * num(p.gasUsdPerGal, 0);
      if (!hasHome) {
        out.note = 'Home charging assumed unavailable, so the plug-in hybrid is costed on ' +
                   'petrol only at its charge-sustaining economy ('
                   + mpgP.toFixed(1) + ' MPG) — i.e. as a conventional hybrid.';
      }
      return out;
    }

    // hev / gas
    var m = mpg(v, p.citySharePct, winter);
    if (m <= 0) return out;
    var gal = miles / m;
    out.gallons = gal;
    out.gasMiles = miles;
    out.monthly = gal * num(p.gasUsdPerGal, 0);
    return out;
  }

  /* --- unit helpers (country pages + converter) --- */
  function mpgToL100km(mpgUS) { return mpgUS > 0 ? 235.214583 / mpgUS : 0; }
  function l100kmToMpg(l) { return l > 0 ? 235.214583 / l : 0; }
  function miPerKwhToKwh100km(miPerKwh) { return miPerKwh > 0 ? 100 / (miPerKwh * 1.609344) : 0; }

  /* Mirrors gen.py money(): symbol + thousands separators + fixed decimals.
     The two must format identically or the pre-rendered HTML and the live
     JavaScript result would visibly disagree on the same page. */
  function money(n, symbol, decimals) {
    var d = decimals === undefined ? 2 : decimals;
    var s = (Math.round(n * Math.pow(10, d)) / Math.pow(10, d)).toFixed(d);
    var parts = s.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return (symbol || '$') + parts.join('.');
  }

  global.FuelCost = {
    DEFAULTS: DEFAULTS,
    view: view,
    monthlyCost: monthlyCost,
    miPerKwh: miPerKwh,
    mpg: mpg,
    mpgToL100km: mpgToL100km,
    l100kmToMpg: l100kmToMpg,
    miPerKwhToKwh100km: miPerKwhToKwh100km,
    money: money,
    clamp: clamp,
    num: num
  };
})(typeof window !== 'undefined' ? window : globalThis);
