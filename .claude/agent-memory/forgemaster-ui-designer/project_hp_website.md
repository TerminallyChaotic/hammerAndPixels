---
name: Hammer & Pixels website redesign
description: Single-page marketing site for H&P web design/IT support business. Key design decisions and structure.
type: project
---

The H&P website is a single-page marketing site (index.html + style.css + script.js) with sections: hero, meet Jesse, services, who I serve, portfolio, photo break, why me, pricing, about, contact, footer.

**Why:** Jesse plans to swap the hero background image for a video in the future -- the hero structure uses a .hero-bg-image wrapper that supports both <img> and <video> elements.

**How to apply:** When making hero changes, preserve the .hero-bg-image container and .hero-content-box opaque panel structure. The overlay is intentionally lighter (35-60% opacity) because the opaque content box handles text readability.
