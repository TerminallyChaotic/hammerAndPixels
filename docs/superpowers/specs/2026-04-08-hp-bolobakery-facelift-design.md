# H&P Demo Site Facelift — Bolo Bakery

**Date:** 2026-04-08
**Status:** Design approved, pending implementation
**Scope:** First of a series of demo site facelifts for the Hammer & Pixels portfolio. This spec covers the global decisions for all demos plus the detailed brief for the first demo (Bolo Bakery). Each subsequent demo (coffee shop, restaurant, yoga gym) will get its own spec cycle.

## Background

The Hammer & Pixels portfolio (`portfolio/*.html`) contains four demo sites — `bolobakery`, `coffeeshop`, `restaurant`, `yogagym` — that are shown to prospective clients on the main H&P site. They are currently dated, feel template-y, and are missing content sections real businesses expect. They need a facelift to wow prospects and reinforce the H&P "no templates" motto.

The two "real lead" example sites (`mangiaficos` and `nonnies`) were moved out of `portfolio/` into `LeadExamples/` in the same session as this spec and are out of scope.

## Goals

A prospect lands on a demo, believes it is a real small business site, is impressed enough to want one like it, and clicks the H&P footer attribution to contact us.

## Non-goals

- Matching any shared visual language across demos. Each demo is its own world. The shared thread between demos is quality, not looks.
- Sourcing real photography. Photos will be added later by the site owner. Demos must look deliberate and polished with placeholder image states in the meantime.
- Building multi-page experiences where a single long-scroll page is sufficient (decided per demo).
- Parallax, scroll-scrub, or showreel animations. Motion is limited to tasteful micro-interactions.

## Global decisions (apply to every demo in the series)

### Visual strategy

Each demo is industry-authentic. The brief for each one is researched against actual winning modern sites in that industry, and the demo leans fully into those industry conventions. Zero shared visual tokens across demos.

### Technical baseline

- Static HTML/CSS/JS. No build step, no frameworks, no package manager.
- Mobile-first responsive. Breakpoints at ~720px and ~1100px.
- Semantic HTML throughout. WCAG AA color contrast. Real `alt` text on every image slot (for both placeholders and eventual real photos).
- Google Fonts via `<link>` tags, `font-display: swap`, system font fallbacks to avoid layout shift.
- Vanilla JS only. Scroll-reveal via `IntersectionObserver` (one-shot). `prefers-reduced-motion` disables all scroll animations.
- Lighthouse target: 95+ across performance, accessibility, best practices, SEO.
- Each demo's CSS is fully self-contained in its own per-demo stylesheet. No dependency on `../style.css`. This strengthens the "no templates" feel — demos share nothing, not even a reset.

### Image placeholder strategy

For every image slot that is waiting for a real photo, render a crafted placeholder block:

- Background: the demo's lightest neutral (e.g., cream for the bakery).
- Border: 1px dashed, in the demo's muted neutral (e.g., `--stone` for the bakery).
- Centered content: a small inline SVG camera icon above a tiny small-caps label reading `image pending`.
- The block fills the image slot at whatever aspect ratio the slot demands, so swapping in a real photo later is a one-line HTML change and does not affect layout.

The placeholder should read as deliberate and intentional — never as broken.

### Fake-data convention (applies to every demo in the series)

To keep demos obviously fictional and legally safe:

- **Do not name any real or plausible individuals or families.** No surnames, no personal first names attached to the business. Use generic collective references only — "the bakers", "the team", "your neighborhood [thing]", etc.
- **Every street address is `123 Main Street`.** The town, state, and zip can be anything that fits the demo (e.g., `123 Main Street, Collinsville, CT 06019`).
- **Every phone number is `(860) 123-4567`.** Corresponding `tel:` href is `tel:+18601234567`.
- **Every email is a generic handle** at the fake business domain (e.g., `hello@bolobakery.example`). Use `.example` TLD to guarantee it won't resolve.
- These rules override any copy suggestions elsewhere in the spec. Apply to all sections, including footers, contact forms, schema.org metadata, and any passing mentions in about/story sections.

### H&P attribution pattern

Every demo ends its footer with a `<div class="hp-attribution">` containing a single small muted centered line:

> *This is a demo site by Hammer & Pixels — web design & IT support in the Farmington Valley. Want a site like this for your business? [Let's talk →](../index.html#contact)*

Identical wording on every demo. No sticky banners, no modals, no top bars.

### File structure per demo

```
portfolio/
  <demo>.html             (rewritten)
  <demo>.css              (rewritten, self-contained)
  <demo>.js               (new, only if the demo has interactivity)
  <DemoName>Assets/       (new folder for per-demo SVG icons and placeholders)
```

No shared assets across demos.

### Delivery cadence

One demo at a time. Spec → implementation → user review on rendered output → merge. Next demo is its own spec cycle. Owner has said they do not need a specific delivery count; demos ship as they're ready.

## Demo 1: Bolo Bakery — design brief

### Concept

"Bolo" is Portuguese for "cake," so the demo leans into a **Portuguese-American family bakery in small-town Connecticut**. Three generations, one oven. Pastéis de nata, crusty pão, bolo de arroz, alongside American pastries. A neighborhood shop, not a chain. Just enough specificity to feel like a real place with an identity rather than generic filler — this is the "tasteful sprinkle of B" layered onto otherwise placeholder-flavored content.

### Brand direction

**Palette (warm, earthy, flour-dusted — morning light through a bakery window).**

| Token       | Hex       | Usage                              |
|-------------|-----------|------------------------------------|
| `--cream`   | `#F7F1E3` | page background, paper-soft        |
| `--crust`   | `#C77D3A` | terracotta accent, the color of a good crust |
| `--espresso`| `#3A2617` | headlines and body text            |
| `--butter`  | `#F1C76A` | small highlight accent (sparingly) |
| `--stone`   | `#A89885` | muted neutral, placeholders, dividers |

Optional subtle paper-grain texture on the body background (inline SVG noise at approximately 3% opacity).

**Type stack.**

- **Display:** DM Serif Display (Google Fonts). Warm humanist serif with generous curves. Reads as "earned" rather than luxury.
- **Body:** Inter (Google Fonts). Weight 400 for body, 500 for small caps and labels.
- **Accent:** Caveat (Google Fonts). Handwritten. Used at most twice on the page: the owner's signature at the end of the story section, and a small "today's bake" label above the product grid. Any more and it becomes tacky.

**Mood adjectives:** warm, unpretentious, heritage, neighborhood, hands-on, slow, nourishing.

### Page structure

Single long-scroll page with anchor navigation. Sections:

1. **Nav bar.**
   - Left: wordmark "Bolo" in DM Serif Display.
   - Right: anchor links — Story, Bakes, Visit, Contact.
   - Starts translucent over the hero. On scroll, transitions to cream-solid with a subtle shadow.
   - Mobile: horizontal menu collapses to a hamburger below 640px.

2. **Hero (full viewport height).**
   - Background: full-bleed image placeholder.
   - Centered content: headline "*Fresh bread, quiet mornings.*" in display serif, subhead in Inter, single CTA button "See Today's Bakes" anchoring to `#bakes`.
   - Subtle scroll-hint chevron at the bottom edge.
   - Headline fades in on page load.

3. **Story section.**
   - Two-column desktop layout, stacked on mobile.
   - Left column: vertical image placeholder ("the oven" or "hands kneading").
   - Right column: two short paragraphs of origin story — three generations, grandmother's recipes, Connecticut small town.
   - Ends with a Caveat-font signature line: *— The Ferreira Family*.

4. **Today's Bakes (`#bakes`).**
   - Small Caveat label above the grid: *today's bake*.
   - Grid of 6 cards, each with: square image placeholder, product name (DM Serif), one-line description (Inter), price.
   - Items: Pastéis de Nata, Country Loaf, Bolo de Arroz, Almond Croissant, Sourdough Miche, Broa de Milho.
   - Grid collapses to 3 columns at tablet, 1 column at mobile.

5. **Visit (`#visit`).**
   - Horizontal split on desktop.
   - Left: address, hours (easy-scan multiline), phone, "Walk-ins welcome" subtitle.
   - Right: placeholder for a static map image. Can be swapped for a real OSM or Google Maps embed later, or left as a placeholder if preferred.
   - Below the split: single italicized line — *We also do custom orders for weddings, birthdays, and celebrations.*

6. **Footer (`#contact` anchor).**
   - Cream background, espresso text.
   - Centered wordmark.
   - Social icon row (Instagram, Facebook) — placeholder SVGs.
   - Tagline: *Baked fresh daily since 1987.*
   - H&P attribution line at the very bottom, smaller and muted.

### Interactivity

Approach A (tasteful micro-motion only):

- Smooth anchor scroll on nav clicks.
- Fade-up on scroll for each section via `IntersectionObserver` (one-shot).
- Hero headline fades in on page load.
- Nav link hover: underline slides in from left.
- Bake card hover: slight lift and softer shadow.
- No carousels, parallax, lightboxes, or modals.

### Copy direction

- Short sentences. Quiet confidence. No hype.
- Zero emoji, zero exclamation marks.
- One or two Portuguese words sprinkled naturally, never translated inline — context carries them.
- No real or plausible person/family names. Signature line reads "— The bakers at Bolo" (collective, no surname).
- Address `123 Main Street, Collinsville, CT 06019` and phone `(860) 123-4567` per the global fake-data convention.

### Image placeholders (the slots that need photos later)

1. **Hero background** — full-bleed landscape. The tile-setter.
2. **Story portrait** — vertical, the oven or hands kneading.
3. **Today's Bakes** — 6 small square product shots (pastéis, loaf, bolo, croissant, miche, broa).
4. **Visit map** — optional. Can remain a placeholder or be swapped for an embed.

### Accessibility

- Visually-hidden "skip to content" link that becomes visible on keyboard focus.
- Semantic `<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`, `<article>` (bake cards).
- Focus ring on every interactive element: `outline: 2px solid var(--espresso); outline-offset: 2px`.
- `prefers-reduced-motion: reduce` disables all scroll animations — sections appear instantly.
- Color contrast checked against WCAG AA for every foreground/background combination.
- All image slots carry descriptive `alt` text — including the placeholders (e.g., `alt="Interior of Bolo Bakery"` for the hero).

### Files created or modified

- `portfolio/bolobakery.html` — rewritten from scratch.
- `portfolio/bolobakery.css` — rewritten from scratch, self-contained.
- `portfolio/bolobakery.js` — new, small script for scroll-reveal and nav scroll effect.
- `portfolio/BoloBakeryAssets/` — new folder containing inline SVG icons (camera placeholder icon, social icons, optional paper-grain texture). No photos yet.

### Success criteria for this demo

- Renders correctly on mobile, tablet, and desktop (tested at 375px, 768px, 1280px, 1920px).
- Lighthouse score 95+ across performance, accessibility, best practices, SEO when audited locally.
- Every image slot reads as an intentional placeholder, not a broken image.
- The H&P footer attribution is present and links to `../index.html#contact`.
- All content is in place; no lorem ipsum anywhere.
- Passes a manual "real or fake?" read — a stranger skimming it should think it's a real small bakery site before noticing the footer line.

## Out of scope for this spec

- Coffee shop, restaurant, and yoga gym demos. Each gets its own spec cycle.
- Photo sourcing. Done later by the site owner.
- Deployment mechanics. The H&P site auto-deploys on push to `main`, so shipping is a normal git commit + push.
- The `portfolio/index.html` landing page. Out of scope unless the owner explicitly pulls it in later.
