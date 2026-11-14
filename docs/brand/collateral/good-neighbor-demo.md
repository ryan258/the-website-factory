# Good Neighbor website walkthrough

**Fictional example.** Good Neighbor shows how a home-services business could explain its work, describe its coverage, and prepare customers to get in touch.

## A three-minute tour

1. **Start with the brief.** A homeowner needs to know whether the business can help with a small job. The business needs enough information to discuss the work. The page plan has Home, Services, About, and Contact.
2. **Show two page decisions.** The homepage distinguishes home upkeep, seasonal help, and one-off projects. The service-area section gives the owner a place to confirm towns and travel limits. Open the Contact page and point out what a useful first message would contain. The demo contact path is disabled.
3. **Explain the review.** Ask the owner to confirm actual services, coverage, response process, and site imagery. Point to the visible example notices. Those are the decisions that turn a sample into an accurate business site.
4. **Show the handoff.** The site’s content, templates, styles, and assets are in a separate project folder. The owner and builder agree on the contact route, who updates the site, and how to rebuild it. The short inventory below is an example of what a recipient can expect.

Open the local workshop with `./wf open --workshop`, then visit `/site-kit/local-service/`. Share this script or the one-sheet during a conversation. The workshop is a local operator preview.

## Sample handoff inventory

| Item | Example |
| --- | --- |
| Page copy and structure | `data/presets/local-service.json` |
| Site identity and shared details | `data/site.yaml` |
| Renderers and styling | `layouts/` and `assets/` |
| Fonts and other static files | `static/`, including font licenses |
| Build and ownership instructions | `README.md` and `docs/cloudflare-setup.md` in the delivery folder |
| Rebuild command | `hugo --minify` with the documented Hugo Extended and Dart Sass versions |
| Contact and publication | Draft. Confirm real coverage, contact details, and delivery before release. The owner chooses the destination and who handles updates. |

## Local verification record

On November 12, 2026, a fresh copy of the `local-service` preset was created in a temporary directory and ejected as a draft. The eject check reported that all 25 compared files matched between the factory build and plain Hugo. The run used Hugo Extended 0.166.0 and Dart Sass 1.104.1. The sample retained fictional content and draft settings. This check demonstrates local output parity for that source snapshot. Client approval, hosted behavior, contact delivery, and visitor outcomes each require their own evidence.

To recreate the draft in a new temporary directory from the factory checkout, put the project’s pinned Hugo Extended and Dart Sass on PATH, then run:

```sh
demo_dir="$(mktemp -d)"
./wf new "$demo_dir/good-neighbor" --name "Good Neighbor" --preset local-service &&
  (cd "$demo_dir/good-neighbor" && ./wf eject "$demo_dir/delivery" --draft)
```

The command prints the delivery folder path. The draft is for demonstrating the build and the source handoff.
