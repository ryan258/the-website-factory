# Plan: host client sites on Cloudflare Workers

**Status:** draft for Ryan's decision, 2026-10-27. Nothing has changed yet.

## Goal

The factory makes a site. Each client site runs on its own Cloudflare Worker, on the
client's domain. The contact form stores each enquiry and emails it to the owner.
Images ship inside the site.

## Why move off Pages

- **Cloudflare's direction.** Its docs now say to start new projects on Workers. Pages
  keeps working, but new features go to Workers.
- **Same cost.** Static file requests are free on both. The contact function is billed
  the same way.
- **Email.** A Worker can send email with a `send_email` binding. A Pages Function
  cannot, which is why the form only stores enquiries today. Sending to a verified
  destination address is free on every plan.
- **Previews.** `wrangler preview` gives each preview a stable URL. It needs wrangler
  4.135 or later, and the repo pins 4.136.2.
- **One condition.** A Worker can only serve a domain whose DNS is on Cloudflare. The
  hosting guide already moves client domains there.

## What stays the same

- The Hugo build and the `public/` output.
- `static/_headers`. Workers reads it natively for static files.
- The `ENQUIRY` KV store, the `ENQUIRY_ENABLED` gate, rate limiting, the 90-day expiry,
  the optional webhook, and the logic inside `contact.js`.
- Images stay in the site. The R2 decision from 2026-10-14 stands.

## What changes

| File | Change |
| --- | --- |
| `wrangler.toml` | Drop `pages_build_output_dir`. Add `main = "worker/index.js"` and `[assets]` with `directory = "public"`, `run_worker_first = ["/api/*"]`, `not_found_handling = "404-page"`. Add `[[send_email]]` with a fixed `destination_address`. |
| `worker/index.js` (new) | Small router: `POST /api/contact` goes to the contact handler. Everything else is a static file. |
| `functions/api/contact.js` | Moves under `worker/`. Same logic. After the KV write succeeds, it also emails the enquiry, best effort, the same way the webhook works now. |
| `functions/_middleware.js` | Delete. A `.assetsignore` file keeps `.factory-build.json` from being uploaded at all, so no code has to block it. |
| `.github/workflows/deploy.yml` | `pages deploy public --project-name=258webco` becomes `wrangler deploy`. |
| `.github/workflows/preview.yml` | Becomes `wrangler preview --name site` or `--name workshop`. Previews get their own test KV, so they never write production data. |
| `scripts/check_contact.sh` | `wrangler pages dev` becomes `wrangler dev`. |
| `scripts/test_contact_endpoint.mjs` | New import path. Add cases for the email step: sent after storage, never before it, and a failed send still returns success. |
| `scripts/new_site.py`, `scripts/eject.py`, `scripts/smoke.py` | Generated config, printed steps, and example URLs switch from `pages.dev` to `workers.dev`. |
| Docs | `cloudflare-setup.md`, `guide-to-hosting-on-cloudflare-on-the-cheap.md`, `factory-guide.md`, `starter-guide.md`, `README.md`, `HAPPY-PATH.md`, and the table in `CLAUDE.md`. |
| `data/presets/258webco.json` | The `privacy` section must say that enquiries are also emailed to the owner. |

## Contact form email

- **Order:** store in KV first, then email. If storage fails, nothing is emailed and the
  visitor sees an error. If the email fails, the enquiry is still safe in KV.
- **One recipient:** the binding is pinned to the owner's address, so a bug cannot
  email anyone else.
- **Sender:** an address on the client's domain, such as `enquiries@<domain>`. This
  needs Email Routing on the domain and the owner's inbox verified as a destination.
- **Reply-to:** the visitor's email address, but only when it passes the form's
  existing validation.
- **Cost:** free, because it only ever sends to a verified destination.

## Phases

1. **Pilot.** Deploy 258webco as a new Worker on its `workers.dev` address, with its
   own test KV store. The live Pages site is not touched.
   *Done when:* `smoke.py` passes against the `workers.dev` URL with the form off, and
   with the form on a test enquiry lands in the test KV store and in the owner's inbox.
2. **Factory.** Switch `new_site.py`, `eject.py`, the workflows, tests, and docs.
   *Done when:* every gate in `CLAUDE.md` passes, including `check_contact.sh` and the
   browser checks.
3. **Cutover.** Attach 258webco.com to the Worker and detach it from the Pages project.
   Keep the Pages project for two weeks as the way back, then delete it.
   *Done when:* `smoke.py` passes on `https://258webco.com`.
4. **Later, optional.** A separate write token lets the Cloudflare MCP do each client's
   setup steps: create the KV store, attach the domain, check DNS.

Each phase needs Ryan's go-ahead. Deploys run only through the manual workflow.

## Risks

- A client who will not move DNS to Cloudflare cannot be hosted this way. Pages could
  serve that client through a CNAME record.
- `_headers` does not apply to responses the Worker writes. `contact.js` already sets
  its own security headers. The pilot must confirm they arrive.
- Trailing-slash URLs: Hugo writes `about/index.html`. Workers' default handling should
  serve `/about/` the same way Pages does. The pilot must confirm it.
- New accounts start with a small daily email quota. Sends to verified destinations do
  not count toward it.

## Decisions for Ryan

1. **Ship the 20 commits that are not live yet, on Pages, before the move?**
   Recommended: yes. That keeps the hosting change separate from content changes.
2. **Which inbox gets 258webco enquiries?** To be confirmed. It must be verified as a
   destination in Email Routing.
3. **Keep the webhook option?** Recommended: yes. It still serves clients who want
   enquiries sent somewhere other than email.
