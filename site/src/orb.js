/* ============================================================
   Thinking orb — the loading indicator, drawn on <canvas>.
   ------------------------------------------------------------
   Replaces the generic spinner / skeleton. Three decisions:

   1. MATERIAL. The reference orbs are luminous blobs. On this
      site's warm paper background, additive glow reads as a
      smudge — light has nothing to emit against. So the orb is
      built from *pigment* instead: overlapping radial fields
      composited with `multiply`, the way ink layers on paper,
      with a conic sweep ring on top as the progress cue.

   2. STATES DIFFER STRUCTURALLY, not just in speed. A screenshot,
      or half a second of peripheral vision, has to be enough to
      tell "working" from "done" from "failed". So each state owns
      its ring geometry (how much of the circumference is lit,
      solid vs broken) and how tightly the pigment converges —
      speed only modulates the result.

   3. COST. One rAF loop per visible orb, paused when scrolled
      out of view or when the tab is hidden, and skipped entirely
      under prefers-reduced-motion (a single static frame is
      drawn instead). DPR is capped at 2.

   API
     ThinkingOrb.scan(root?)        mount every [data-orb] under root
     ThinkingOrb.setState(el, st)   'idle'|'working'|'solving'|'done'|'fail'
     ThinkingOrb.destroy(el)
   ============================================================ */
(function () {
  'use strict';

  /* arc     – fraction of the circumference the sweep lights up
     dashLen – [on, off] as fractions of the circumference; null = solid
     blobR   – pigment field radius (convergence: smaller = tighter/pressing) */
  var STATES = {
    idle:    { speed: 0.18, blobs: 3, spread: 0.26, pulse: 0.10, ring: 0.55,
               arc: 0.55, dashLen: null,          blobR: 0.60 },
    working: { speed: 0.85, blobs: 4, spread: 0.34, pulse: 0.20, ring: 0.95,
               arc: 1.00, dashLen: null,          blobR: 0.66 },
    solving: { speed: 1.60, blobs: 5, spread: 0.20, pulse: 0.30, ring: 1.00,
               arc: 0.70, dashLen: [0.20, 0.11],  blobR: 0.72 },
    done:    { speed: 0.30, blobs: 3, spread: 0.20, pulse: 0.05, ring: 1.00,
               arc: 1.00, dashLen: null,          blobR: 0.58 },
    fail:    { speed: 0.00, blobs: 2, spread: 0.16, pulse: 0.00, ring: 0.80,
               arc: 1.00, dashLen: [0.05, 0.05],  blobR: 0.54 }
  };

  var reduced = false;
  try {
    reduced = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (e) { /* older engines: assume motion is fine */ }

  /* ---- colour: read the live tokens so the orb tracks the theme ---- */

  function hexToRgb(s) {
    s = String(s).trim();
    var m = /^#([0-9a-f]{3})$/i.exec(s);
    if (m) {
      return [parseInt(m[1][0] + m[1][0], 16),
              parseInt(m[1][1] + m[1][1], 16),
              parseInt(m[1][2] + m[1][2], 16)];
    }
    m = /^#([0-9a-f]{6})$/i.exec(s);
    if (m) {
      var n = parseInt(m[1], 16);
      return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    }
    m = /^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)/i.exec(s);
    if (m) return [+m[1], +m[2], +m[3]];
    return null;
  }

  var PALETTE = null;
  function palette() {
    if (PALETTE) return PALETTE;
    var cs = window.getComputedStyle(document.documentElement);
    function token(name, fallback) {
      var v = cs.getPropertyValue(name);
      return hexToRgb(v) || fallback;
    }
    PALETTE = {
      accent: token('--accent',     [18, 79, 62]),
      signal: token('--signal',     [63, 174, 134]),
      hot:    token('--signal-hot', [127, 224, 189]),
      brass:  token('--brass',      [184, 134, 47]),
      err:    token('--err',        [143, 47, 34])
    };
    return PALETTE;
  }

  /* If the OS flips light/dark mid-session, drop the cached palette so
     the next frame repaints with the new theme's tokens. */
  if (window.matchMedia) {
    try {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
        PALETTE = null;
      });
    } catch (e) { /* older Safari: no listener support, palette stays cached */ }
  }

  function rgba(c, a) {
    return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')';
  }

  /* ---- one frame --------------------------------------------------
     Pigment fields are multiplied so overlaps deepen instead of
     washing out, which is what gives the disc its marbled interior. */
  function paint(ctx, size, time, cfg, failed) {
    var P = palette();
    var r = size / 2;
    var hue = failed ? P.err : P.accent;
    var mid = failed ? P.err : P.signal;
    var lift = failed ? P.brass : P.hot;
    var lw = Math.max(1.5, r * 0.18);

    ctx.clearRect(0, 0, size, size);
    ctx.save();
    ctx.beginPath();
    ctx.arc(r, r, r - lw * 0.5, 0, Math.PI * 2);
    ctx.clip();

    /* base wash — kept low so the pigment fields below read as layers */
    var base = ctx.createRadialGradient(r * 0.72, r * 0.66, r * 0.06, r, r, r);
    base.addColorStop(0, rgba(lift, 0.40));
    base.addColorStop(0.55, rgba(mid, 0.24));
    base.addColorStop(1, rgba(hue, 0.12));
    ctx.fillStyle = base;
    ctx.fillRect(0, 0, size, size);

    /* pigment fields */
    ctx.globalCompositeOperation = 'multiply';
    var breathe = 1 + Math.sin(time * 1.1) * cfg.pulse;
    var rr = r * cfg.blobR;
    for (var i = 0; i < cfg.blobs; i++) {
      var a = time * cfg.speed + (i / cfg.blobs) * Math.PI * 2;
      var dist = r * cfg.spread * breathe;
      var cx = r + Math.cos(a) * dist;
      var cy = r + Math.sin(a) * dist;
      var g = ctx.createRadialGradient(cx, cy, 0, cx, cy, rr);
      var tint = (i % 2 === 0) ? hue : mid;
      g.addColorStop(0, rgba(tint, 0.46));
      g.addColorStop(0.6, rgba(tint, 0.18));
      g.addColorStop(1, rgba(tint, 0));
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(cx, cy, rr, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalCompositeOperation = 'source-over';

    /* the sweep ring — the part that actually says "still working".
       `arc` shortens the lit portion, `dashLen` breaks it up. */
    var circ = Math.PI * 2 * r;
    var lit = cfg.arc;
    if (typeof ctx.createConicGradient === 'function') {
      var ring = ctx.createConicGradient(time * cfg.speed * 0.9, r, r);
      ring.addColorStop(0.00, rgba(hue, 0.00));
      ring.addColorStop(Math.max(0.02, lit * 0.45), rgba(hue, 0.70 * cfg.ring));
      ring.addColorStop(lit * 0.78, rgba(mid, 1.00 * cfg.ring));
      ring.addColorStop(lit * 0.94, rgba(lift, 0.98 * cfg.ring));
      ring.addColorStop(lit, rgba(hue, 0.00));
      ring.addColorStop(1.00, rgba(hue, 0.00));
      ctx.strokeStyle = ring;
    } else {
      ctx.strokeStyle = rgba(mid, 0.75 * cfg.ring);
    }
    ctx.lineWidth = lw;
    if (cfg.dashLen) {
      ctx.setLineDash([circ * cfg.dashLen[0], circ * cfg.dashLen[1]]);
      ctx.lineDashOffset = -time * cfg.speed * 14;
    } else {
      ctx.setLineDash([]);
      ctx.lineDashOffset = 0;
    }
    ctx.beginPath();
    ctx.arc(r, r, r - lw * 0.5, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.lineDashOffset = 0;

    /* specular: a small orbiting highlight, so the disc reads as a
       physical bead rather than a flat gradient */
    var sa = time * cfg.speed * 1.6;
    var sx = r + Math.cos(sa) * r * 0.34;
    var sy = r + Math.sin(sa) * r * 0.34;
    var sg = ctx.createRadialGradient(sx, sy, 0, sx, sy, r * 0.32);
    sg.addColorStop(0, rgba(lift, 0.50));
    sg.addColorStop(1, rgba(lift, 0));
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = sg;
    ctx.beginPath();
    ctx.arc(sx, sy, r * 0.32, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalCompositeOperation = 'source-over';

    ctx.restore();
  }

  /* ---- lifecycle --------------------------------------------------- */

  var live = [];       // orbs running a rAF loop
  var rafId = null;

  function frame() {
    rafId = null;
    var now = performance.now() / 1000;
    var again = false;
    for (var i = 0; i < live.length; i++) {
      var o = live[i];
      if (o.paused) continue;
      paint(o.ctx, o.size, now, STATES[o.state] || STATES.working, o.state === 'fail');
      again = true;
    }
    if (again) rafId = requestAnimationFrame(frame);
  }

  function ensureLoop() {
    if (rafId === null && live.some(function (o) { return !o.paused; })) {
      rafId = requestAnimationFrame(frame);
    }
  }

  function pause(o) { if (!o.paused) { o.paused = true; ensureLoop(); } }
  function resume(o) { if (o.paused) { o.paused = false; ensureLoop(); } }

  function mount(el) {
    if (el.__orb) return el.__orb;

    var size = parseInt(el.getAttribute('data-orb-size') || '20', 10) || 20;
    var canvas = document.createElement('canvas');
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.round(size * dpr);
    canvas.height = Math.round(size * dpr);
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    el.appendChild(canvas);

    var ctx = null;
    try { ctx = canvas.getContext('2d'); } catch (e) { ctx = null; }

    var state = el.getAttribute('data-orb') || el.getAttribute('data-orb-state') || 'working';
    var cfg = STATES[state] || STATES.working;

    if (!ctx) {
      /* No 2D context (jsdom, or a hardened canvas-less build). Fall
         back to a CSS ring so the indicator still means something. */
      el.classList.add('orb--fallback');
      el.__orb = { setState: function () {}, destroy: function () {} };
      return el.__orb;
    }

    var o = { el: el, canvas: canvas, ctx: ctx, size: canvas.width,
              state: state, paused: false, io: null };

    /* Static frame under reduced motion: identity kept, no travel. */
    if (reduced) {
      paint(ctx, o.size, 0, cfg, state === 'fail');
      el.__orb = {
        setState: function (s) {
          o.state = s;
          paint(ctx, o.size, 0, STATES[s] || STATES.working, s === 'fail');
        },
        destroy: function () { el.__orb = null; }
      };
      return el.__orb;
    }

    live.push(o);

    /* Only burn frames while the orb is actually on screen. */
    if (typeof IntersectionObserver === 'function') {
      o.io = new IntersectionObserver(function (entries) {
        for (var i = 0; i < entries.length; i++) {
          if (entries[i].isIntersecting) resume(o); else pause(o);
        }
      }, { rootMargin: '64px' });
      o.io.observe(el);
    }
    if (document.hidden) pause(o);
    ensureLoop();

    var api = {
      setState: function (s) {
        o.state = s;
        el.setAttribute('data-orb', s);
        if (reduced) paint(ctx, o.size, 0, STATES[s] || STATES.working, s === 'fail');
      },
      destroy: function () {
        pause(o);
        if (o.io) o.io.disconnect();
        var idx = live.indexOf(o);
        if (idx !== -1) live.splice(idx, 1);
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
        el.__orb = null;
      }
    };
    el.__orb = api;
    return api;
  }

  function scan(root) {
    var host = root || document;
    var nodes = host.querySelectorAll ? host.querySelectorAll('[data-orb]') : [];
    for (var i = 0; i < nodes.length; i++) mount(nodes[i]);
  }

  function setState(el, state) {
    var api = el && el.__orb ? el.__orb : (el ? mount(el) : null);
    if (api) api.setState(state);
  }

  document.addEventListener('visibilitychange', function () {
    for (var i = 0; i < live.length; i++) {
      if (document.hidden) pause(live[i]); else resume(live[i]);
    }
  });

  window.ThinkingOrb = {
    scan: scan,
    mount: mount,
    setState: setState,
    destroy: function (el) { if (el && el.__orb) el.__orb.destroy(); }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { scan(document); });
  } else {
    scan(document);
  }
})();
