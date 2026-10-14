# Migrating a domain from GoDaddy to Cloudflare

For clients whose domain is at GoDaddy. It is the detailed version of step 2B in
[guide-to-hosting-on-cloudflare-on-the-cheap.md](guide-to-hosting-on-cloudflare-on-the-cheap.md).

Cloudflare's side was checked against Cloudflare's docs on 2026-10-14. **GoDaddy's own help pages
refused automated reading, so the GoDaddy menu names come from search summaries of GoDaddy's help
and third-party guides.** GoDaddy changes its screens often: trust what is on screen, and fix this
file when it differs.

## Two ways to move: pick one first

| | A. Nameservers only | B. Full transfer |
| --- | --- | --- |
| What moves | DNS only. The domain stays registered at GoDaddy. | DNS and the registration. |
| Time | Minutes to a day | About 5 to 10 days |
| Yearly bill | Still paid to GoDaddy at GoDaddy's price | Paid to Cloudflare, at cost |
| Needs | Nothing special | Domain older than 60 days, unlocked, auth code |
| Risk | Low | Low if done in order |

**Do A first, always.** It gets the site on Cloudflare and lets us check every record. B (the
transfer) needs A done anyway, because Cloudflare only transfers domains that already use its
nameservers. If the client is happy to keep paying GoDaddy, stop after A.

## Before touching anything (client and us, 15 minutes)

1. **Who is the registrant?** The client must own the account and the registrant email, and read that
   email. The auth code and approvals go there. If the previous web person's email is on the domain,
   fix that first. **Changing the registrant name, organization, or email starts a 60-day transfer
   lock**, so fix it early, not on transfer day.
2. **Find out what GoDaddy is doing for them.** Open the domain at GoDaddy and note:
   - **Email**: GoDaddy-hosted Microsoft 365 or Workspace mailboxes? Email forwarding? None?
   - **Website**: a GoDaddy site builder or hosting plan that is live today?
   - **Forwarding**: any domain forwarding or subdomain forwarding?
   - **DNSSEC**: on or off.
   - **Domain Protection**: a paid add-on that adds an identity check on transfer-out.
   - **Renewal date and auto-renew.**
3. **Screenshot or export every DNS record** from GoDaddy's DNS page. This is the rollback copy.
4. Confirm the domain is more than 60 days old and the owner details have not changed in 60 days.
   If it is expired, renew it at GoDaddy first; if it expired and was renewed, wait 45 days after the
   original expiration date.
5. Warn the client's bank that a charge from Cloudflare is coming. Cloudflare bills the transfer when the
   auth code is submitted.

## Stage 1 — Put DNS on Cloudflare (Option A)

1. **Turn DNSSEC off at GoDaddy** if it is on, then **wait 24 hours** before changing nameservers.
   Skipping the wait can leave the domain unreachable for some visitors. If DNSSEC was never on,
   skip this.
2. **Add the domain to the client's Cloudflare account** (Add a domain, Free plan). Cloudflare scans
   for existing records. **The scan is not guaranteed to find everything.** Compare it line by line
   with the GoDaddy export from step 3 above.
3. **Check these records in particular:**
   - `A` / `CNAME` for the bare domain and `www`. GoDaddy parked or forwarded domains can show a
     placeholder address. Use the site's real destination, not GoDaddy's.
   - `MX` for mail, and every `TXT` (SPF, Microsoft verification, DKIM, DMARC) and
     `CNAME` such as Microsoft's `autodiscover`. Mail breaks silently without these.
   - Records for other services (booking, newsletters, domain verification).
   - Set `MX` and mail-related `CNAME` records to **DNS only** (grey cloud), not proxied.
4. **Keep email working (pick the case that fits):**
   - **GoDaddy-hosted Microsoft 365 or Workspace:** recreate the records exactly as GoDaddy shows them.
     If the account was set up through GoDaddy's own admin, check that changing nameservers does not
     break the link to it; ask GoDaddy or Microsoft support if unsure. Do **not** turn on Cloudflare
     Email Routing, because it replaces the MX records.
   - **GoDaddy email forwarding only:** it will stop when GoDaddy no longer serves DNS. Set up
     Cloudflare Email Routing with the same rules before the switch (see the hosting guide).
   - **No email:** nothing to do.
5. **Write down the two nameservers** Cloudflare assigns.
6. **At GoDaddy:** open the domain → **DNS** → **Nameservers** → **Change** → **I'll use my own
   nameservers**. Enter the two Cloudflare names and save. GoDaddy may warn about this; accept it.
7. **Wait for Active.** In Cloudflare, the domain moves from Pending to Active, usually within minutes,
   up to 24 hours. If it is still Pending after 24 hours, check the nameservers and DNSSEC.
8. **Test before celebrating:** the website, `www`, and **send and receive a real email**. Keep GoDaddy
   subscriptions (email, hosting) running until everything works. Do not cancel anything yet.

**Rollback for Stage 1:** put GoDaddy's default nameservers back (GoDaddy's DNS page shows
the option to use GoDaddy nameservers). Nothing else was changed, so the old records resume.

Stop here if the client is staying at GoDaddy. The site can now go on Cloudflare Pages.

## Stage 2 — Transfer the registration (Option B)

Start only when Stage 1 is Active and working. Do this close together, because auth codes expire.

1. **Cloudflare side is ready:** the client's account has a verified email and a working payment method,
   and the domain is Active.
2. **Unlock the domain at GoDaddy.** On the domain page, find the **Domain Lock** toggle (in the
   Transfer / Registration Settings area) and turn it off.
3. **Get the authorization code.** On the domain page, **Additional Settings → Transfer domain away
   from GoDaddy**, then show and copy the **authorization code** (also called EPP or transfer code).
   - If **Domain Protection** is on, GoDaddy asks the owner to verify identity first: a code by SMS or
     authenticator app if two-step verification has been on for at least 24 hours, otherwise a one-time
     code sent to the registrant email.
   - GoDaddy also emails the code to the domain's administrative contact email.
   - Some guides say the transfer option is hidden while a Domain Protection plan is active. If you
     cannot find it, ask GoDaddy to remove or downgrade it, or look under the domain's protection
     settings.
4. **In Cloudflare:** **Transfer domains** → pick the domain → paste the code → confirm the registrant
   contact details → **Confirm transfer**. The charge is made now: one year of renewal for most
   `.com`, `.net` and `.org` domains, added to the current expiry date.
5. **Approve at GoDaddy.** GoDaddy emails the registrant a transfer confirmation. Approving it (link or
   GoDaddy dashboard) finishes the transfer sooner. If nobody approves, it completes on its own in
   about five days.
6. **Watch Cloudflare's Transfer domains page.** `Transfer in progress` for more than 24 hours usually
   means the domain is still locked at GoDaddy. `Transfer rejected`: choose **Retry**.
7. **When it finishes** (Cloudflare emails the owner), open the domain in Cloudflare and check:
   - auto-renew is on (domain management → auto-renew toggle),
   - DNSSEC: turn it back on in Cloudflare if the client wants it,
   - the website and email still work.
8. **Then, and only then,** cancel GoDaddy products the client no longer needs (hosting, email, site
   builder, protection plans). Let the client do this in their own GoDaddy account. The domain itself
   is no longer there.

## Timeline

| Day | What happens |
| --- | --- |
| 0 | Inventory, export records, fix registrant email if needed |
| 0 | Turn DNSSEC off at GoDaddy (if on) |
| 1 | Add to Cloudflare, check records, change nameservers, test site and mail |
| 2 | Unlock, auth code, submit the transfer, approve at GoDaddy |
| 2 to 7 | Wait. The domain keeps working the whole time. |
| Done | Auto-renew on, cancel unused GoDaddy products |

## When something is wrong

| What you see | Likely cause | What to do |
| --- | --- | --- |
| Cloudflare stays Pending | Nameservers not saved at GoDaddy, or DNSSEC still on | Re-check both. Wait the full 24 hours. |
| Site works, mail stopped | An `MX` or `TXT` record was missed | Add it from the GoDaddy export. Check the mail records are DNS only. |
| Site shows a GoDaddy parked page | A parked or forwarding placeholder record was copied | Replace the `A`/`CNAME` with the real destination. |
| No transfer option at GoDaddy | Domain Protection, a lock, or a 60-day block | See stage 2 step 3. Check for a recent owner-detail change. |
| Cloudflare will not accept the code | Wrong or expired code | Copy it fresh. Paste, do not type. |
| `Transfer in progress` for days | GoDaddy has not released it | Approve the confirmation email or the GoDaddy dashboard prompt. |
| Domain says it cannot be transferred | Under 60 days old, recent owner change, expired, or an unsupported name | Wait out the 60 days. Leave the transfer In Progress and Cloudflare waits. |
| Payment problem during transfer | Card declined after submitting | Fix the payment method, then retry. A failed payment can leave a transfer half-started. |

## Message to send the client

> We're moving your domain's settings to Cloudflare so your new site can run there. Nothing changes
> for your visitors. Please do not change anything in your GoDaddy account until we say so.
>
> Today I need you to: (1) tell me whether you use email at your domain, and with whom; (2) check that
> the owner email on your GoDaddy domain is one you read. Tomorrow I'll send two short steps to do in
> your GoDaddy account. Cancelling GoDaddy products comes last, after everything is checked.

## Checklist

- [ ] Registrant is the client, email is theirs, no recent change (60 days)
- [ ] Email and website at GoDaddy identified
- [ ] GoDaddy DNS records exported
- [ ] DNSSEC off (if it was on), 24 hours waited
- [ ] Cloudflare records match, mail records DNS only
- [ ] Nameservers changed, Cloudflare Active
- [ ] Site, `www` and real email send and receive tested
- [ ] Transfer submitted with a fresh code, approved at GoDaddy
- [ ] Transfer complete, auto-renew on, DNSSEC decision made
- [ ] Unused GoDaddy products cancelled by the client
