# Happy Path: Deploying 258webco.com to Cloudflare

This is the fastest, cleanest path to get **258webco.com** live with working forms, durable KV storage, and Gmail notifications.

---

## 1. Cloudflare Dashboard: Email & Domain Setup

Cloudflare recently relocated zone-level Email Routing. Follow this exact path:

1. **Activate Email Routing**:
   - In Cloudflare, select domain **258webco.com**.
   - In the left sidebar, click **DNS** → **Records**.
   - Click the **Email Routing** sub-tab at the top of the records page.
   - Click **Enable Email Routing** and accept the suggested DNS records (replaces any previous MX records).
2. **Verify Destination Address**:
   - Add `ryanleejwebdev@gmail.com` as a destination address.
   - Open Gmail, find Cloudflare's verification email, and click the link. *(Required before notifications work)*.
3. **Configure Forwarding Rules**:
   - **Custom address**: `ryan@258webco.com` → forward to `ryanleejwebdev@gmail.com`.
   - **Catch-all rule**: forward all remaining `@258webco.com` mail to `ryanleejwebdev@gmail.com`.
4. **Smoke test email**:
   - Send an email from a phone or alternate account to `ryan@258webco.com`. Confirm it lands in your Gmail.

---

## 2. Cloudflare Project & Bindings Setup

Run these commands from your local project terminal (`~/Projects/the-website-factory`):

1. **Log in to Wrangler** (if not already authenticated):
   ```sh
   npx wrangler login
   ```

2. **Create the Pages Project**:
   ```sh
   npx wrangler pages project create 258webco --production-branch main
   ```

3. **Verify KV Namespace in `wrangler.toml`**:
   The KV namespace is configured in [wrangler.toml](wrangler.toml):
   ```toml
   [[kv_namespaces]]
   binding = "ENQUIRY"
   id = "ea6f0db631da4aaeb78c786a4581214c"
   ```
   *(Note: Cloudflare Pages configuration files reject `send_email` bindings — only Workers support that block in config files. The Pages Function at `functions/api/contact.js` automatically uses `ENQUIRY` KV for durable zero-loss enquiry storage).*

4. **Attach KV Binding in Cloudflare Pages Dashboard**:
   Go to Cloudflare Dashboard → **Workers & Pages** → **258webco** → **Settings** → **Bindings**:
   - Under **KV namespace bindings**, verify or add:
     - Variable name: `ENQUIRY`
     - KV namespace: `ENQUIRY` (`ea6f0db631da4aaeb78c786a4581214c`)

---

## 3. Verify Locally

Run the preflight suite to confirm the static site and the contact Pages Function pass all gates:

```sh
sh scripts/check_contact.sh
```

**Expected output:**
```
Contact endpoint checks passed: accepted, stored, redirected, rejected, and unconfigured paths.
```

---

## 4. Deploy

You can deploy immediately from the CLI, or let GitHub Actions deploy on push.

### Option A: Immediate CLI Deploy (Fastest)

Build the production release with form delivery enabled and search indexing turned on:

```sh
rm -rf public
HUGO_PARAMS_FORMENABLED=true HUGO_PARAMS_NOINDEX=false \
  python3 scripts/build.py --base-url https://258webco.com/
```

Deploy the verified build output (including `functions/api/contact.js`):

```sh
npx wrangler pages deploy public --project-name 258webco
```

### Option B: Automatic Deployment via GitHub Actions

1. In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions**.
2. Add these repository secrets:
   - `CLOUDFLARE_API_TOKEN`: Cloudflare API token with **Cloudflare Pages: Edit** permission.
   - `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare account ID (found in the dashboard URL or via `npx wrangler whoami`).
3. Commit and push to `main`. The `.github/workflows/deploy.yml` workflow will automatically setup Hugo Extended 0.166.0, compile Dart Sass 1.104.1, build the site, and deploy via Wrangler.

---

## 5. Attach Custom Domain (258webco.com)

1. In the Cloudflare dashboard, go to **Workers & Pages** → **258webco**.
2. Click the **Custom domains** tab along the top.
3. Click **Set up a custom domain**.
4. Type `258webco.com` and click **Continue** → **Activate domain**.
5. *(Optional)* Click **Set up a custom domain** again to add `www.258webco.com`.
6. Confirm DNS record activation. Cloudflare automatically handles the DNS routing and issues SSL/TLS certificates (typically active in 1–2 minutes).

---

## 6. Live Verification (Smoke Test)

1. Open `https://258webco.com/contact/` in your browser (or your preview at `https://258webco.pages.dev/contact/`).
2. Fill out and submit the form with a test message.
3. Confirm:
   - Success state appears on the page ("Thank you. Your enquiry has been received.").
   - Backup enquiry is recorded in Cloudflare KV:
     ```sh
     npx wrangler kv key list --binding ENQUIRY --remote
     ```
   - Inspect the stored message payload:
     ```sh
     npx wrangler kv key get --binding ENQUIRY --remote "<key-from-list-above>"
     ```
