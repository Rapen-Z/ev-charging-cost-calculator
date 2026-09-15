// Worker entry for Cloudflare Workers Static Assets.
//
// The site is 100% static (HTML/CSS/JS + /assets/zips.json — no server-side API).
// Workers Static Assets serves ./site directly and, importantly, handles the
// site's _redirects (308 aliases) and _headers (security headers) NATIVELY, and
// returns 404.html for unmatched paths via `not_found_handling = "404-page"` in
// wrangler.toml. So this Worker only needs to pass the request through to ASSETS.
//
// Keeping an explicit (tiny) Worker is intentional: it makes the deployment a
// real, inspectable Cloudflare Worker and leaves a clean place to add genuine
// dynamic routes later (e.g. a real /api/* handler) without restructuring.

export default {
  async fetch(request, env) {
    return env.ASSETS.fetch(request);
  },
};
