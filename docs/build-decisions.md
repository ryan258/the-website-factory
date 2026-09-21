> Historical initial-build decisions. Current configuration and client-copy workflow are in [factory-guide.md](factory-guide.md), [starter-guide.md](starter-guide.md), and [roadmap.md](../roadmap.md).

# Build decisions

The supplied developer brief is the source of truth. This is a standalone fictional marketing site for busy small-business owners and marketing managers, demonstrating clear content and lean static delivery.

The creative sandbox, reusable implementation, and bounded static scope satisfy the kickstart premise and build gates. The supplied brief authorizes the build. No extra approval gates or unrelated personal skill installation are needed.

Voice: plain, specific, serious. Marketing copy explains a useful outcome; interface copy states the actual system state. Neither voice invents measured results, real clients, availability, or delivery confirmation.

Craft rules: five main pages plus four case-study detail pages; one primary contact route; fictional claims labeled at the point of use; no tracking or runtime third-party requests; failure retains form input; performance reports identify their measurement environment.

Netlify is the implementation default because native forms accept HTML POSTs without third-party scripts or a separate account. This is prepared configuration, not a deployment. The default build disables submission. An owner must enable form detection, choose who receives messages, set HUGO_PARAMS_FORMENABLED=true, and authorize a test before live delivery is accepted.

Hugo Extended 0.166.0 uses Dart Sass 1.104.1 through css.Sass. The brief's suggestion that Extended alone supports Dart Sass is inaccurate: @use requires the standalone compiler. Sass is still built by Hugo Pipes; Node is only used for optional QA.

Case artwork is original programmatically drawn illustration, rasterized as PNG sources and processed by Hugo into responsive WebP and JPEG. The home hero is lightweight HTML/CSS artwork and requires no image request. The font is Inter, Latin-subset variable WOFF2, with the SIL Open Font License included.

Base URL intentionally defaults to https://example.invalid/. Netlify builds derive canonical URLs from DEPLOY_PRIME_URL. No domain registration, DNS change, publication, push, staging, or commit is authorized by implementation.
