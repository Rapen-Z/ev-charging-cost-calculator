/* ============================================================
   Cookie / tracker consent gate
   ------------------------------------------------------------
   Compliance contract (stage 04-compliance):
   - NOTHING non-essential is loaded before an explicit choice.
   - "Accept all" and "Reject all" are visually identical (§25
     TDDDG Equal-Choice / OVG Lüneburg 14 LA 1/24).
   - No pre-ticked boxes (CJEU Planet49 C-673/17).
   - Closing / scrolling / browsing is NOT consent.
   - Global Privacy Control (GPC) is honoured as a valid opt-out.
   - Withdrawal is available from the footer at any time.

   >>> ALL NON-ESSENTIAL TAGS SHIP WITH enabled:false <<<
   Flipping one to true is a P0-gated change: see
   04-compliance/02-third-party-mapping.md §2.3 (6-step change
   control) and run QA-GATE-01 before deploying.
   ============================================================ */
(function () {
  'use strict';

  var POLICY_VERSION = '2026-09-10';
  var COOKIE_NAME = 'cc_consent';
  var COOKIE_MAX_AGE_DAYS = 365;   // do not re-ask for 12 months after a refusal

  /* ---------------- tag registry ---------------- */
  /* enabled:false = will not be injected, regardless of consent. */
  var TAGS = [
    {
      id: 'ga4',
      name: 'Google Analytics',
      category: 'analytics',
      enabled: false,
      measurementId: '[GA_MEASUREMENT_ID]',
      cookies: ['_ga', '_ga_*'],
      load: function () {
        if (isPlaceholder(this.measurementId)) return skip(this);
        var id = this.measurementId;
        var s = document.createElement('script');
        s.async = true;
        s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id);
        document.head.appendChild(s);
        window.dataLayer = window.dataLayer || [];
        window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
        window.gtag('js', new Date());
        window.gtag('config', id, { anonymize_ip: true });
      }
    },
    {
      id: 'clarity',
      name: 'Microsoft Clarity',
      category: 'analytics',
      enabled: false,
      projectId: '[CLARITY_PROJECT_ID]',
      cookies: ['_clck', '_clsk'],
      load: function () {
        if (isPlaceholder(this.projectId)) return skip(this);
        /* P1-2: Clarity records the DOM. Before enabling, masking of the
           calculator inputs MUST be verified, or Clarity must not be
           loaded on calculator pages at all. */
        window.clarity = window.clarity || function () {
          (window.clarity.q = window.clarity.q || []).push(arguments);
        };
        var s = document.createElement('script');
        s.async = true;
        s.src = 'https://www.clarity.ms/tag/' + encodeURIComponent(this.projectId);
        document.head.appendChild(s);
      }
    },
    {
      id: 'ads',
      name: 'Advertising network',
      category: 'advertising',
      enabled: false,
      scriptSrc: '[AD_NETWORK_SCRIPT_URL]',
      cookies: [],
      load: function () {
        if (isPlaceholder(this.scriptSrc)) return skip(this);
        var s = document.createElement('script');
        s.async = true;
        s.src = this.scriptSrc;
        document.head.appendChild(s);
      }
    }
  ];

  var CATEGORIES = [
    {
      id: 'necessary',
      name: 'Strictly necessary',
      required: true,
      desc: 'Remembers your privacy choices and keeps the site secure. These cannot be turned off.'
    },
    {
      id: 'analytics',
      name: 'Analytics',
      required: false,
      desc: 'Helps us understand which pages are used. Currently not enabled.'
    },
    {
      id: 'advertising',
      name: 'Advertising',
      required: false,
      desc: 'Used for ad delivery and measurement. Currently not enabled.'
    }
  ];

  /* ---------------- helpers ---------------- */
  function isPlaceholder(v) {
    return !v || String(v).charAt(0) === '[';
  }
  function skip(tag) {
    if (window.console && console.info) {
      console.info('[consent] "' + tag.id + '" is enabled in config but its ID/URL is still a placeholder — not loaded.');
    }
  }
  function readCookie(name) {
    var parts = document.cookie ? document.cookie.split(';') : [];
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i].trim();
      if (p.indexOf(name + '=') === 0) {
        try { return JSON.parse(decodeURIComponent(p.substring(name.length + 1))); }
        catch (e) { return null; }
      }
    }
    return null;
  }
  function writeCookie(obj) {
    var value = encodeURIComponent(JSON.stringify(obj));
    var secure = location.protocol === 'https:' ? '; Secure' : '';
    document.cookie = COOKIE_NAME + '=' + value +
      '; Path=/; Max-Age=' + (COOKIE_MAX_AGE_DAYS * 86400) +
      '; SameSite=Lax' + secure;
  }
  function hasGPC() {
    return navigator.globalPrivacyControl === true;
  }
  function emptyState() {
    return { necessary: true, analytics: false, advertising: false };
  }

  /* ---------------- apply ---------------- */
  function apply(state) {
    TAGS.forEach(function (tag) {
      if (!tag.enabled) return;                 // hard off-switch (P0-2)
      if (!state[tag.category]) return;         // no consent
      if (document.getElementById('cc-tag-' + tag.id)) return; // already loaded
      try { tag.load(); } catch (e) {
        if (window.console) console.error('[consent] failed to load ' + tag.id, e);
      }
    });
  }

  function purgeThirdPartyCookies() {
    /* best-effort removal on withdrawal */
    var host = location.hostname;
    var domains = [host, '.' + host, host.replace(/^[^.]+\./, ''), '.' + host.replace(/^[^.]+\./, '')];
    var names = ['_ga', '_gid', '_gat', '_clck', '_clsk', '_fbp', '_gcl_au'];
    var i, j;
    for (i = 0; i < names.length; i++) {
      for (j = 0; j < domains.length; j++) {
        document.cookie = names[i] + '=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:01 GMT' +
          (domains[j] ? '; Domain=' + domains[j] : '');
      }
    }
  }

  function save(state, action) {
    writeCookie({
      v: POLICY_VERSION,
      ts: new Date().toISOString(),
      a: action,
      necessary: true,
      analytics: !!state.analytics,
      advertising: !!state.advertising
    });
    hide();
    if (state.analytics || state.advertising) {
      apply({ analytics: state.analytics, advertising: state.advertising });
    } else {
      purgeThirdPartyCookies();
    }
  }

  /* ---------------- UI ---------------- */
  var banner, managePanel;

  function build() {
    banner = document.createElement('div');
    banner.className = 'cc-banner';
    banner.id = 'cc-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-modal', 'false');
    banner.setAttribute('aria-labelledby', 'cc-title');
    banner.setAttribute('aria-describedby', 'cc-desc');

    var inner = document.createElement('div');
    inner.className = 'cc-banner__inner';

    var head = document.createElement('div');
    head.innerHTML =
      '<h2 class="cc-banner__title" id="cc-title">Cookies on this site</h2>' +
      '<p class="cc-banner__text" id="cc-desc">We use one strictly necessary cookie to remember your choice. ' +
      'Analytics and advertising are <strong>not currently enabled</strong>. If that changes, nothing non-essential ' +
      'will load until you agree. Read the <a href="/cookie-policy">Cookie Policy</a> and <a href="/privacy">Privacy Policy</a>.</p>';
    inner.appendChild(head);

    var actions = document.createElement('div');
    actions.className = 'cc-actions';

    // Equal-choice: Accept and Reject share one class string so they cannot
    // drift apart visually (H group / §25 TDDDG). The beam hover is part of
    // the shared treatment.
    var accept = mkButton('Accept all', 'btn beam', function () {
      save({ analytics: true, advertising: true }, 'accept_all');
    });
    var reject = mkButton('Reject all', 'btn beam', function () {
      save({ analytics: false, advertising: false }, 'reject_all');
    });
    var manage = mkButton('Manage preferences', 'btn btn--link', function () {
      managePanel.hidden = !managePanel.hidden;
    });
    manage.setAttribute('aria-expanded', 'false');
    manage.addEventListener('click', function () {
      manage.setAttribute('aria-expanded', managePanel.hidden ? 'false' : 'true');
    });

    actions.appendChild(accept);
    actions.appendChild(reject);
    actions.appendChild(manage);
    inner.appendChild(actions);

    managePanel = document.createElement('div');
    managePanel.className = 'cc-manage';
    managePanel.hidden = true;
    CATEGORIES.forEach(function (cat) {
      var row = document.createElement('div');
      row.className = 'cc-cat';
      var input = document.createElement('input');
      input.type = 'checkbox';
      input.id = 'cc-cat-' + cat.id;
      input.checked = cat.required;                 // NOT pre-ticked for optional cats
      input.disabled = !!cat.required;
      var label = document.createElement('label');
      label.setAttribute('for', input.id);
      label.textContent = cat.name;
      var desc = document.createElement('p');
      desc.className = 'cc-cat__desc';
      desc.textContent = cat.desc;
      row.appendChild(input);
      row.appendChild(label);
      row.appendChild(desc);
      managePanel.appendChild(row);
    });
    var saveBtn = mkButton('Save preferences', 'btn', function () {
      save({
        analytics: document.getElementById('cc-cat-analytics').checked,
        advertising: document.getElementById('cc-cat-advertising').checked
      }, 'save');
    });
    var saveWrap = document.createElement('div');
    saveWrap.className = 'cc-actions';
    saveWrap.style.marginTop = '.9rem';
    saveWrap.appendChild(saveBtn);
    managePanel.appendChild(saveWrap);
    inner.appendChild(managePanel);

    banner.appendChild(inner);
    document.body.appendChild(banner);
  }

  function mkButton(text, cls, onClick) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = cls;
    b.textContent = text;
    b.addEventListener('click', onClick);
    return b;
  }

  function hide() { if (banner) banner.hidden = true; }
  function show() { if (banner) { banner.hidden = false; if (managePanel) managePanel.hidden = true; } }

  function isStale(state) {
    if (!state || state.v !== POLICY_VERSION) return true;
    if (!state.ts) return true;
    var age = Date.now() - Date.parse(state.ts);
    return isNaN(age) || age > COOKIE_MAX_AGE_DAYS * 86400000;
  }

  /* ---------------- boot ---------------- */
  function init() {
    build();
    var state = readCookie(COOKIE_NAME);

    /* GPC: treat as a refusal of analytics + advertising */
    if (hasGPC()) {
      if (!state || state.analytics || state.advertising) {
        save({ analytics: false, advertising: false }, 'gpc');
      } else {
        hide();
      }
      return;
    }

    if (isStale(state)) {
      show();
      return;
    }

    hide();
    apply({ analytics: !!state.analytics, advertising: !!state.advertising });
  }

  window.CookieConsent = {
    open: function () {
      if (!banner) return;
      var s = readCookie(COOKIE_NAME) || emptyState();
      var an = document.getElementById('cc-cat-analytics');
      var ad = document.getElementById('cc-cat-advertising');
      if (an) an.checked = !!s.analytics;
      if (ad) ad.checked = !!s.advertising;
      show();
      managePanel.hidden = false;
    },
    status: function () { return readCookie(COOKIE_NAME); },
    version: POLICY_VERSION
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
