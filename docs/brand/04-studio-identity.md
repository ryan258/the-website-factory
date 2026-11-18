# 258 Web Co. visual style guide

258 Web Co. is the service brand. Use the yellow factory silhouette, neutral page surfaces, and Inter typography already in the studio’s storefront. Carry the same visual language into proposals, examples, and the [studio campaign](05-launch-and-marketing.md).

## Logo and wordmark

The canonical mark pairs the square factory silhouette with the live-text wordmark **258 Web Co.** Use the [header mark geometry](../../layouts/partials/mark.html) for lockups and the [favicon](../../static/favicon.svg) for tiny square placements. The square sits to the left of the wordmark. At header size, use a 32 px mark, a gap of about 8 px, and a wordmark around 15 px in bold Inter. Keep at least a quarter of the mark width clear of neighboring content. Use the full lockup on a document cover, proposal, or first frame. The standalone mark fits a profile image, favicon, or small repeated placement with the brand already named.

Use the yellow-and-ink mark on light and dark surfaces. For one-ink production use an ink silhouette on white and preserve the building outline. Use approved artwork at its original aspect ratio and keep edges crisp. Avoid shadows, skewing, outline effects, and placing copy directly on a busy image. When mark and wordmark are adjacent, let the visible wordmark name the brand and mark the graphic decorative.

## Color

The storefront owns these values in [site data](../../data/site.yaml). When creating new material, check the source for changes and verify any new foreground and background pair.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| Canvas | `#FFFFFF` | `#14181F` | Main background |
| Alternate surface | `#F3F5F7` | `#1E242D` | Steps, examples, and grouped content |
| Main text | `#14181F` | `#F4F5F7` | Headlines and body |
| Secondary text | `#555D68` | `#B7C0CA` | Supporting information |
| Accent and accent text | `#FFC400` with `#14181F` | Same | Mark, primary action, and one focal detail |
| Links | `#0A5CD6` | `#8ABAFF` | Underlined links in running text |
| Dividers | `#D8DDE3` | `#434C59` | Decorative grouping |

Use Ink for text on yellow. Draw focus and required control boundaries with a color tested against neighboring surfaces. A decorative divider is insufficient as the sole visual boundary of an interactive element. Keep status visible in words and icon shape as well as color.

## Type, spacing, and layout

Use the repository’s [self-hosted Inter](../../static/fonts/inter-latin-variable.woff2) with a system sans-serif fallback. Keep its [font license](../../static/fonts/OFL-inter.txt) with redistributed font files. Use weights 700–800 for headlines and wordmarks, 550–650 for labels, and 400–500 for reading text. The recommendations below apply to new studio collateral. The workshop’s living guide documents exact storefront CSS values and usage.

| Element | Digital size | Layout |
| --- | --- | --- |
| Display | 36–64 px | One main statement, wrapped at a phrase boundary |
| Section heading | 24–32 px | Direct and sentence case |
| Body | 17–19 px | About 1.55 line height, roughly 45–70 characters per line |
| Supporting text | 14–16 px | Plain labels with generous space |
| Buttons | At least 44 px high | One filled primary action per section; visible focus and a meaningful label |

Start with an 8 px spacing rhythm. Use 16–24 px between closely related elements and 48–72 px between major sections on wide layouts. Tighten spacing and stack columns on mobile. Allow headings to reflow at zoom. Keep the important sentence, support copy, and first action in that reading order. For print, aim for 11 pt body type or larger, with margins that survive a standard office printer.

## Image and icon direction

Show real work, real people, or a real customer task when the necessary consent and usage rights are documented. Favor a clear focal point, real settings, daylight, and sufficient space for a mobile crop. Use a labeled fictional example when demonstrating a layout. Keep evidence labels in nearby live text so a cropped image can be understood in context. Redact customer and enquiry details from screenshots before use.

For an explanatory diagram, show a small number of steps in the order the reader performs them. For icons, use simple shapes with a consistent stroke and pair them with words for any action or status. Provide useful alternative text when the image contributes information and empty alternative text for decoration.

## Accessibility and application

- Use 4.5:1 or higher for ordinary text and 3:1 or higher for qualifying large text. Test controls and focus indicators against adjacent colors. Use the 44 px studio design target for major controls. [W3C contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [W3C non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html), [W3C target size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- Verify keyboard order, visible focus, readable zoom and reflow, and clear form feedback on the actual rendered page before publishing. Maintain headings, meaningful link names, and text outside artwork.
- Use the client’s identity in client sites. Choose the client’s own theme and type in the client copy. Check the complete palette and rendered output in both supported themes. Factory brand tokens belong to Factory materials.

## Ready artwork

- Studio logo exports include [color SVG](collateral/258webco-logo.svg), [transparent PNG](collateral/258webco-logo.png), [reverse SVG](collateral/258webco-logo-reversed.svg), and [one-ink SVG](collateral/258webco-logo-monochrome.svg). Use the reverse on dark backgrounds and the one-ink version on light backgrounds.

- [Studio one-sheet PDF](collateral/258webco-one-sheet.pdf) is ready for direct introductions. The [editable HTML](collateral/258webco-one-sheet.html) includes responsive and US Letter layouts.
- [Studio share card](collateral/258webco-share.png) is a 1200 × 630 image for link previews, direct messages, and social posts. Use the caption and alternative text in the [marketing playbook](05-launch-and-marketing.md).
