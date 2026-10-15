# Hosting a client site on Cloudflare, on the cheap

How we put a client's site on **their own** Cloudflare account, for about the price of the domain.

- **Part 1** is for the client. Send it as-is.
- **Part 2** is for us. It is the setup, done inside the client's account.
- **Part 3** is the handover outline.
- **Part 4** lists what is not built or not decided yet.

This is the agency process. It is not copied into client sites. The 258webco-specific runbook is
[cloudflare-setup.md](cloudflare-setup.md); client copies get their own generated version.

Cloudflare facts below were checked against Cloudflare's docs on 2026-10-14. Limits and menu names
move, so re-check before quoting a number to a client.

## What it costs

| Item | Cost | Notes |
| --- | --- | --- |
| Domain | Paid once a year, at cost | Cloudflare sells domains with no markup. The exact price shows before paying. Fees are not refundable. |
| Site hosting (Pages) | $0 | Static pages and images are free and unlimited. Free plan: 20,000 files per site, 25 MiB per file. |
| Contact form (Pages Function + KV) | $0 | Free plan: 100,000 function requests a day. KV allows 1,000 writes a day. |
| Email to `hello@theirdomain.com` | $0 | Email Routing forwards incoming mail to their existing inbox. Unlimited inbound. |
| Sending mail *from* their domain | Not free | See [Part 4](#part-4--not-built-or-not-decided). |

One enquiry costs two KV writes (the enquiry and the rate-limit counter), so the free plan covers
about 500 enquiries a day. That is far more than a small business receives.

---

## Part 1 — For the client

Plain steps. You keep ownership of everything: the account, the domain, and the bill.

### 1. Make a Cloudflare account

1. Go to <https://dash.cloudflare.com/sign-up> and sign up with **your own business email**
   (not ours). Use a password manager for the password.
2. Click the verification link Cloudflare emails you. Nothing works until you do.
3. Turn on two-factor sign-in: **Profile → Authentication**.
4. Add a payment method: **Manage Account → Billing → Payment info**. It is only charged for the
   domain and any paid extras you choose.

### 2A. Buy a new domain

1. In the dashboard, go to **Domains → Register Domains**.
2. Search for the name. Pick it and check the price shown.
3. Pay. Leave **auto-renew** on, or the domain can lapse and be lost.
4. Use your own name and address as the owner. The domain is registered to whoever you enter.

### 2B. Move a domain you already own

Do these in order. The order matters. The detailed GoDaddy version is
[migrating-domains-from-godaddy-to-cloudflare.md](migrating-domains-from-godaddy-to-cloudflare.md).

1. **If DNSSEC is on at your current registrar, turn it off, then wait 24 hours.** Skip this if it was
   never on.
2. **Add the domain to your Cloudflare account.** Dashboard → **Add a domain**, enter it, choose the
   **Free** plan. Cloudflare copies the existing DNS records, but may miss some. **Tell us before the
   next step**, so we can check the copy is complete (especially email records).
3. At your **current** registrar, change the nameservers to the two Cloudflare gives you. Wait for
   the dashboard to show the domain as **Active**. The site works from here, even if you stop.
4. At your current registrar: **unlock** the domain and ask for the **authorization (auth) code**.
   Codes expire, so do the next step the same day.
5. In Cloudflare, go to **Domains → Transfer Domains**, choose the domain, and paste the code.
   You are charged for one year's renewal when you submit it.
6. Your old registrar has up to five days to release the domain. Approving the transfer in their
   dashboard or email makes it faster.

Blocked? A domain cannot move within 60 days of being registered or having its owner details
changed (`.uk` is exempt). Leave it **In Progress** and Cloudflare waits. Nothing is lost: the
site works on the nameserver change alone, so the transfer can finish later.

### 3. Give us access

1. Dashboard → **Manage Account → Members → Invite**.
2. Enter our email: `<agency email>`.
3. Choose the **Administrator** role. Do **not** choose Super Administrator.
4. Click **Invite**. We accept it from our email.

You can see what we do and remove us at any time from the same page. We never need your password.

### 4. Send us these

- The domain name, and whether you bought it new or moved it.
- Which inbox should receive mail sent to `hello@yourdomain` (and any other addresses you want).
- Confirmation that you own the domain contact email, and that it is one you read. Renewal and
  transfer notices go there.

---

## Part 2 — For us: set up inside the client's account

**Before you start:** the client copy exists, builds, and its claims are confirmed. The form stays
off and the site stays `noindex` until the client signs off (see Part 3).
Never put the client's tokens, auth codes, or account ID in git.

### 0. Accept the invite and check access

1. Accept the invitation from the email. Switch to the client's account (account switcher, top left).
2. Check the role did its job:

```sh
npx wrangler login          # log in as yourself; you are a member of their account
npx wrangler whoami         # their account should be listed. Copy its account ID.
export CLOUDFLARE_ACCOUNT_ID=<their account id>   # this shell only, so commands target their account
```

3. If the account does not appear, or a step below says "permission denied", stop. Ask the client
   to check the invite role. Do not ask for their login.

### 1. Domain and DNS

- Bought on their account: it is already there. Open **Domains → Manage** and confirm auto-renew is on.
- Moved in: confirm every old DNS record exists in Cloudflare **before** the nameserver change goes
  live (A, CNAME, and especially MX and TXT for mail). Missing mail records mean lost mail.
- Never buy the domain on our own account "to save time". Moving it later needs both accounts to
  approve, DNSSEC off, a domain older than 10 days, and it locks the domain for 30 days.

### 2. Create the Pages project and the enquiry store

```sh
cd ../<client-copy>
npx wrangler pages project create <slug> --production-branch main
npx wrangler kv namespace create ENQUIRY
```

Put the namespace `id` in the client's `wrangler.toml` (uncomment the `[[kv_namespaces]]` block).
Keep `ENQUIRY_ENABLED = "false"` in source control. Details: the generated
`docs/cloudflare-setup.md` in the client copy.

### 3. Deploy a private draft first

```sh
python3 scripts/build.py && python3 scripts/check_site.py
npx wrangler pages deploy public --project-name <slug>
```

Send the client the `https://<slug>.pages.dev` link. The site is `noindex` and the form is off.
Do not attach the domain until the client has approved the content.

### 4. Go live

1. Content review is recorded: `./wf status`, then `./wf approve --by "<client name>"` after the
   client has actually confirmed the facts.
2. Turn the form on **together with** the endpoint (the build refuses an indexable release with the
   form off). Set `ENQUIRY_ENABLED = "true"` in the deploy checkout only, then:

```sh
rm -rf public
HUGO_PARAMS_FORMENABLED=true HUGO_PARAMS_NOINDEX=false \
  python3 scripts/build.py --base-url https://<their-domain>/
npx wrangler pages deploy public --project-name <slug>
```

   Set `ENQUIRY_ENABLED` back to `"false"` before committing.
3. Attach the domain: **Workers & Pages → <slug> → Custom domains → Set up a custom domain**. Add
   `www` too, and redirect one to the other. The certificate issues itself in a minute or two.
4. Check the live site: `python3 scripts/smoke.py https://<their-domain> --form on`.

### 5. Email: receive mail on their domain

Free forwarding to their existing inbox.

1. **Compute → Email Service → Email Routing** (use the dashboard search for "Email Routing" if the
   menu has moved again).
2. **Destination addresses**: add the client's inbox. They must click Cloudflare's verification
   link. Rules stay off until they do.
3. **Routing rules**: add `hello@` (and any others) → their inbox. Add a catch-all if they want one.
4. Accept the MX and SPF records Cloudflare offers. **If they already use a hosted mailbox
   (Google Workspace, Microsoft 365), skip this**: Email Routing would replace the mail records and
   break it.
5. Test from a different address than the destination. Some providers drop mail that appears to come
   from the account it is delivered to.

Replying: they reply from their inbox, so the reply shows their own address, not `hello@`. Tell them.
Replying *as* `hello@` needs a paid sender (Part 4).

### 6. The contact form

- The form stores each enquiry in the client's KV for 90 days. It sends no email.
- **Alerts:** add a webhook secret so the client hears about enquiries:
  `npx wrangler pages secret put NOTIFICATION_WEBHOOK --project-name <slug>`. Also set
  `RATE_LIMIT_SALT`. Without a webhook, nobody is told: the client would have to check KV.
- **Privacy page:** it must name the real business and match what the form stores and for how long.
  Update it before go-live.
- **Test it for real:** send one enquiry through the live domain, then
  `npx wrangler kv key list --binding ENQUIRY --remote --prefix enquiry:`. A form that looks fine and
  drops messages is worse than no form.
- Spam: honeypot and 5 per 10 minutes per visitor. Add Turnstile only if spam actually arrives; it
  needs the CSP loosened in `static/_headers`.

### 7. Images

**Default: images are part of the site.** Put them in `assets/images/`; the build makes WebP sizes and
Pages serves them from the site's own domain, free, with no extra setup. This is the right answer for
almost every client site.

Files over 25 MiB, or more than 20,000 files in total, do not fit on free Pages. **Cloudflare R2**
(10 GB free, no download fees) can hold them, served from a custom domain such as
`media.<their-domain>`. **The factory does not support this yet.** The site's security policy only
allows images from the site's own address, and the output check rejects images from another origin. See
[Part 4](#part-4--not-built-or-not-decided). Decided 2026-10-14: not supported. Do not set up R2 for a client; tell the client images ship with the site.

### 8. Deploying updates later

- **By hand:** `npx wrangler pages deploy public --project-name <slug>`, logged in as a member.
- **From GitHub:** the master's workflow is not copied to clients. A client repo needs its own
  `CLOUDFLARE_API_TOKEN` (create it in **their** account: Pages edit and KV edit only, nothing else)
  and `CLOUDFLARE_ACCOUNT_ID` as repository secrets. Never reuse our own token.

### Setup checklist

- [ ] Client account has 2FA and a payment method
- [ ] Domain in the client's account, auto-renew on, owner email is theirs
- [ ] We are Administrator, not Super Administrator
- [ ] Pages project + KV namespace created in **their** account (`whoami` showed theirs)
- [ ] Private `.pages.dev` draft approved
- [ ] Content review recorded; strict claims clean
- [ ] Privacy page updated
- [ ] Domain attached, certificate active, `www` redirect set
- [ ] Mail routes tested (or existing mailbox records left alone)
- [ ] Live test enquiry stored and the alert arrived
- [ ] `smoke.py` passes against the live domain

---

## Part 3 — Handover outline

One short document per client, in the client's own copy as `docs/handover.md`, written in plain
language. It extends what `./wf handover` already generates (build evidence, claims status, content
review). The sections below are what is still missing.

0. **Before writing it:** run `./wf eject ../<client>-delivery` and hand over that folder, not the factory copy
   (see the operator guide). Its README and `docs/cloudflare-setup.md` already say how to build and deploy.
1. **What you have.** One paragraph: the site address, what the pages are, what the form does.
2. **Who owns what.** A table: Cloudflare account, domain, mailbox, GitHub repo (if any), design files.
   Each row says owner, login email, and where the renewal date is.
3. **What it costs and when.** Domain renewal date and price, anything else that bills, and what happens
   if a payment fails.
4. **How to get your enquiries.** Where they arrive (webhook channel), how long they are kept (90 days),
   how to export them (`python3 scripts/enquiries.py export`, or ask us), and a note that the form sends
   no email.
5. **Email.** Which addresses forward where, and how to add one. The reply-from limitation.
6. **How to change things.** Small edits: what they may do themselves and how. Everything else: send us a
   request. Include the deploy steps for whoever does it.
7. **What we tested, and what we did not.** Link the generated acceptance report. State plainly that
   automated checks are not a full accessibility audit and that facts were confirmed by the client on
   `<date>`.
8. **Access after handover.** Our role is reduced or removed, and the date. If a care plan exists, it
   names the role we keep and what it is for.
9. **If something breaks.** Site down, form not delivering, domain warning, mail missing: the first thing
   to check and who to contact. Cloudflare status page link.
10. **Credentials checklist** (never in the document itself): the client holds the account login, 2FA
    recovery codes, and the registrar contact email. Our tokens and any wrangler login are revoked.
11. **Sign-off.** Client name, date, and "the site may be indexed" (the `noindex` decision).

Handover actions for us, in order: remove `RATE_LIMIT_SALT`/webhook copies from our notes, delete our
API tokens, confirm the client can deploy or has a care plan, then reduce our member role.

---

## Part 4 — Not built or not decided

1. **R2 images: decided against for now (2026-10-14).** Images stay in the site. Revisit when a client needs
   media over 25 MiB or 20,000 files. It would need a change to: `img-src` in `static/_headers` and the build's CSP, the
   cross-origin image check in `scripts/check_site.py`, and validation of media URLs in
   `scripts/factory.py`. Until then, images live in the site.
2. **Sending mail from the domain.** Cloudflare Email Sending needs the Workers Paid plan (3,000 messages a month included; it was
   a public beta at last check). Sending only to a *verified destination address* is free on every
   plan, so a contact-form alert email to the client's own inbox could be free, via Cloudflare's REST API
   from the form function. The current function cannot do this: the existing runbook says Pages cannot
   bind `send_email`, and nothing calls the REST API. Worth a spike if clients dislike webhooks.
3. **Menu names in the existing runbook.** [cloudflare-setup.md](cloudflare-setup.md)
   step 5 was updated to note Cloudflare's current location under **Compute → Email Service → Email Routing**
   (with the older DNS → Records path noted). Re-confirm against the live dashboard during onboarding.
4. **Client GitHub deploy workflow** does not exist for client copies.
5. **Account-level facts to verify on the first real client.** The exact permissions of the Administrator
   role (can it manage Registrar, DNS, Email Routing, Pages and KV?), and whether the invite screen offers
   narrower roles. If Administrator is too broad or too narrow, change Part 1, step 3.
6. **No cap on a runaway bill.** The free plan stops at its limits rather than billing. Moving a client to
   a paid Workers plan is their decision, in writing.
