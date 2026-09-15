=== 1) scripts/check_setup.py (Preflight) ===
ShipSolo setup check: student-site-compliance-pipeline

Environment variables:

Common commands:
- OK git
- OK node
- OK npm
- OK python3
- OK curl
- OK wrangler
- OK gh

Browser/login requirements:

Note: this script only checks local readiness. It cannot verify every web login state.
exit=0
=== 2) scripts/validate_handoff.py ===
has_status: PASS
has_risk: PASS
has_next: PASS
exit=0
=== 3) scripts/validate_compliance_docs.py ===
OK 合规与基础法律页面 report basic structure passed
exit=0
=== 4) site build + self-check ===
Building site …
  wrote assets/styles.css
  wrote assets/consent.js
  wrote index.html
  wrote privacy\index.html
  wrote terms\index.html
  wrote cookie-policy\index.html
  wrote disclaimer\index.html
  wrote about\index.html
  wrote contact\index.html
  wrote 404.html
  wrote _redirects
  wrote _headers
  wrote robots.txt
  wrote sitemap.xml
Built 8 routes.

Self-check …
  8 HTML files found
  OK  all 8 internal links resolve (no 404)
  OK  all 8 canonical routes present
  OK  footer carries all 6 legal links on every page
  OK  16 alias redirects emit 308
  OK  zero third-party font/CDN references (self-hosted)
  OK  all non-essential tags ship disabled (consent gate)
  INFO  8 pages contain placeholders (must be replaced before launch):
        404.html: [OPERATING ENTITY]
        about/index.html: [CONTACT EMAIL], [OPERATING ENTITY]
        contact/index.html: [CONTACT EMAIL], [OPERATING ENTITY]
        cookie-policy/index.html: [CONTACT EMAIL], [OPERATING ENTITY]
        disclaimer/index.html: [CONTACT EMAIL], [OPERATING ENTITY]
        index.html: [OPERATING ENTITY]
        privacy/index.html: [CONTACT EMAIL], [OPERATING ENTITY]
        terms/index.html: [CONTACT EMAIL], [JURISDICTION], [OPERATING ENTITY]

SELF-CHECK PASSED
exit=0
=== 5) local HTTP smoke ===
/                        200
/privacy/                200
/terms/                  200
/cookie-policy/          200
/disclaimer/             200
/about/                  200
/contact/                200
/assets/styles.css       200
/assets/consent.js       200
/robots.txt              200
/sitemap.xml             200
/nope                    404
