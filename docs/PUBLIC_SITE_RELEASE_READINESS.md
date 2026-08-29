# Public-site release readiness

The GitHub Pages site is a release interface for users, developers, automation, and assistive-technology users. A successful static build is necessary but is not sufficient evidence that the public surface is ready.

## Required gates

1. **Deterministic project contract** — `scripts/check-public-site.py` validates generated routes, machine endpoints, stable-release metadata, fragments/resources, and project-specific public contracts.
2. **Cross-browser user flows** — Playwright Test runs the project-specific suite in `tests/site/public-site.spec.mjs` against candidate bytes built locally by `scripts/build-public-site.py`.
3. **Automated accessibility** — `@axe-core/playwright` is executed inside the browser suite in light and dark system modes.
4. **Quality budgets** — Lighthouse CI evaluates accessibility, best practices, SEO, and performance against `lighthouserc.cjs`.
5. **Link integrity** — Lychee checks repository/public-document links while the deterministic site checker remains authoritative for candidate-site internal routes and fragments.
6. **Deployed smoke** — after Pages deployment, Chromium repeats the primary user journey against the deployed URL and the deterministic checker verifies the live surface.

The browser/accessibility/Lighthouse/link tooling is intentionally standard upstream tooling. Project code should contain only VanillaCord-specific assertions and contracts, not a bespoke browser framework.

## Blocking browser/device envelope

The release-readiness suite must pass in:

- desktop Chromium;
- desktop Firefox;
- desktop WebKit/Safari-family behavior;
- Android Chromium using a Playwright Pixel device profile;
- iPhone WebKit using a Playwright iPhone device profile.

A separate 320 CSS-pixel reflow assertion runs across the browser projects to ensure primary navigation and controls remain usable and the document does not acquire accidental horizontal overflow.

Tablet behavior may be added as an advisory project if evidence shows value; it is not part of the initial blocking baseline.

## Browser acceptance envelope

The Playwright suite verifies that:

- every intended human route returns successfully with one H1, named primary navigation, a main landmark, footer, project identity, theme selector, skip link, and one current-page marker;
- automated axe scans report no configured WCAG A/AA violations in light and dark system modes;
- `Theme = System` follows `prefers-color-scheme`, while explicit Light/Dark choices persist locally and override the system setting;
- desktop keyboard users can focus and activate the skip link to reach main content;
- the page does not overflow horizontally at 320 CSS pixels and primary navigation remains available;
- release/download/support/guide journeys stay on the friendly public site where appropriate;
- release download URLs still resolve from the stable-release contract rather than being inferred from page text;
- browser page errors and console errors are absent.

## Accessibility target

The public site targets **WCAG 2.2 Level AA** and is designed to align with the Revised Section 508 web accessibility criteria where applicable. Automated testing is evidence, not certification: automated tools detect only a subset of accessibility defects.

Material interaction/design changes still require manual keyboard, zoom/reflow, screen-reader/semantic, and forced-colors/high-contrast review before the surface is described as release-ready.

Use native HTML semantics before ARIA. ARIA should clarify relationships or state that HTML cannot express; it should not replace correctly structured headings, links, buttons, labels, tables, and landmarks.

## Candidate bytes, not yesterday's deployment

PR validation must test the exact candidate site bytes. `scripts/build-public-site.py --base-url <local-url>` rewrites generated navigation/assets for the local candidate server so browser tests cannot accidentally follow the currently deployed production site and certify an older revision.

Canonical links remain production-facing metadata; navigational test URLs are the candidate-local override.

## Local reproduction

Install the exact direct tool versions in `package.json`, then install the three Playwright browser engines:

```sh
npm install --ignore-scripts --no-audit --no-fund
npx playwright install --with-deps chromium firefox webkit
npm run site:test
CHROME_PATH="$(node --input-type=module -e "import { chromium } from '@playwright/test'; process.stdout.write(chromium.executablePath())")" npm run site:lighthouse
```

CI also runs the pinned Lychee GitHub Action for link checking. Browser traces/screenshots, the Playwright HTML report, Lighthouse reports, and Lychee output are retained as diagnostic evidence when available.

## External destinations

Transient third-party outages should not be confused with candidate-site defects. The deterministic checker is authoritative for internal candidate routes/resources/fragments. Critical external release/download destinations remain part of the owning release contract; general external documentation links are checked by Lychee with limited retries.
