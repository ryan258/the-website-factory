# Happy Path: Putting 258webco.com Live

A short checklist. Each step links to the full instructions in
[docs/cloudflare-setup.md](docs/cloudflare-setup.md), which is the single deploy guide.

**A push to `main` does not deploy.** It only runs the checks. Deploying is a manual,
owner-only step (step 5).

---

## One-time setup

1. **Log Wrangler in** — `npx wrangler login` ([guide step 2](docs/cloudflare-setup.md#step-2--log-the-deploy-tool-in)).
2. **Create the Pages project** — `npx wrangler pages project create 258webco --production-branch main` ([guide step 3](docs/cloudflare-setup.md#step-3--make-the-website-project)).
3. **Check the enquiry store** — the `ENQUIRY` KV namespace id is already in `wrangler.toml`. Do not add it in the dashboard: `wrangler.toml` is the only place Cloudflare reads it from ([guide step 4](docs/cloudflare-setup.md#step-4--make-the-box-that-enquiries-get-stored-in)).
4. **Set up domain email forwarding** (optional, for mail sent to `@258webco.com`) ([guide step 5](docs/cloudflare-setup.md#step-5--set-up-mail-on-the-domain)). This is separate from the contact form.
5. **Add GitHub secrets** — in the repository, **Settings → Secrets and variables → Actions**, add `CLOUDFLARE_API_TOKEN` (with **Cloudflare Pages: Edit**) and `CLOUDFLARE_ACCOUNT_ID`.

## Every release

1. **Run the checks locally** — `sh scripts/check_contact.sh` should end with `Contact endpoint checks passed`.
2. **Push to `main`.** The **Verify Quality Gates** job must pass.
3. **Deploy** — in GitHub, open **Actions → CI Quality Gates & Pages Deployment → Run workflow**:
   - Tick **Authorize production release**.
   - Tick **Accept enquiries** to switch the contact form on. This turns on both the form and the endpoint together. Leave it unticked to publish with the form switched off.
4. **Attach the domain** (first release only) ([guide step 9](docs/cloudflare-setup.md#step-9--put-your-real-domain-on-it)).
5. **Send a real test enquiry** and confirm it is stored:
   ```sh
   npx wrangler kv key list --binding ENQUIRY --remote --prefix enquiry:
   ```

## Good to know

- The contact form stores enquiries in Cloudflare KV for 90 days. It does not send email: Cloudflare Pages cannot. For alerts, add a `NOTIFICATION_WEBHOOK` secret on the Pages project.
- The privacy notice at `/privacy/` describes exactly this. If you change what the form collects or where it goes, update that page too.
