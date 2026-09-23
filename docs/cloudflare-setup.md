# Putting a site on Cloudflare, step by step

This is the part nobody else can do for you, because it needs your Cloudflare login.
Everything here happens in one Cloudflare account, so there is only one place to look later.

Do the steps in order. Each one says what to type, what you should see, and what it
means if you see something else. If a step looks wrong, stop there rather than
carrying on — a wrong step early makes the later ones confusing.

Written for the domain **258webco.com**. If you use a different domain, swap the name.

---

## Before you start

Open a terminal in the project folder:

```sh
cd ~/Projects/the-website-factory
```

Every command below is run from there.

One piece of housekeeping first. The old `public/` folder has leftovers in it from
builds that ran outside the helper, and the build now refuses to write into a folder
it does not fully own. Clear it once:

```sh
rm -rf public
```

That folder is generated output. Nothing you wrote by hand lives in it.

---

## Step 1 — Let Claude talk to Cloudflare

The Cloudflare MCP server is already added to your Claude Code config. It is not
logged in yet. In Claude Code, type:

```
/mcp
```

Pick **cloudflare** from the list and choose to authenticate. A browser window opens,
Cloudflare asks if you want to allow access, and you say yes.

**You should see:** `cloudflare … ✔ Connected` when you run `/mcp` again.

From then on Claude can look things up in your account — which domains you have,
whether a deploy worked, what the DNS records are. It is a helper, not a replacement
for the steps below; the commands are still the reliable path.

---

## Step 2 — Log the deploy tool in

```sh
npx wrangler login
```

A browser window opens and asks you to allow Wrangler. Say yes.

**You should see:** `Successfully logged in.`

Check it picked the right account:

```sh
npx wrangler whoami
```

**You should see:** your email address and your account name.

---

## Step 3 — Make the website project

This creates an empty project in Cloudflare that the site will live in.

```sh
npx wrangler pages project create 258webco --production-branch main
```

**You should see:** a confirmation and a web address ending in `.pages.dev`. Write that
address down — it is your private preview link, and it keeps working forever, even
after the real domain is attached.

If it says the name is taken, pick another one (`258webco-site`) and use that name
everywhere below instead.

---

## Step 4 — Make the box that enquiries get stored in

When someone fills in the contact form, the message is saved here first. This is the
safety net: even if a notification fails, the message is not lost.

```sh
npx wrangler kv namespace create ENQUIRY
```

**You should see:** a short block of text containing an `id = "..."` with a long
string of letters and numbers.

Now open `wrangler.toml` in this project.

In **this master project**, the block is already filled in with the 258webco namespace
id, so there is nothing to uncomment. Check the `id` matches the one you were just given
(or skip this step if you did not create a new namespace).

In a **new client copy** made with `scripts/new_site.py`, find these three lines:

```toml
# [[kv_namespaces]]
# binding = "ENQUIRY"
# id = "<paste the id wrangler prints>"
```

Delete the `#` and the space at the start of each one, and replace
`<paste the id wrangler prints>` with the id you were just given. It should end up
looking like this, with your own id:

```toml
[[kv_namespaces]]
binding = "ENQUIRY"
id = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
```

### Turn intake on for this deployment

A namespace is somewhere to put enquiries; it is not permission to accept them. The
endpoint also requires an explicit variable, so that a copy of this project — which
starts without it — can never write into the namespace above:

```toml
[vars]
ENQUIRY_ENABLED = "true"
```

In `wrangler.toml`, this stays `"false"` in source control. Without `"true"` every submission is refused with a 503 and nothing is stored — safe, but silent to you.

**The form and the endpoint must be switched on together.** The page's form (`HUGO_PARAMS_FORMENABLED`) and the endpoint (`ENQUIRY_ENABLED`) are two settings. If the form is on but the endpoint is off, every visitor gets an error.

- **From GitHub (recommended):** run the deploy workflow with **Accept enquiries** ticked. It sets both in its own copy of the project and checks they agree before publishing. Nothing is committed.
- **From your own machine:** change `ENQUIRY_ENABLED` to `"true"`, build with `HUGO_PARAMS_FORMENABLED=true` (step 7), deploy (step 8), then change it back to `"false"` before you commit.

**The dashboard cannot turn this on.** When a Pages project has a `wrangler.toml`, Cloudflare treats that file as the only source of its variables and bindings. A value typed into **Settings → Variables and Secrets** does not override it. Whatever `wrangler.toml` says at deploy time is what the live site uses. Secrets, such as `NOTIFICATION_WEBHOOK`, are the exception: add them with `npx wrangler pages secret put NOTIFICATION_WEBHOOK --project-name 258webco`.

After deploying, check the live endpoint answers: a form submission should return a success page, not "could not confirm delivery". A 503 means intake is still off.

---

## Step 5 — Set up mail on the domain

258webco.com's mail currently points at an unused Microsoft 365 mailbox. You are
replacing it with Cloudflare Email Routing. Do these in order.

> **Note on Cloudflare UI layout:** Under the domain sidebar for **258webco.com**, the
> **Email** menu only lists DMARC and Security. Zone-level Email Routing is configured
> under **DNS**: go to **DNS** → **Records**, then click the **Email Routing** sub-tab at the top.

1. Account level → **Email** → **Email Routing** → **Destination addresses** → add
   `ryanleejwebdev@gmail.com`. Open Gmail and click Cloudflare's verification link.
   Nothing works until you click it.
2. In the left sidebar under **258webco.com**, click **DNS** → **Records**, then click
   the **Email Routing** sub-tab at the top.
3. Enable Email Routing and accept the DNS records it offers. This replaces the old Outlook MX record.
4. Add a route: `ryan@258webco.com` → your Gmail. Add a **catch-all** → your Gmail too,
   so nothing else bounces.
5. Send a message to `ryan@258webco.com` from another account and confirm it arrives.

Email Routing forwards all incoming mail sent to `ryan@258webco.com` (and the catch-all) directly to your Gmail.

*(Note: this is mail sent to your domain. The contact form does not use it. Cloudflare Pages cannot send email, so the contact form has no email path. Enquiries are stored in the `ENQUIRY` KV namespace for 90 days (`expirationTtl: 7776000`). For real-time alerts, add a `NOTIFICATION_WEBHOOK` secret (see step 4).)*

### Security & Privacy Protections

- **Rate Limiting:** `functions/api/contact.js` counts submissions per visitor in KV under `ratelimit:<hash>`, a SHA-256 hash of the IP address (never the raw address), and returns HTTP 429 after 5 enquiries within 10 minutes. Add a `RATE_LIMIT_SALT` secret so the hash cannot be reversed by trying every address. KV is eventually consistent, so this is a best-effort limit: a fast burst can exceed it. Counters share the `ENQUIRY` namespace unless you bind a separate `RATE_LIMIT` KV namespace, so list enquiries with `--prefix enquiry:` (as `scripts/enquiries.py` does).
- **Cross-site Posts:** a POST whose `Origin` header names another website is refused with HTTP 403.
- **No-JavaScript Errors:** visitors without JavaScript get a small HTML error page with a link back to the form, not raw JSON.
- **Data Retention TTL:** Enquiries are stored with a 90-day expiration TTL in KV to avoid hoarding personal information indefinitely.
- **Privacy Notice:** `/privacy/` tells visitors what the form stores, for how long, and how to ask for deletion. Keep it in step with any change to the form or these settings.
- **Webhook Delivery:** Setting the `NOTIFICATION_WEBHOOK` secret enables immediate POST notification forwarding for new submissions. A webhook that answers with an error status or takes more than 10 seconds counts as a failed delivery. Without a webhook, nobody is alerted: someone must check the KV store on a schedule.
- **Internal Artifact & Dotfile Protection:** `functions/_middleware.js` intercepts and returns HTTP 404 for `/.factory-build.json` and hidden dotfiles (the public `/.well-known/` folder stays reachable), backed by `static/_headers` with `X-Robots-Tag: noindex, nofollow, noarchive` and `Cache-Control: no-store`.

---

## Step 6 — Check it still works before anyone can see it

```sh
sh scripts/check_contact.sh
```

This builds the site, runs the contact form on your own machine, and sends fake
enquiries through it — a good one, a spam one, several broken ones, and one with the
settings missing.

**You should see:** `Contact endpoint checks passed: ...`

If you see `FAIL:` instead, stop and fix that before deploying. Nothing has gone live
at this point, so there is no rush and nothing is broken in public.

---

## Step 7 — Build the real site

The recommended way to publish is the GitHub workflow (see **Deploying from GitHub**
below). It does steps 7 and 8 for you. Use these two steps only to deploy from your own
machine.

Up to now every build has been a private draft: the contact form is switched off, and
every page tells search engines to ignore it. This command turns both of those off and
builds the public version. Before running it with the form on, set
`ENQUIRY_ENABLED = "true"` in `wrangler.toml` (step 4), or the live form refuses every
message. Set it back to `"false"` after deploying.

```sh
rm -rf public
HUGO_PARAMS_FORMENABLED=true HUGO_PARAMS_NOINDEX=false \
  python3 scripts/build.py --base-url https://258webco.com/
```

**You should see:** `Build and generated-output checks passed: public`

**Only run this when you actually want the site to be public and findable on Google.**
For a private preview, leave both settings off and just run `python3 scripts/build.py`.

---

## Step 8 — Send it to Cloudflare

```sh
npx wrangler pages deploy public --project-name 258webco
```

**You should see:** an upload progress list, then `Deployment complete!` and a
`.pages.dev` address (e.g. `https://258webco.pages.dev`).

Open that address in a browser. The site should be there. Go to the contact page and
send yourself a real test enquiry. Then check it arrived:

```sh
npx wrangler kv key list --binding ENQUIRY --remote
```

**You should see:** one entry, starting with `enquiry:` and today's date. To view the
submitted message content:

```sh
npx wrangler kv key get --binding ENQUIRY --remote "<paste-key-name>"
```

To list or export every stored enquiry later (read-only; needs `npx wrangler login`):

```sh
python3 scripts/enquiries.py list
python3 scripts/enquiries.py export --format csv -o enquiries.csv
```

An export contains personal data. Keep it out of the repository (`.gitignore` covers
`enquiries*.csv` and `enquiries*.json`) and delete it when you are done.

**Do not skip this test.** It is the only proof that a real customer's message reaches
you. A form that looks fine and quietly drops enquiries is worse than no form.

---

## Step 9 — Put your real domain on it

In the Cloudflare dashboard:
1. Go to **Workers & Pages** → click **258webco**.
2. Along the top tabs, click **Custom domains**.
3. Click the blue **Set up a custom domain** button.
4. Type `258webco.com` and click **Continue** → **Activate domain**.
5. *(Optional)* Click **Set up a custom domain** again and add `www.258webco.com`.

Because the domain is already in this same Cloudflare account, the DNS record is added
for you and the certificate is issued automatically. It usually takes a minute or two.

**You should see:** `258webco.com` listed as Active.

Then visit https://258webco.com and send one more test enquiry through the real
address, because that is the address customers will actually use.

---

## Deploying from GitHub

A push to `main` runs the checks only. It never deploys.

1. Once: in the repository, **Settings → Secrets and variables → Actions**, add
   `CLOUDFLARE_API_TOKEN` (with **Cloudflare Pages: Edit**) and `CLOUDFLARE_ACCOUNT_ID`.
2. Open **Actions → CI Quality Gates & Pages Deployment → Run workflow**.
3. Tick **Authorize production release**.
4. Tick **Accept enquiries** to publish with the contact form on. The workflow switches
   the form and the endpoint on together, checks they agree, and fails if they do not.
   Leave it unticked to publish with the form off.

**You should see:** both jobs green. Then do the live test enquiry from step 8.

To share a draft without touching the live site, run **Actions → Preview Deployment →
Run workflow** and pick `site` or `workshop`. It publishes to
`https://preview-site.258webco.pages.dev` or `https://preview-workshop.258webco.pages.dev`,
always with search engines blocked and the form off. Anyone with the link can open it; add
Cloudflare Access to `*.258webco.pages.dev` if the workshop must stay private.

---

## What to do when you change the site later

1. Edit content and settings.
2. `python3 scripts/build.py` and look at it locally.
3. When happy, push to `main`, then run the workflow as in **Deploying from GitHub**.

That is the whole loop. You never touch the Cloudflare dashboard again unless you are
adding a domain or changing how you get notified.

---

## If something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| `Refusing to write generated output` | The `public/` folder contains files the build does not own | `rm -rf public` and build again |
| `hugo: expected 0.166.0` | Wrong Hugo version installed | See README.md for the pinned install |
| `Configuration file for Pages projects does not support "send_email"` | Pages configuration does not support `send_email` in `wrangler.toml` (Workers-only) | Remove any `[[send_email]]` block; enquiries are stored in KV |
| Every live form submission fails with 503 | The form was built on, but `ENQUIRY_ENABLED` was `"false"` at deploy time | Deploy with the workflow's **Accept enquiries** ticked, or see step 4 |
| Form says "could not confirm delivery" | The endpoint refused the message | Run `sh scripts/check_contact.sh` to find out which check failed |
| Form works but no email received | The form never sends email; submissions are stored in KV | Query KV keys directly using step 8, or add a `NOTIFICATION_WEBHOOK` secret |
| `Authentication error` from wrangler | Login expired | `npx wrangler login` again |

---

## What this setup does not do

- It does not make backups of your enquiries anywhere except Cloudflare KV.
- It does not stop distributed spam beyond a simple hidden-field honeypot trap and IP rate limiting (5 requests per 10 minutes). If large-scale spam arrives, that is
  the point to add Turnstile — and doing so needs the security headers in
  `static/_headers` loosened, so it is a deliberate change, not a switch.
- It does not send a confirmation email to the person who filled in the form.
- Nothing here commits or pushes your code. Git is still yours to drive.
