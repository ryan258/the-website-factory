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
safety net: even if the notification email fails, the message is not lost.

```sh
npx wrangler kv namespace create ENQUIRY
```

**You should see:** a short block of text containing an `id = "..."` with a long
string of letters and numbers.

Now open `wrangler.toml` in this project. Find these three lines:

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

`wrangler.toml` is already filled in for this:

```toml
[[send_email]]
name = "EMAIL"
destination_address = "ryanleejwebdev@gmail.com"

[vars]
ENQUIRY_TO = "ryanleejwebdev@gmail.com"
ENQUIRY_FROM = "forms@258webco.com"
```

`ENQUIRY_TO` is the Gmail address, not `ryan@258webco.com` — Cloudflare delivers to
verified destination addresses, and `ryan@` is one it forwards *from*. `ENQUIRY_FROM`
needs no mailbox behind it; the catch-all covers any replies.

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

Up to now every build has been a private draft: the contact form is switched off, and
every page tells search engines to ignore it. This command turns both of those off and
builds the public version.

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
npx wrangler pages deploy
```

**You should see:** an upload progress list, then `Deployment complete!` and a
`.pages.dev` address.

Open that address in a browser. The site should be there. Go to the contact page and
send yourself a real test enquiry. Then check it arrived:

```sh
npx wrangler kv key list --binding ENQUIRY --remote
```

**You should see:** one entry, starting with `enquiry:` and today's date. If you chose
option B in step 5, you should also have an email.

**Do not skip this test.** It is the only proof that a real customer's message reaches
you. A form that looks fine and quietly drops enquiries is worse than no form.

---

## Step 9 — Put your real domain on it

In the Cloudflare dashboard: **Workers & Pages** → **258webco** → **Custom domains** →
**Set up a custom domain** → type `258webco.com` → confirm.

Because the domain is already in this same Cloudflare account, the DNS record is added
for you and the certificate is issued automatically. It usually takes a minute or two.

**You should see:** `258webco.com` listed as Active.

Then visit https://258webco.com and send one more test enquiry through the real
address, because that is the address customers will actually use.

---

## What to do when you change the site later

1. Edit content and settings.
2. `python3 scripts/build.py` and look at it locally.
3. When happy, repeat **step 7** and **step 8**.

That is the whole loop. You never touch the Cloudflare dashboard again unless you are
adding a domain or changing how you get notified.

---

## If something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| `Refusing to write generated output` | The `public/` folder contains files the build does not own | `rm -rf public` and build again |
| `hugo: expected 0.166.0` | Wrong Hugo version installed | See README.md for the pinned install |
| Form says "could not confirm delivery" | The endpoint refused the message | Run `sh scripts/check_contact.sh` to find out which check failed |
| Form works but no email | The destination address was never verified | Re-check step 5, choice B, point 3 |
| `Authentication error` from wrangler | Login expired | `npx wrangler login` again |

---

## What this setup does not do

- It does not make backups of your enquiries anywhere except Cloudflare KV.
- It does not stop spam beyond a simple hidden-field trap. If spam arrives, that is
  the point to add Turnstile — and doing so needs the security headers in
  `static/_headers` loosened, so it is a deliberate change, not a switch.
- It does not send a confirmation email to the person who filled in the form.
- Nothing here commits or pushes your code. Git is still yours to drive.
