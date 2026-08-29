# Public-site release readiness

The GitHub Pages site is a release interface for users, developers, automation, and assistive-technology users. A successful site build is not sufficient evidence that the public surface is ready.

## Required gates

1. **Deterministic contract check** — `scripts/check-public-site.py` validates generated files, machine endpoints, common page structure, theme/accessibility assets, and every internal `href`/`src` in the built artifact.
2. **Browser user-flow check** — `scripts/check-public-site-browser.mjs` uses headless Chromium and axe to crawl all discoverable human routes, exercise the rendered DOM, and fail on browser-level regressions.
3. **Deployed-site smoke** — the Pages workflow repeats contract and browser checks against the deployed URL after publication.

## Browser acceptance envelope

The browser gate must verify:

- every discoverable human page returns successfully and has one H1, named primary navigation, main and footer landmarks, the project icon, a theme selector, a skip link, and one current-page marker;
- internal resources linked from the human surface resolve successfully;
- automated axe scans report no WCAG A/AA violations in both light and dark system modes;
- `Theme = System` follows `prefers-color-scheme`, while explicit Light/Dark choices persist locally and override the system setting;
- skip navigation is the first keyboard focus target and moves focus to main content;
- the page does not overflow horizontally at a 320 CSS-pixel reflow width and primary navigation is not hidden;
- browser page errors and console errors are absent.

External destinations are recorded for review but are not release-blocking solely because a third-party host is temporarily unavailable. Critical external release/download targets remain release-contract concerns and should be validated by their owning release pipeline.

## Accessibility target

The public site targets **WCAG 2.2 Level AA** and is designed to align with the Revised Section 508 web accessibility criteria where applicable. The automated browser gate is evidence, not a certification: automated tools detect only a subset of accessibility defects. Material interaction/design changes still require manual keyboard, zoom/reflow, screen-reader/semantic, and high-contrast review before calling the surface release-ready.

Use native HTML semantics before adding ARIA. ARIA should clarify relationships or state that HTML cannot express; it should not replace correctly structured headings, links, buttons, labels, tables, and landmarks.

## Local browser check

The CI workflow pins the Playwright and axe package versions used by the gate. To reproduce the browser check locally, install the same versions shown in `.github/workflows/documentation.yml`, install Chromium with Playwright, build a local-browser copy with `--base-url`, serve it over HTTP, and run `scripts/check-public-site-browser.mjs --base-url <local-url>`.

The generated JSON readiness report is diagnostic evidence. It records the pages crawled, internal resources exercised, external links observed, and final pass/fail state.
