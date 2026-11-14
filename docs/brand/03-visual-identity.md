# The Website Factory visual identity

Proposed system · November 12, 2026

[Open the visual brand board](assets/brand-board.html) · [Download the CSS tokens](assets/tokens.css) · [Download the JSON tokens](assets/tokens.json)

## Brand architecture

The Website Factory is the identity for the Hugo production toolkit. Use it on Factory documentation, tooling demonstrations, technical outreach, and any future product landing page. The full name is **The Website Factory**. Use **the Factory** in subsequent running copy once the name has been introduced.

**258 Web Co.** is the web studio identity used in the current storefront source. Its yellow accent, logo treatment, and site theme come from the configured preset and site data. A client site takes the client's identity. An operator can explain the production system in a proposal when it helps the client understand review and handoff. Keep one lead identity per asset. In a joint case study, show the delivering studio in the header and credit the production toolkit in ordinary text if the studio elects to do so. [258 Web Co. configuration](../../data/site.yaml) · [Factory and agency workflow](../agency-workflow.md)

## Visual idea

Two offset pages represent the relationship between a reviewed plan and a working page. The art is a schematic. Use it as an introduction to the workflow, then use a real labeled screenshot when a reader needs to see how the workshop behaves.

The system pairs warm paper and deep green ink with a concentrated lime accent. Inter gives the tool and its documentation the same typographic voice. The identity should feel precise enough to trust and calm enough to work in for an afternoon.

## Marks and exports

| Asset | Use | Files |
| --- | --- | --- |
| Primary horizontal lockup | Paper, Sage, or White surfaces. Use at the first introduction. | [Outlined SVG](assets/wordmark.svg) · [Transparent PNG](assets/wordmark.png) |
| Reversed horizontal lockup | Ink surfaces. For photographs, place it on a solid Ink plate. | [Outlined SVG](assets/wordmark-reversed.svg) · [Transparent PNG](assets/wordmark-reversed.png) |
| One-color lockup | One-ink printing or documents constrained to a single dark color. Use on a light ground. | [Outlined SVG](assets/wordmark-monochrome.svg) · [Transparent PNG](assets/wordmark-monochrome.png) |
| Compact page mark | Avatar, app icon, or favicon. Use beside visible product text when there is room. | [SVG](assets/mark.svg) · [512 × 512 PNG](assets/mark.png) |
| Workflow illustration | Large-scale hero, article heading, or share card. | [SVG](assets/page-illustration.svg) |
| Landscape share card | Link previews and wide announcements. | [1200 × 630 PNG](assets/social-share.png) · [Outlined SVG](assets/social-share.svg) |
| Square share card | Social posts and square directory placements. | [1080 × 1080 PNG](assets/social-square.png) · [Outlined SVG](assets/social-square.svg) |

The wordmarks use outlined letterforms and need no font installation. Choose the SVG for vector use. PNG lockups have 4× raster dimensions for embedding in documents or apps. The artwork exports use sRGB values. For print production, proof color on the intended stock using the printer's requested profile. Screen hex values give a source reference for that proof.

### Placement and scale

- For horizontal lockups, leave at least a quarter of the symbol tile's width clear on every side. At the master SVG's 56 px tile height, this is 14 px.
- Display horizontal lockups at **172 CSS px wide** or larger, with **215 px** preferred. Use at least **38 mm** wide in ordinary print. For narrower placements, use the compact mark and keep the full name available in neighboring text or in the control's accessible name.
- The compact mark works as a standalone **16 px** favicon. Use **24 px** or more in the interface. For circular avatar crops, preview the circle and add outer padding when needed to preserve the two page shapes.
- Keep the symbol's orientation and proportions. Use the supplied variants for dark surfaces and one-color work. Put the wordmark on a flat field when the backdrop competes with its shapes or letters.
- The image's accessible name is **The Website Factory** when it supplies the name. Use empty alt text beside visible equivalent text. A logo that is the only content of a link needs a name that identifies its destination.

## Color

| Token | Value | Role |
| --- | --- | --- |
| Ink | `#172522` | Main text, dark panels, and action outlines |
| Paper | `#F8F6EF` | Default canvas |
| Sage | `#E6EEE6` | Preview backgrounds and quiet grouping |
| Lime | `#D9F46C` | Primary action fill, mark, and illustration focal point |
| Pine | `#245C4C` | Links, focus indicators on light surfaces, and labeled diagram details |
| Muted | `#4B6259` | Secondary text on Paper, Sage, and White |
| Border | `#6F817A` | Boundaries where an interactive element needs a visible edge on a light surface |
| Divider | `#C9D4CB` | Decorative separators |
| White | `#FFFFFF` | Document surfaces and text on solid Pine when needed |

Use Paper as the dominant field. Group content in Sage and reserve Lime for one visually primary action or one illustration focal point per view. Give a Lime action a visible Ink outline on Paper. Use underlined Pine links on Paper, Sage, and White. On Ink use Sage or Paper text and an underlined Lime link. Pair color with explicit labels and shape when communicating a status such as “Needs review.”

### Measured combinations

Ratios use the repository's relative luminance calculation for solid sRGB colors. Text combinations listed here reach at least 4.5:1. Border combinations listed here reach at least 3:1 and are for interactive boundaries. [Contrast calculator](../../scripts/contrast.py) · [WCAG 2.2 contrast and non-text contrast](https://www.w3.org/TR/WCAG22/#distinguishable)

| Foreground | Background and contrast | Use |
| --- | --- | --- |
| Ink | Paper 14.67 · Sage 13.39 · White 15.86 · Lime 12.92 | Body, headings, action labels |
| Muted | Paper 6.09 · Sage 5.56 · White 6.58 | Supporting copy |
| Pine | Paper 7.17 · Sage 6.54 · White 7.75 | Underlined links and light-surface focus |
| Paper, Sage, Lime | Ink 14.67, 13.39, 12.92 respectively | Dark panels and dark-surface focus |
| White | Pine 7.75 | Inverse label |
| Border | Paper 3.81 · Sage 3.48 · White 4.12 | Input boundaries on light surfaces |

Lime on Paper is 1.14:1. Pair Lime controls with Ink text and outlines. Use Divider for decoration only. Recalculate combinations when a design introduces imagery, opacity, or a new background.

## Typography and composition

| Role | Specification |
| --- | --- |
| Display | Inter 720, `clamp(2.5rem, 6vw, 5rem)`, 1.04 line height, `-.045em` tracking |
| Section heading | Inter 700, `clamp(1.75rem, 3vw, 2.625rem)`, 1.12 line height, `-.03em` tracking |
| Body | Inter 400, `1.125rem`, 1.6 line height |
| Label and navigation | Inter 600, `0.9375rem`, 1.45 line height |
| Code and commands | `ui-monospace, SFMono-Regular, Consolas, monospace` at the surrounding text size |

Use the bundled [Inter variable WOFF2](../../static/fonts/inter-latin-variable.woff2) with `font-display: swap` and a system sans-serif fallback. The bundled file covers the Latin subset and weights 400–800. When extending language coverage, confirm the glyphs in use and include a compatible licensed font or appropriate fallback. Include the [SIL Open Font License](../../static/fonts/OFL.txt) when distributing the font file.

- Design around the `4, 8, 16, 24, 32, 48, 64, 96 px` spacing scale. Use 16–24 px gaps within a group and 48–96 px between major sections.
- Use a `70rem` maximum content frame and `65ch` prose measure. Pair the headline and an image in wide layouts and stack them in reading order on narrow screens.
- Use 8 px corner radii for controls and grouping. Use a border or a background change to group content. Reserve shadows for surfaces whose layering conveys a real interaction.
- On a product landing layout, give the first view a clear heading, a short audience description, and one next step. Follow with the workflow, a real example, and what a builder gets at handoff.
- In proposals and decks, use one headline per page or slide. Keep headings and body as selectable text. Use one image or diagram to support each point, and put source dates or provenance next to any evidence.

## Images, icons, and motion

**Product visuals.** Show a recognizable moment such as selecting a starter, checking a page plan, or reviewing the built output. Capture at a readable zoom level with sample content. Label the preset, viewport, and fictional nature where it could be mistaken for client work. Keep private contact details and credentials out of captures.

**Photography.** Use authentic, rights-cleared working images when they add context. Favor natural light, ordinary work surfaces, and crops that preserve the subject. For a client site, favor the client's own work and images with permission. Caption synthetic or illustrative imagery when a reader could reasonably infer it documents actual work.

**Icons and diagrams.** Prefer simple 24 px line icons with consistent weight and square proportions. Pair every unfamiliar action with a text label. Use the overlapping-page illustration as a brand device in a single focal area. Add a short text equivalent for diagrams that carry a process or decision. Decorative artwork can use empty alt text.

**Motion.** The base identity is still. For interactive feedback, use brief transitions where they clarify state and remove nonessential motion when the user requests reduced motion. Maintain visible keyboard focus and a design target of at least 44 × 44 CSS px for commonly used controls. Check responsive reflow at narrow widths and at increased zoom. [WCAG 2.2 keyboard, reflow, and target size criteria](https://www.w3.org/TR/WCAG22/)

## Apply the identity

- **Product introduction.** Use the primary lockup, Paper canvas, headline “From reviewed brief to Hugo site.” and the short description “A Hugo production toolkit for independent web builders.” A sample brief and rendered page give the pitch a concrete next step.
- **Share preview.** Use the wide PNG for preview metadata or a landscape header and the square PNG for a post. Keep the headline in the post or linked page as selectable text. Suggested image alt text is “The Website Factory. From reviewed brief to Hugo site. A Hugo production toolkit for independent web builders.”
- **Documentation.** Use the lockup once and prioritize copyable commands, explicit filenames, and clear steps. Use the monochrome lockup for one-color handoff documents.
- **Client handoff.** Use the delivering studio or client identity, whichever owns the document. Keep Factory attribution optional and describe the production workflow in text if it helps the recipient.
- **Reuse.** Open the brand board locally to review all assets. Its HTML provides editable copy and layout. Use the vector sources for artwork production. Import `tokens.json` into a token workflow or start from `tokens.css` and adjust its local font path when copying it outside this folder.

The brand board and artwork are reference materials kept alongside this guide. The existing [client theme and design primitives](../../assets/scss/abstracts/_variables.scss) serve configurable Hugo outputs. The Factory palette here is a proposed product identity with its own tokens.
