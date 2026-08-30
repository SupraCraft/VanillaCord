import fs from 'node:fs';
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const stable = JSON.parse(fs.readFileSync('STABLE_RELEASE.json', 'utf8'));
const siteBaseUrl = new URL(process.env.SITE_BASE_URL || 'http://127.0.0.1:4173/');
const expectedOrigin = siteBaseUrl.origin;
const expectedBasePath = siteBaseUrl.pathname.endsWith('/') ? siteBaseUrl.pathname : `${siteBaseUrl.pathname}/`;
const sourceUrl = 'https://github.com/SupraCraft/VanillaCord';
const allowedExternalUrls = new Set([sourceUrl, stable.artifact.download_url]);
const routes = [
  '/',
  '/download/',
  '/support/',
  '/guide/',
  '/releases/',
  `/releases/${stable.version}/`,
  '/accessibility/',
];

function routeUrl(route) {
  return new URL(route.replace(/^\/+/, ''), siteBaseUrl).toString();
}

function isInternalUrl(value) {
  const target = new URL(value, siteBaseUrl);
  return target.origin === expectedOrigin && target.pathname.startsWith(expectedBasePath);
}

function assertExpectedSite(page, label) {
  const current = new URL(page.url());
  expect(current.origin, `${label} must stay on the site origin under test`).toBe(expectedOrigin);
  expect(current.pathname.startsWith(expectedBasePath), `${label} must stay under the site base path ${expectedBasePath}`).toBe(true);
}

async function assertNoHorizontalOverflow(page, label) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow, `${label} must not overflow horizontally`).toBeLessThanOrEqual(1);
}

async function assertA11y(page, label) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22a', 'wcag22aa'])
    .analyze();
  expect(results.violations, `${label} axe violations: ${results.violations.map(v => v.id).join(', ')}`).toEqual([]);
}

async function assertOutlinkContract(page, label) {
  const navHrefs = await page.locator('nav[aria-label="Primary"] a[href]').evaluateAll(nodes => nodes.map(node => node.href));
  for (const href of navHrefs) {
    expect(isInternalUrl(href), `${label} primary navigation must remain internal: ${href}`).toBe(true);
  }

  const anchors = await page.locator('a[href]').evaluateAll(nodes => nodes.map(node => {
    const indicator = node.querySelector('.external-link-indicator');
    const note = node.querySelector('.sr-only');
    const rect = indicator?.getBoundingClientRect();
    const style = indicator ? getComputedStyle(indicator) : null;
    return {
      href: node.href,
      target: node.getAttribute('target') || '',
      rel: node.getAttribute('rel') || '',
      className: node.className,
      indicatorText: indicator?.textContent?.trim() || '',
      indicatorAriaHidden: indicator?.getAttribute('aria-hidden') || '',
      indicatorVisible: Boolean(indicator && rect && rect.width > 0 && rect.height > 0 && style?.display !== 'none' && style?.visibility !== 'hidden'),
      noteText: note?.textContent?.trim() || '',
    };
  }));

  const external = anchors.filter(anchor => !isInternalUrl(anchor.href));
  expect(external.length, `${label} should expose only explicit external handoffs`).toBeGreaterThan(0);

  for (const anchor of external) {
    expect(allowedExternalUrls.has(anchor.href), `${label} unexpected outlink: ${anchor.href}`).toBe(true);
    expect(anchor.className.split(/\s+/)).toContain('external-link');
    expect(anchor.target, `${label} external link must preserve the current site`).toBe('_blank');
    const rel = new Set(anchor.rel.split(/\s+/).filter(Boolean));
    expect(rel.has('noopener'), `${label} external link must use noopener`).toBe(true);
    expect(rel.has('noreferrer'), `${label} external link must use noreferrer`).toBe(true);
    expect(anchor.indicatorText, `${label} external link must show the visual indicator`).toBe('↗');
    expect(anchor.indicatorAriaHidden, `${label} visual indicator should not duplicate the assistive notification`).toBe('true');
    expect(anchor.indicatorVisible, `${label} visual indicator must be visibly rendered`).toBe(true);
    expect(anchor.noteText, `${label} external link must provide an accessible new-context notification`).toMatch(/opens in a new tab or window/i);
  }

  const sourceLinks = external.filter(anchor => anchor.href === sourceUrl);
  expect(sourceLinks, `${label} should contain exactly one secondary source outlink`).toHaveLength(1);
}

for (const route of routes) {
  test(`${route} is a complete accessible user page`, async ({ page }, testInfo) => {
    const consoleErrors = [];
    const pageErrors = [];
    page.on('console', message => {
      if (message.type() === 'error') consoleErrors.push(message.text());
    });
    page.on('pageerror', error => pageErrors.push(String(error)));

    const response = await page.goto(routeUrl(route), { waitUntil: 'networkidle' });
    expect(response?.status()).toBeLessThan(400);
    assertExpectedSite(page, `${testInfo.project.name} ${route}`);
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    await expect(page.locator('h1')).toHaveCount(1);
    await expect(page.locator('nav[aria-label="Primary"]')).toHaveCount(1);
    await expect(page.locator('main#main-content')).toHaveCount(1);
    await expect(page.locator('footer')).toHaveCount(1);
    await expect(page.locator('.brand .brand-mark')).toHaveCount(1);
    await expect(page.locator('#theme-select')).toHaveCount(1);
    await expect(page.locator('a.skip-link[href="#main-content"]')).toHaveCount(1);
    await expect(page.locator('[aria-current="page"]')).toHaveCount(1);
    await expect(page.locator('img:not([alt])')).toHaveCount(0);

    const headings = await page.locator('h1,h2,h3,h4,h5,h6').evaluateAll(nodes => nodes.map(n => Number(n.tagName.slice(1))));
    for (let index = 1; index < headings.length; index += 1) {
      expect(headings[index] - headings[index - 1], `heading jump on ${route}`).toBeLessThanOrEqual(1);
    }

    await assertNoHorizontalOverflow(page, `${testInfo.project.name} ${route}`);
    await assertOutlinkContract(page, `${testInfo.project.name} ${route}`);
    await assertA11y(page, `${testInfo.project.name} ${route} light/system`);

    await page.emulateMedia({ colorScheme: 'dark' });
    await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('data-effective-theme', 'dark');
    await assertOutlinkContract(page, `${testInfo.project.name} ${route} dark/system`);
    await assertA11y(page, `${testInfo.project.name} ${route} dark/system`);

    expect(pageErrors, `${route} page errors`).toEqual([]);
    expect(consoleErrors, `${route} console errors`).toEqual([]);
  });
}

test('primary user journeys stay on the friendly site', async ({ page }) => {
  await page.goto(routeUrl('/'));
  assertExpectedSite(page, 'homepage');
  await page.getByRole('link', { name: 'Download VanillaCord' }).click();
  assertExpectedSite(page, 'download journey');
  await expect(page).toHaveURL(/\/download\/$/);
  await expect(page.getByRole('heading', { level: 1 })).toContainText(`VanillaCord ${stable.version}`);

  const download = page.getByRole('link', { name: new RegExp(`Download ${stable.artifact.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`) });
  await expect(download).toHaveAttribute('href', stable.artifact.download_url);
  await expect(download).toHaveAttribute('target', '_blank');
  expect(stable.artifact.download_url).toContain('/releases/download/');

  await page.getByRole('link', { name: 'Supported versions' }).click();
  assertExpectedSite(page, 'support journey');
  await expect(page).toHaveURL(/\/support\/$/);
  await expect(page.getByRole('table')).toBeVisible();

  await page.getByRole('link', { name: 'Guide' }).click();
  assertExpectedSite(page, 'guide journey');
  await expect(page).toHaveURL(/\/guide\/$/);
});

test('theme System, Light, and Dark work and persist', async ({ page }) => {
  await page.goto(routeUrl('/'));
  assertExpectedSite(page, 'theme test homepage');
  await page.evaluate(() => localStorage.removeItem('supracraft-theme'));
  await page.emulateMedia({ colorScheme: 'light' });
  await page.reload();

  const selector = page.locator('#theme-select');
  await expect(selector).toHaveValue('system');
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('data-effective-theme', 'light');

  await selector.selectOption('dark');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.reload();
  await expect(selector).toHaveValue('dark');

  await selector.selectOption('light');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');

  await selector.selectOption('system');
  await expect(page.locator('html')).not.toHaveAttribute('data-theme', /.+/);
  await page.emulateMedia({ colorScheme: 'dark' });
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('data-effective-theme', 'dark');
});

test('320px reflow keeps navigation and primary controls usable', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  for (const route of routes) {
    await page.goto(routeUrl(route), { waitUntil: 'networkidle' });
    assertExpectedSite(page, `320px ${route}`);
    await assertNoHorizontalOverflow(page, `320px ${route}`);
    await assertOutlinkContract(page, `320px ${route}`);
    const navLinks = page.locator('nav[aria-label="Primary"] a');
    for (let index = 0; index < await navLinks.count(); index += 1) {
      await expect(navLinks.nth(index)).toBeVisible();
    }
    const primaryControls = page.locator('nav[aria-label="Primary"] a, #theme-select, a.button');
    const boxes = await primaryControls.evaluateAll(nodes => nodes.map(node => {
      const rect = node.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    }));
    for (const box of boxes) {
      expect(box.width).toBeGreaterThanOrEqual(24);
      expect(box.height).toBeGreaterThanOrEqual(24);
    }
  }
});

test('desktop keyboard users can skip directly to main content', async ({ page }, testInfo) => {
  test.skip(!testInfo.project.name.startsWith('desktop-'), 'keyboard tab-order check applies to desktop browser projects');
  await page.goto(routeUrl('/'));
  assertExpectedSite(page, `${testInfo.project.name} keyboard test`);
  await page.evaluate(() => document.activeElement?.blur());
  await page.keyboard.press('Tab');
  await expect(page.locator('.skip-link')).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();
});
