# Bolo Bakery Facelift Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `portfolio/bolobakery.html`, `portfolio/bolobakery.css`, and add `portfolio/bolobakery.js` from scratch as a polished, industry-authentic single-page demo site for a fictional Portuguese-American family bakery, ready for the H&P main portfolio.

**Architecture:** Static HTML/CSS/JS, no build step, no frameworks. Self-contained per-demo CSS (no `../style.css` dependency). Semantic HTML, mobile-first responsive, WCAG AA accessible, with crafted image placeholders pending real photo sourcing later. Vanilla JS via `IntersectionObserver` for scroll-reveal and a scroll-state class on the nav. Builds section by section with a commit after each section so any mistake is cheap to revert.

**Tech Stack:** HTML5, CSS3 (custom properties, grid, flexbox), vanilla ES6+ JS, Google Fonts (DM Serif Display, Inter, Caveat), inline SVG icons.

**Source spec:** `docs/superpowers/specs/2026-04-08-hp-bolobakery-facelift-design.md` — read before starting if any task's rationale is unclear.

---

## File Structure

```
portfolio/
  bolobakery.html                     (rewritten from scratch)
  bolobakery.css                      (rewritten from scratch, self-contained)
  bolobakery.js                       (new file, ~40 lines)
  BoloBakeryAssets/                   (new folder)
    camera-placeholder.svg            (icon for image-pending blocks)
    instagram.svg                     (footer social icon)
    facebook.svg                      (footer social icon)
    chevron-down.svg                  (hero scroll hint)
    paper-grain.svg                   (body background texture at 3% opacity)
```

**Responsibilities:**
- `bolobakery.html` — semantic page structure, content, nav, no styling.
- `bolobakery.css` — all visual presentation, fully self-contained. Organized top-to-bottom: custom properties, reset, base typography, layout helpers, then per-section rules in the same order as the HTML sections.
- `bolobakery.js` — two behaviors only: scroll-reveal on `[data-reveal]` elements via `IntersectionObserver`, and toggling `.scrolled` on the nav once the window scrolls past the hero.
- `BoloBakeryAssets/` — only inline-able SVG files for icons and textures. Zero photos; photos come later.

---

## Task 1: Create asset folder with SVG icons

**Files:**
- Create: `portfolio/BoloBakeryAssets/camera-placeholder.svg`
- Create: `portfolio/BoloBakeryAssets/instagram.svg`
- Create: `portfolio/BoloBakeryAssets/facebook.svg`
- Create: `portfolio/BoloBakeryAssets/chevron-down.svg`
- Create: `portfolio/BoloBakeryAssets/paper-grain.svg`

- [ ] **Step 1: Create the camera placeholder icon**

Write `portfolio/BoloBakeryAssets/camera-placeholder.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
  <circle cx="12" cy="13" r="4"/>
</svg>
```

- [ ] **Step 2: Create the Instagram icon**

Write `portfolio/BoloBakeryAssets/instagram.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
  <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
  <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
</svg>
```

- [ ] **Step 3: Create the Facebook icon**

Write `portfolio/BoloBakeryAssets/facebook.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
</svg>
```

- [ ] **Step 4: Create the chevron-down scroll hint**

Write `portfolio/BoloBakeryAssets/chevron-down.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="6 9 12 15 18 9"/>
</svg>
```

- [ ] **Step 5: Create the paper grain texture**

Write `portfolio/BoloBakeryAssets/paper-grain.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
  <filter id="noise">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
  <rect width="100%" height="100%" filter="url(#noise)" opacity="0.4"/>
</svg>
```

- [ ] **Step 6: Verify all 5 files exist**

Run: `ls portfolio/BoloBakeryAssets/`
Expected output: 5 files listed — `camera-placeholder.svg`, `chevron-down.svg`, `facebook.svg`, `instagram.svg`, `paper-grain.svg`.

- [ ] **Step 7: Commit**

```bash
rm -f .git/index.lock
git add portfolio/BoloBakeryAssets/
git commit -m "feat(bolobakery): add per-demo SVG icon set and paper-grain texture"
```

---

## Task 2: Scaffold the CSS foundation

**Files:**
- Create: `portfolio/bolobakery.css` (starts fresh; earlier file will be fully replaced by this series of tasks)

- [ ] **Step 1: Replace `portfolio/bolobakery.css` with the foundation**

Write `portfolio/bolobakery.css` (overwrites any existing file):

```css
/* =========================================================================
   Bolo Bakery — self-contained stylesheet
   ========================================================================= */

/* ----- Design tokens ----- */
:root {
  --cream: #F7F1E3;
  --crust: #C77D3A;
  --crust-dark: #A5622A;
  --espresso: #3A2617;
  --butter: #F1C76A;
  --stone: #A89885;
  --stone-light: #D6CEC2;

  --font-display: "DM Serif Display", Georgia, "Times New Roman", serif;
  --font-body: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-hand: "Caveat", "Brush Script MT", cursive;

  --max-width: 1200px;
  --gutter: clamp(1.25rem, 4vw, 3rem);
  --section-pad: clamp(4rem, 9vw, 7rem);

  --radius-sm: 6px;
  --radius-md: 12px;

  --shadow-soft: 0 2px 14px rgba(58, 38, 23, 0.08);
  --shadow-lift: 0 10px 30px rgba(58, 38, 23, 0.14);

  --transition: 280ms cubic-bezier(0.22, 0.61, 0.36, 1);
}

/* ----- Reset ----- */
*, *::before, *::after { box-sizing: border-box; }
html, body, h1, h2, h3, h4, p, ul, ol, figure { margin: 0; padding: 0; }
ul, ol { list-style: none; }
img, svg { display: block; max-width: 100%; height: auto; }
a { color: inherit; text-decoration: none; }
button { font: inherit; color: inherit; background: none; border: 0; cursor: pointer; }

/* ----- Base ----- */
html {
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
body {
  font-family: var(--font-body);
  color: var(--espresso);
  background-color: var(--cream);
  background-image: url("BoloBakeryAssets/paper-grain.svg");
  background-size: 200px 200px;
  background-repeat: repeat;
  line-height: 1.6;
  font-size: clamp(1rem, 0.95rem + 0.2vw, 1.0625rem);
}
body::before {
  /* Overlay softens the grain texture to ~3% effective opacity. */
  content: "";
  position: fixed;
  inset: 0;
  background: var(--cream);
  opacity: 0.97;
  pointer-events: none;
  z-index: -1;
}

h1, h2, h3 {
  font-family: var(--font-display);
  font-weight: 400;
  color: var(--espresso);
  line-height: 1.15;
}
h1 { font-size: clamp(2.5rem, 5.5vw, 4.5rem); }
h2 { font-size: clamp(2rem, 3.8vw, 3rem); }
h3 { font-size: clamp(1.25rem, 1.6vw, 1.5rem); }

.hand {
  font-family: var(--font-hand);
  font-weight: 500;
  color: var(--crust-dark);
  font-size: 1.75em;
  line-height: 1;
}

.label {
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--stone);
}

/* ----- Layout helpers ----- */
.container {
  width: 100%;
  max-width: var(--max-width);
  margin: 0 auto;
  padding-left: var(--gutter);
  padding-right: var(--gutter);
}
main > section { padding-block: var(--section-pad); }

/* ----- Skip link ----- */
.skip-link {
  position: absolute;
  left: 1rem;
  top: -3rem;
  background: var(--espresso);
  color: var(--cream);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  font-weight: 500;
  z-index: 100;
  transition: top var(--transition);
}
.skip-link:focus { top: 1rem; }

/* ----- Focus ring ----- */
:focus-visible {
  outline: 2px solid var(--espresso);
  outline-offset: 3px;
  border-radius: 2px;
}

/* ----- Image placeholder block ----- */
.img-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  width: 100%;
  height: 100%;
  background: var(--cream);
  border: 1px dashed var(--stone);
  border-radius: var(--radius-sm);
  color: var(--stone);
  padding: 1.5rem;
  min-height: 160px;
}
.img-placeholder svg { width: 36px; height: 36px; opacity: 0.8; }
.img-placeholder span {
  font-size: 0.6875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.2em;
}

/* ----- Reveal animation (JS-triggered) ----- */
[data-reveal] {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 700ms ease, transform 700ms cubic-bezier(0.22, 0.61, 0.36, 1);
}
[data-reveal].is-visible {
  opacity: 1;
  transform: none;
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  [data-reveal] { opacity: 1; transform: none; transition: none; }
}
```

- [ ] **Step 2: Verify the CSS file loads without syntax errors**

Run: `head -5 portfolio/bolobakery.css && wc -l portfolio/bolobakery.css`
Expected: first 5 lines show the header comment and `:root {`. Line count around 130.

- [ ] **Step 3: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.css
git commit -m "feat(bolobakery): scaffold self-contained CSS foundation (tokens, reset, helpers)"
```

---

## Task 3: Scaffold the HTML skeleton

**Files:**
- Create: `portfolio/bolobakery.html` (fully replaces any existing file)

- [ ] **Step 1: Replace `portfolio/bolobakery.html` with the skeleton**

Write `portfolio/bolobakery.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Bolo Bakery — a Portuguese-American family bakery in small-town Connecticut. Fresh bread, quiet mornings.">
  <title>Bolo Bakery — Fresh bread, quiet mornings.</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@500&family=DM+Serif+Display&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="bolobakery.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <!-- NAV — Task 4 fills this in -->

  <main id="main">

    <!-- HERO — Task 5 fills this in -->

    <!-- STORY — Task 6 fills this in -->

    <!-- BAKES — Task 7 fills this in -->

    <!-- VISIT — Task 8 fills this in -->

  </main>

  <!-- FOOTER — Task 9 fills this in -->

  <script src="bolobakery.js" defer></script>
</body>
</html>
```

- [ ] **Step 2: Verify HTML is well-formed and loads the stylesheet**

Run: `grep -c 'bolobakery.css' portfolio/bolobakery.html && grep -c 'Google Fonts' portfolio/bolobakery.html || grep -c 'fonts.googleapis.com' portfolio/bolobakery.html`
Expected: `1` for the stylesheet, `1` for the font link.

- [ ] **Step 3: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.html
git commit -m "feat(bolobakery): scaffold semantic HTML skeleton with skip link and font imports"
```

---

## Task 4: Build the nav bar

**Files:**
- Modify: `portfolio/bolobakery.html` (replace the `<!-- NAV -->` placeholder)
- Modify: `portfolio/bolobakery.css` (append nav styles)

- [ ] **Step 1: Add the nav HTML**

In `portfolio/bolobakery.html`, replace the `<!-- NAV — Task 4 fills this in -->` comment with:

```html
  <header class="site-nav" id="site-nav">
    <div class="container nav-inner">
      <a class="brand" href="#main" aria-label="Bolo Bakery — home">Bolo</a>
      <nav aria-label="Main navigation">
        <ul class="nav-links">
          <li><a href="#story">Story</a></li>
          <li><a href="#bakes">Bakes</a></li>
          <li><a href="#visit">Visit</a></li>
          <li><a href="#contact">Contact</a></li>
        </ul>
      </nav>
      <button class="nav-toggle" id="nav-toggle" aria-expanded="false" aria-controls="nav-links-mobile" aria-label="Open menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </header>
```

- [ ] **Step 2: Append nav styles to `portfolio/bolobakery.css`**

Append to the end of `portfolio/bolobakery.css`:

```css
/* ----- Nav ----- */
.site-nav {
  position: fixed;
  inset: 0 0 auto 0;
  z-index: 50;
  background: transparent;
  transition: background-color var(--transition), box-shadow var(--transition);
}
.site-nav.scrolled {
  background: var(--cream);
  box-shadow: var(--shadow-soft);
}
.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-block: 1.25rem;
}
.brand {
  font-family: var(--font-display);
  font-size: 1.75rem;
  color: var(--cream);
  transition: color var(--transition);
}
.site-nav.scrolled .brand { color: var(--espresso); }

.nav-links {
  display: flex;
  gap: 2.25rem;
  font-size: 0.9375rem;
  font-weight: 500;
}
.nav-links a {
  color: var(--cream);
  position: relative;
  padding-block: 0.25rem;
  transition: color var(--transition);
}
.nav-links a::after {
  content: "";
  position: absolute;
  left: 0;
  right: 100%;
  bottom: 0;
  height: 1px;
  background: currentColor;
  transition: right var(--transition);
}
.nav-links a:hover::after,
.nav-links a:focus-visible::after { right: 0; }
.site-nav.scrolled .nav-links a { color: var(--espresso); }

.nav-toggle {
  display: none;
  width: 44px;
  height: 44px;
  position: relative;
}
.nav-toggle span {
  position: absolute;
  left: 10px;
  right: 10px;
  height: 2px;
  background: var(--cream);
  transition: transform var(--transition), opacity var(--transition), top var(--transition), background var(--transition);
}
.nav-toggle span:nth-child(1) { top: 14px; }
.nav-toggle span:nth-child(2) { top: 21px; }
.nav-toggle span:nth-child(3) { top: 28px; }
.site-nav.scrolled .nav-toggle span { background: var(--espresso); }

@media (max-width: 639px) {
  .nav-links { display: none; }
  .nav-toggle { display: block; }
  .site-nav.menu-open { background: var(--cream); box-shadow: var(--shadow-soft); }
  .site-nav.menu-open .nav-links {
    display: flex;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    flex-direction: column;
    gap: 0;
    background: var(--cream);
    padding: 0.5rem 0 1.25rem;
    border-top: 1px solid var(--stone-light);
  }
  .site-nav.menu-open .nav-links a {
    display: block;
    padding: 0.75rem var(--gutter);
    color: var(--espresso);
  }
  .site-nav.menu-open .nav-toggle span { background: var(--espresso); }
  .site-nav.menu-open .nav-toggle span:nth-child(1) { top: 21px; transform: rotate(45deg); }
  .site-nav.menu-open .nav-toggle span:nth-child(2) { opacity: 0; }
  .site-nav.menu-open .nav-toggle span:nth-child(3) { top: 21px; transform: rotate(-45deg); }
}
```

- [ ] **Step 3: Verify the HTML placeholder is gone and the nav renders in the source**

Run: `grep -c 'NAV — Task 4' portfolio/bolobakery.html && grep -c 'site-nav' portfolio/bolobakery.html`
Expected: `0` for the placeholder (removed), `1` or more for `site-nav`.

- [ ] **Step 4: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.html portfolio/bolobakery.css
git commit -m "feat(bolobakery): add fixed nav with scroll state and mobile menu"
```

---

## Task 5: Build the hero section

**Files:**
- Modify: `portfolio/bolobakery.html` (replace the `<!-- HERO -->` placeholder)
- Modify: `portfolio/bolobakery.css` (append hero styles)

- [ ] **Step 1: Add the hero HTML**

In `portfolio/bolobakery.html`, replace the `<!-- HERO — Task 5 fills this in -->` comment with:

```html
    <section class="hero" aria-labelledby="hero-heading">
      <div class="hero-media" aria-hidden="true">
        <div class="img-placeholder hero-placeholder">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
          <span>image pending</span>
        </div>
        <div class="hero-tint"></div>
      </div>
      <div class="container hero-content">
        <p class="label hero-eyebrow" data-reveal>Farmington Valley · Since 1987</p>
        <h1 id="hero-heading" data-reveal>Fresh bread,<br>quiet mornings.</h1>
        <p class="hero-sub" data-reveal>A small Portuguese-American bakery in small-town Connecticut. Three generations, one oven, and the smell of something good in the air before the sun is up.</p>
        <a class="btn-primary" href="#bakes" data-reveal>See today's bakes</a>
      </div>
      <a class="hero-scroll-hint" href="#story" aria-label="Scroll to story">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
      </a>
    </section>
```

- [ ] **Step 2: Append hero styles to `portfolio/bolobakery.css`**

Append to the end of `portfolio/bolobakery.css`:

```css
/* ----- Hero ----- */
.hero {
  position: relative;
  min-height: 100vh;
  padding-block: 0 !important;
  display: flex;
  align-items: center;
  overflow: hidden;
}
.hero-media {
  position: absolute;
  inset: 0;
  z-index: 0;
}
.hero-media .img-placeholder.hero-placeholder {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 0;
  background: linear-gradient(140deg, #D4BFA5 0%, #A87C4F 55%, #6B4328 100%);
  color: var(--cream);
  min-height: 0;
}
.hero-media .hero-placeholder svg { opacity: 0.55; width: 48px; height: 48px; }
.hero-media .hero-placeholder span { color: var(--cream); opacity: 0.7; }
.hero-tint {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(58, 38, 23, 0.35) 0%, rgba(58, 38, 23, 0.65) 100%);
}
.hero-content {
  position: relative;
  z-index: 1;
  color: var(--cream);
  max-width: 720px;
  padding-block: 8rem 4rem;
}
.hero-eyebrow {
  color: var(--butter);
  margin-bottom: 1.5rem;
}
.hero h1 {
  color: var(--cream);
  margin-bottom: 1.25rem;
}
.hero-sub {
  font-size: clamp(1.05rem, 1.2vw, 1.2rem);
  max-width: 48ch;
  margin-bottom: 2.25rem;
  opacity: 0.92;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.95rem 1.75rem;
  background: var(--crust);
  color: var(--cream);
  font-weight: 500;
  font-size: 0.9375rem;
  letter-spacing: 0.02em;
  border-radius: 999px;
  transition: background var(--transition), transform var(--transition), box-shadow var(--transition);
  box-shadow: var(--shadow-soft);
}
.btn-primary:hover,
.btn-primary:focus-visible {
  background: var(--crust-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lift);
}

.hero-scroll-hint {
  position: absolute;
  left: 50%;
  bottom: 2rem;
  transform: translateX(-50%);
  width: 36px;
  height: 36px;
  color: var(--cream);
  opacity: 0.7;
  animation: nudge 2.4s ease-in-out infinite;
}
.hero-scroll-hint svg { width: 100%; height: 100%; }
@keyframes nudge {
  0%, 100% { transform: translate(-50%, 0); opacity: 0.55; }
  50%      { transform: translate(-50%, 8px); opacity: 0.9; }
}
@media (prefers-reduced-motion: reduce) {
  .hero-scroll-hint { animation: none; }
}
```

- [ ] **Step 3: Verify hero is in place**

Run: `grep -c 'HERO — Task 5' portfolio/bolobakery.html && grep -c 'class="hero"' portfolio/bolobakery.html`
Expected: `0` for the placeholder (removed), `1` for `class="hero"`.

- [ ] **Step 4: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.html portfolio/bolobakery.css
git commit -m "feat(bolobakery): add full-bleed hero with gradient placeholder and scroll hint"
```

---

## Task 6: Build the story section

**Files:**
- Modify: `portfolio/bolobakery.html` (replace the `<!-- STORY -->` placeholder)
- Modify: `portfolio/bolobakery.css` (append story styles)

- [ ] **Step 1: Add the story HTML**

In `portfolio/bolobakery.html`, replace the `<!-- STORY — Task 6 fills this in -->` comment with:

```html
    <section id="story" class="story" aria-labelledby="story-heading">
      <div class="container story-grid">
        <figure class="story-media" data-reveal>
          <div class="img-placeholder story-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
            <span>image pending</span>
          </div>
          <figcaption class="label">The oven</figcaption>
        </figure>
        <div class="story-copy" data-reveal>
          <p class="label">Our story</p>
          <h2 id="story-heading">A small oven, a long line of mornings.</h2>
          <p>Bolo started in a Connecticut kitchen with a grandmother, a rolling pin, and a stack of recipes brought over from Portugal. Three generations later, the oven is a little bigger, the kitchen has a sign out front, and the recipes are still the same.</p>
          <p>We bake in small batches, by hand, every morning. Some days we sell out. On those days, we are sorry — and also a little proud.</p>
          <p class="hand signature">— The Ferreira Family</p>
        </div>
      </div>
    </section>
```

- [ ] **Step 2: Append story styles to `portfolio/bolobakery.css`**

Append to the end of `portfolio/bolobakery.css`:

```css
/* ----- Story ----- */
.story-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 3rem;
  align-items: center;
}
.story-media {
  aspect-ratio: 4 / 5;
  max-width: 480px;
  margin-inline: auto;
  width: 100%;
}
.story-media .img-placeholder { height: 100%; }
.story-media figcaption {
  text-align: center;
  margin-top: 0.75rem;
}
.story-copy .label { margin-bottom: 0.75rem; }
.story-copy h2 { margin-bottom: 1.5rem; }
.story-copy p + p { margin-top: 1rem; }
.story-copy .signature {
  margin-top: 1.75rem;
  display: inline-block;
}
@media (min-width: 880px) {
  .story-grid {
    grid-template-columns: 5fr 7fr;
    gap: 4.5rem;
  }
  .story-media { max-width: none; }
}
```

- [ ] **Step 3: Verify story placeholder is replaced**

Run: `grep -c 'STORY — Task 6' portfolio/bolobakery.html && grep -c 'id="story"' portfolio/bolobakery.html`
Expected: `0` for the placeholder, `1` for the `id="story"` section.

- [ ] **Step 4: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.html portfolio/bolobakery.css
git commit -m "feat(bolobakery): add two-column story section with family signature"
```

---

## Task 7: Build the Today's Bakes grid

**Files:**
- Modify: `portfolio/bolobakery.html` (replace the `<!-- BAKES -->` placeholder)
- Modify: `portfolio/bolobakery.css` (append bakes styles)

- [ ] **Step 1: Add the bakes HTML**

In `portfolio/bolobakery.html`, replace the `<!-- BAKES — Task 7 fills this in -->` comment with:

```html
    <section id="bakes" class="bakes" aria-labelledby="bakes-heading">
      <div class="container">
        <header class="bakes-header" data-reveal>
          <p class="hand">today's bake</p>
          <h2 id="bakes-heading">Small batches, baked by hand.</h2>
          <p class="bakes-intro">A rotating selection from this morning's oven. When it's gone, it's gone — and tomorrow we start again.</p>
        </header>
        <ul class="bakes-grid" role="list">
          <li class="bake-card" data-reveal>
            <div class="img-placeholder"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg><span>image pending</span></div>
            <div class="bake-body">
              <h3>Pastéis de Nata</h3>
              <p>Portuguese custard tarts with a lacquered, cinnamon-dusted top.</p>
              <p class="price">$3.50</p>
            </div>
          </li>
          <li class="bake-card" data-reveal>
            <div class="img-placeholder"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg><span>image pending</span></div>
            <div class="bake-body">
              <h3>Country Loaf</h3>
              <p>Slow-fermented sourdough with a dark, crackling crust.</p>
              <p class="price">$8.00</p>
            </div>
          </li>
          <li class="bake-card" data-reveal>
            <div class="img-placeholder"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg><span>image pending</span></div>
            <div class="bake-body">
              <h3>Bolo de Arroz</h3>
              <p>Tender rice-flour muffin with vanilla and lemon zest.</p>
              <p class="price">$2.75</p>
            </div>
          </li>
          <li class="bake-card" data-reveal>
            <div class="img-placeholder"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg><span>image pending</span></div>
            <div class="bake-body">
              <h3>Almond Croissant</h3>
              <p>Twice-baked with frangipane and a generous snowfall of sugar.</p>
              <p class="price">$4.25</p>
            </div>
          </li>
          <li class="bake-card" data-reveal>
            <div class="img-placeholder"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg><span>image pending</span></div>
            <div class="bake-body">
              <h3>Sourdough Miche</h3>
              <p>A large, heritage-grain round for the table. Feeds a small crowd.</p>
              <p class="price">$14.00</p>
            </div>
          </li>
          <li class="bake-card" data-reveal>
            <div class="img-placeholder"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg><span>image pending</span></div>
            <div class="bake-body">
              <h3>Broa de Milho</h3>
              <p>Portuguese corn bread with a quiet sweetness and a dense crumb.</p>
              <p class="price">$7.00</p>
            </div>
          </li>
        </ul>
      </div>
    </section>
```

- [ ] **Step 2: Append bakes styles to `portfolio/bolobakery.css`**

Append to the end of `portfolio/bolobakery.css`:

```css
/* ----- Bakes ----- */
.bakes { background: rgba(168, 152, 133, 0.09); }
.bakes-header {
  text-align: center;
  max-width: 640px;
  margin: 0 auto 3.5rem;
}
.bakes-header .hand { margin-bottom: 0.5rem; }
.bakes-header h2 { margin-bottom: 1rem; }
.bakes-intro { color: var(--espresso); opacity: 0.78; }

.bakes-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.75rem;
}
@media (min-width: 640px) { .bakes-grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 960px) { .bakes-grid { grid-template-columns: repeat(3, 1fr); gap: 2.25rem; } }

.bake-card {
  background: var(--cream);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-soft);
  transition: transform var(--transition), box-shadow var(--transition);
  display: flex;
  flex-direction: column;
}
.bake-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lift);
}
.bake-card .img-placeholder {
  aspect-ratio: 4 / 3;
  border: none;
  border-radius: 0;
  background: rgba(168, 152, 133, 0.18);
}
.bake-body {
  padding: 1.5rem 1.5rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}
.bake-body h3 { line-height: 1.2; }
.bake-body p { font-size: 0.9375rem; opacity: 0.82; }
.bake-body .price {
  margin-top: auto;
  padding-top: 0.75rem;
  font-family: var(--font-display);
  font-size: 1.125rem;
  color: var(--crust);
  opacity: 1;
}
```

- [ ] **Step 3: Verify**

Run: `grep -c 'BAKES — Task 7' portfolio/bolobakery.html && grep -c 'bake-card' portfolio/bolobakery.html`
Expected: `0` for the placeholder, `6` for `bake-card` (one per product).

- [ ] **Step 4: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.html portfolio/bolobakery.css
git commit -m "feat(bolobakery): add Today's Bakes responsive grid with 6 products"
```

---

## Task 8: Build the Visit section

**Files:**
- Modify: `portfolio/bolobakery.html` (replace the `<!-- VISIT -->` placeholder)
- Modify: `portfolio/bolobakery.css` (append visit styles)

- [ ] **Step 1: Add the visit HTML**

In `portfolio/bolobakery.html`, replace the `<!-- VISIT — Task 8 fills this in -->` comment with:

```html
    <section id="visit" class="visit" aria-labelledby="visit-heading">
      <div class="container visit-grid">
        <div class="visit-copy" data-reveal>
          <p class="label">Visit</p>
          <h2 id="visit-heading">Come say good morning.</h2>
          <address class="visit-address">
            42 Main Street<br>
            Collinsville, CT 06019
          </address>
          <dl class="visit-hours">
            <div><dt>Tue – Fri</dt><dd>6:30 am – 2:00 pm</dd></div>
            <div><dt>Saturday</dt><dd>7:00 am – 3:00 pm</dd></div>
            <div><dt>Sunday</dt><dd>7:00 am – 1:00 pm</dd></div>
            <div><dt>Monday</dt><dd>Closed (we're resting)</dd></div>
          </dl>
          <p class="visit-phone">
            <a href="tel:+18605552253">(860) 555-BAKE</a>
          </p>
          <p class="visit-walkin">Walk-ins welcome.</p>
        </div>
        <figure class="visit-media" data-reveal>
          <div class="img-placeholder visit-map">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            <span>map pending</span>
          </div>
        </figure>
      </div>
      <p class="visit-upsell" data-reveal><em>We also do custom orders for weddings, birthdays, and celebrations. Ask at the counter or call ahead.</em></p>
    </section>
```

- [ ] **Step 2: Append visit styles to `portfolio/bolobakery.css`**

Append to the end of `portfolio/bolobakery.css`:

```css
/* ----- Visit ----- */
.visit-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 3rem;
  align-items: start;
}
@media (min-width: 880px) {
  .visit-grid {
    grid-template-columns: 5fr 7fr;
    gap: 4.5rem;
  }
}
.visit-copy .label { margin-bottom: 0.75rem; }
.visit-copy h2 { margin-bottom: 1.5rem; }
.visit-address {
  font-style: normal;
  font-size: 1.0625rem;
  line-height: 1.7;
  margin-bottom: 1.75rem;
}
.visit-hours {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.75rem;
}
.visit-hours > div {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: 1rem;
  padding-block: 0.4rem;
  border-bottom: 1px dashed var(--stone-light);
}
.visit-hours dt { font-weight: 500; color: var(--espresso); }
.visit-hours dd { color: var(--espresso); opacity: 0.8; }

.visit-phone { font-size: 1.25rem; margin-bottom: 0.5rem; }
.visit-phone a {
  font-family: var(--font-display);
  color: var(--crust);
  border-bottom: 1px solid transparent;
  transition: border-color var(--transition);
}
.visit-phone a:hover,
.visit-phone a:focus-visible { border-bottom-color: var(--crust); }
.visit-walkin { color: var(--stone); font-size: 0.9375rem; }

.visit-media .visit-map {
  aspect-ratio: 4 / 3;
  background: rgba(168, 152, 133, 0.14);
  border: 1px dashed var(--stone);
}

.visit-upsell {
  max-width: 48rem;
  margin: 3.5rem auto 0;
  text-align: center;
  color: var(--stone);
  font-size: 1.05rem;
}
```

- [ ] **Step 3: Verify**

Run: `grep -c 'VISIT — Task 8' portfolio/bolobakery.html && grep -c 'id="visit"' portfolio/bolobakery.html`
Expected: `0` for the placeholder, `1` for the `id="visit"` section.

- [ ] **Step 4: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.html portfolio/bolobakery.css
git commit -m "feat(bolobakery): add Visit section with address, hours, phone, and map placeholder"
```

---

## Task 9: Build the footer with H&P attribution

**Files:**
- Modify: `portfolio/bolobakery.html` (replace the `<!-- FOOTER -->` placeholder)
- Modify: `portfolio/bolobakery.css` (append footer styles)

- [ ] **Step 1: Add the footer HTML**

In `portfolio/bolobakery.html`, replace the `<!-- FOOTER — Task 9 fills this in -->` comment with:

```html
  <footer id="contact" class="site-footer">
    <div class="container footer-inner">
      <p class="footer-brand">Bolo</p>
      <ul class="footer-social" aria-label="Social media">
        <li><a href="#" aria-label="Instagram">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>
        </a></li>
        <li><a href="#" aria-label="Facebook">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>
        </a></li>
      </ul>
      <p class="footer-tagline">Baked fresh daily since 1987.</p>
      <div class="hp-attribution">
        This is a demo site by <strong>Hammer &amp; Pixels</strong> — web design &amp; IT support in the Farmington Valley. Want a site like this for your business? <a href="../index.html#contact">Let's talk →</a>
      </div>
    </div>
  </footer>
```

- [ ] **Step 2: Append footer styles to `portfolio/bolobakery.css`**

Append to the end of `portfolio/bolobakery.css`:

```css
/* ----- Footer ----- */
.site-footer {
  background: var(--cream);
  padding-block: 4rem 2.5rem;
  border-top: 1px solid var(--stone-light);
}
.footer-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  text-align: center;
}
.footer-brand {
  font-family: var(--font-display);
  font-size: 2.25rem;
  color: var(--espresso);
}
.footer-social {
  display: flex;
  gap: 1rem;
}
.footer-social a {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 999px;
  border: 1px solid var(--stone-light);
  color: var(--espresso);
  transition: background var(--transition), color var(--transition), border-color var(--transition);
}
.footer-social svg { width: 18px; height: 18px; }
.footer-social a:hover,
.footer-social a:focus-visible {
  background: var(--espresso);
  color: var(--cream);
  border-color: var(--espresso);
}
.footer-tagline {
  color: var(--stone);
  font-size: 0.9375rem;
  letter-spacing: 0.04em;
}

.hp-attribution {
  margin-top: 2rem;
  padding-top: 1.75rem;
  border-top: 1px dashed var(--stone-light);
  max-width: 44rem;
  color: var(--stone);
  font-size: 0.8125rem;
  line-height: 1.7;
}
.hp-attribution strong { color: var(--espresso); font-weight: 500; }
.hp-attribution a {
  color: var(--crust);
  border-bottom: 1px solid transparent;
  transition: border-color var(--transition);
}
.hp-attribution a:hover,
.hp-attribution a:focus-visible { border-bottom-color: var(--crust); }
```

- [ ] **Step 3: Verify**

Run: `grep -c 'FOOTER — Task 9' portfolio/bolobakery.html && grep -c 'hp-attribution' portfolio/bolobakery.html`
Expected: `0` for the placeholder, `1` for the `hp-attribution` div in the HTML.

- [ ] **Step 4: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.html portfolio/bolobakery.css
git commit -m "feat(bolobakery): add footer with social icons, tagline, and H&P attribution"
```

---

## Task 10: Add scroll-reveal and nav scroll JavaScript

**Files:**
- Create: `portfolio/bolobakery.js`

- [ ] **Step 1: Create the JS file**

Write `portfolio/bolobakery.js`:

```javascript
(function () {
  "use strict";

  // ---- Nav scroll state ----
  const nav = document.getElementById("site-nav");
  if (nav) {
    const updateNav = () => {
      if (window.scrollY > 80) nav.classList.add("scrolled");
      else nav.classList.remove("scrolled");
    };
    updateNav();
    window.addEventListener("scroll", updateNav, { passive: true });
  }

  // ---- Mobile menu toggle ----
  const toggle = document.getElementById("nav-toggle");
  if (nav && toggle) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("menu-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
    // Close on link click
    nav.querySelectorAll(".nav-links a").forEach((a) => {
      a.addEventListener("click", () => {
        nav.classList.remove("menu-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
      });
    });
  }

  // ---- Scroll reveal via IntersectionObserver ----
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const reveals = document.querySelectorAll("[data-reveal]");
  if (reduced) {
    reveals.forEach((el) => el.classList.add("is-visible"));
    return;
  }
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" }
    );
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("is-visible"));
  }
})();
```

- [ ] **Step 2: Verify**

Run: `node --check portfolio/bolobakery.js && wc -l portfolio/bolobakery.js`
Expected: no syntax error from `node --check`, line count around 45.

If `node` is not installed, instead run: `head -5 portfolio/bolobakery.js` and visually confirm the IIFE wrapper.

- [ ] **Step 3: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.js
git commit -m "feat(bolobakery): add scroll-reveal, nav scroll state, and mobile menu JS"
```

---

## Task 11: Responsive and accessibility pass

**Files:**
- Modify: `portfolio/bolobakery.css` (append final pass)
- Modify: `portfolio/bolobakery.html` (audit alt text and landmarks)

- [ ] **Step 1: Append a final responsive/a11y pass to `portfolio/bolobakery.css`**

Append to the end of `portfolio/bolobakery.css`:

```css
/* ----- Final pass: fine-tuning and selection color ----- */
::selection {
  background: var(--crust);
  color: var(--cream);
}

/* Narrower hero content on small screens */
@media (max-width: 520px) {
  .hero-content { padding-block: 7rem 3rem; }
  .hero h1 br { display: none; }
  .hero-sub { font-size: 1rem; }
}

/* Tighten section padding on tight phones */
@media (max-width: 480px) {
  main > section { padding-block: clamp(3.5rem, 10vw, 5rem); }
}

/* Make the nav brand slightly smaller on narrow screens */
@media (max-width: 400px) {
  .brand { font-size: 1.5rem; }
}
```

- [ ] **Step 2: Audit every image slot in the HTML for decorative-vs-meaningful distinction**

Open `portfolio/bolobakery.html` and verify:
- The hero placeholder and map placeholder are inside `aria-hidden="true"` wrappers (hero is) OR have empty alt text.
- The story `<figure>` has a `<figcaption>` present ("The oven").
- Each bake card has a `<h3>` with product name (the placeholders are decorative per the visible card label).

Run: `grep -n 'aria-hidden\|figcaption\|<h3>' portfolio/bolobakery.html`
Expected: hero media has `aria-hidden="true"`, there is one `figcaption`, six `<h3>` product names.

If any are missing, edit the HTML to add them before committing.

- [ ] **Step 3: Verify the skip link, lang attribute, and meta description exist**

Run: `grep -n 'lang="en"\|skip-link\|name="description"' portfolio/bolobakery.html`
Expected: 3 lines, one match each.

- [ ] **Step 4: Commit**

```bash
rm -f .git/index.lock
git add portfolio/bolobakery.html portfolio/bolobakery.css
git commit -m "feat(bolobakery): responsive polish and accessibility audit pass"
```

---

## Task 12: Final verification and push

**Files:** none (verification-only)

- [ ] **Step 1: Confirm no stray task-placeholder comments remain**

Run: `grep -c 'Task [0-9]* fills this in' portfolio/bolobakery.html`
Expected: `0`.

If any are non-zero, go back and finish the corresponding task before proceeding.

- [ ] **Step 2: Confirm the page references no broken local assets**

Run: `grep -oE '(src|href)="[^"]*"' portfolio/bolobakery.html | grep -v 'https://\|#\|tel:\|mailto:' | sort -u`
Expected: local references to `bolobakery.css`, `bolobakery.js`, `../index.html#contact`. No `.png`/`.jpg` references (we are using placeholder blocks until photos are sourced).

- [ ] **Step 3: Confirm file sizes and count**

Run:
```bash
ls -la portfolio/bolobakery.html portfolio/bolobakery.css portfolio/bolobakery.js
ls portfolio/BoloBakeryAssets/
```
Expected: HTML roughly 6–10 KB, CSS roughly 9–14 KB, JS roughly 1.5–2 KB. 5 SVG files in assets.

- [ ] **Step 4: Lighthouse audit (optional but recommended)**

If Chrome or a Chromium-based browser is available, open `portfolio/bolobakery.html` with devtools, run a Lighthouse audit for Performance, Accessibility, Best Practices, and SEO on desktop preset. Target: 95+ on all four categories. If any category scores below 95, read the specific issues Lighthouse flags and address them before moving to Step 5.

If Lighthouse is not available in the environment, skip this step and rely on the manual check below plus the a11y audit done in Task 11.

- [ ] **Step 5: Manual browser check (user action, not automated)**

Open `portfolio/bolobakery.html` directly in a browser (`file://` URL is fine). Visually confirm:
1. Hero renders full-viewport with the gradient placeholder and cream headline over a dark tint.
2. Nav is translucent at the top, becomes cream-solid with a subtle shadow after scrolling past the hero.
3. Story section has the 2-column layout on desktop, stacked on mobile.
4. Today's Bakes grid shows 6 cards, collapses to 3 columns on tablet and 1 column on mobile.
5. Visit section shows address, hours table, phone link, and map placeholder side by side on desktop.
6. Footer has centered brand wordmark, social icons, tagline, and the H&P attribution line at the bottom.
7. Clicking nav links smooth-scrolls to sections.
8. Scroll-reveal kicks in for sections as you scroll.
9. Resize the browser to 375px wide: mobile menu hamburger appears, tapping it expands the menu, tapping a link closes it.
10. In devtools, enable "prefers-reduced-motion" and reload: sections appear instantly (no fade-up), hero scroll-hint stops bouncing.

- [ ] **Step 6: Push to origin**

```bash
for i in 1 2 3 4 5; do rm -f .git/index.lock && git push origin main && break; sleep 1; done
```

Expected: `main -> main` update pushed.

- [ ] **Step 7: Report back**

Announce to the user that the Bolo Bakery facelift is live on `main` and auto-deploying via Cloudflare/Netlify. Include the list of commits created during this plan for the changelog.

---

## Out of scope for this plan

- Coffee shop, restaurant, yoga gym demos. Each gets its own spec + plan cycle when the user is ready.
- Sourcing or integrating real photographs. Placeholders stand in until the user provides image assets.
- Modifying `portfolio/index.html` (the portfolio landing page). Any updates to the landing page are separate work.
- Lead example sites (`LeadExamples/mangiaficos.*`, `LeadExamples/nonnies.*`). Out of scope entirely.
