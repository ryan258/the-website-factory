> Historical reference-demo evidence. Subsequent starter and factory changes are recorded in [starter-acceptance.md](starter-acceptance.md), [acceptance.md](acceptance.md), and [roadmap.md](../roadmap.md); these Lighthouse scores were not rerun for later milestones.

# Acceptance evidence — 2026-09-21

## Built and verified locally

- Five main pages, four fictional case-study detail pages, and a contact receipt page. The Hugo build reports 12 total outputs, including sitemap and robots; 10 are HTML pages.
- Hugo Extended 0.166.0 + Dart Sass 1.104.1. `hugo --minify --gc` completes with zero warnings after setting the documented PATH and writable temporary cache environment.
- Custom Sass modules with `@use`, responsive Grid/Flexbox, shared color/spacing variables, CSS custom properties, device-following dark mode, one breakpoint mixin, and a single fingerprinted CSS file with SRI.
- Latin-subset, self-hosted Inter variable font (43,620 bytes). SIL Open Font License included.
- Original case illustrations transformed by Hugo into WebP srcsets and JPEG fallbacks; explicit image dimensions and lazy loading. HTML/CSS hero adds no image request.
- Unique title, description, canonical URL, one H1, and `noindex` on all 10 HTML pages. Internal links resolve. Home Organization and Services FAQ JSON-LD, social card, favicon, touch icon, robots, and sitemap are generated.
- All five main pages and all four detail pages: axe WCAG A/AA tags report zero violations in light and dark modes. Each tested at widths 320, 600, 900, and 1200 with no document horizontal overflow.
- A 200% text-size probe at 600 pixels passes on all five main pages after fixing work-card result wrapping. This is a browser automation check, not a complete manual zoom/device acceptance.
- Keyboard probes: first focusable item is the skip link; Enter moves focus to main; mobile menu opens; FAQ disclosure toggles with Enter. A complete manual keyboard audit remains open.
- Form-enabled test build: simulated HTTP 503 preserves entered text, focuses the error, and permits retry; simulated HTTP 200 announces success and clears inputs. Form name and honeypot are posted. JavaScript-disabled HTML POST reaches a local mock. No message was sent to Netlify or any third party. Default production/local build keeps submission disabled.

## Home performance evidence

A focused Lighthouse mobile run against the local production build served by Python on port 14722 returned:

| Measurement | Result | Brief target |
| --- | --- | --- |
| Performance | 97 | 100 preferred, 95 minimum |
| Accessibility | 100 | 100 |
| Largest Contentful Paint | 1,429 ms | Under 1,500 ms |
| Cumulative Layout Shift | 0 | Under 0.05 |
| Transfer weight | 100,500 bytes (~100.5 KB) | Under 150 KB |
| Requests | 6 | At most 10 |
| CSS gzip | ~3.7 KB | Under 20 KB |
| JavaScript gzip | 615 bytes, Contact only | Under 5 KB |

The first run while other local browser work was in progress scored 88 (slow Speed Index). The isolated repeat scored 97. Scores are environment-sensitive; this is not a claim of stable hosted performance. Reports are `reports/home-lighthouse.html` and `.json`. Subsequent final edits only adjusted pricing copy/spacing and source formatting; all-page production performance still needs the documented audit.

Home has no executable JavaScript. Contact has one same-origin script. No external scripts, font requests, analytics, or trackers are present. The local server does not provide host Brotli behavior; verify it after deployment. Lighthouse does not establish field INP.

## Still open before full brief sign-off

- Run the supplied five-page mobile Lighthouse command and inspect every score, LCP, CLS, and network budget. The full run is left to the operator per the instruction to provide long-running commands rather than execute broad suites.
- Manual VoiceOver/NVDA, complete keyboard navigation, real-device layout, tap-target, and zoom acceptance. Automated axe passes do not establish full WCAG 2.2 AA conformance.
- Owner selection/approval of deployment, account, recipient, and any collection of submitted information; enable Netlify form detection and `HUGO_PARAMS_FORMENABLED=true` only afterward.
- Test an authorized synthetic submission on the live host, verify storage and notification delivery, and inspect no-JavaScript host error handling.
- Verify hosted HTTPS, compression, caching, CSP, canonical hostname, and performance. Keep the fictional domain untouched and `noindex` enabled.
- Git initialization, staging, commit, push, and publication remain owner-controlled. The folder started empty and outside a Git repository. No Git mutation was performed.

The site implementation is ready for review. External acceptance is not complete.
