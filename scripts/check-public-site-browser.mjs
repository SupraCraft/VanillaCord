#!/usr/bin/env node
import fs from 'node:fs';
import process from 'node:process';
import path from 'node:path';
import { chromium } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

function parseArgs(argv) {
  const args = { report: null };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--base-url') args.baseUrl = argv[++i];
    else if (arg === '--report') args.report = argv[++i];
    else throw new Error(`unknown argument: ${arg}`);
  }
  if (!args.baseUrl) throw new Error('--base-url is required');
  args.baseUrl = new URL('./', args.baseUrl).href;
  return args;
}

function fail(message) {
  throw new Error(message);
}

function isHumanRoute(url, baseUrl) {
  if (url.origin !== baseUrl.origin) return false;
  if (!url.pathname.startsWith(baseUrl.pathname)) return false;
  const relative = url.pathname.slice(baseUrl.pathname.length);
  return relative === '' || relative.endsWith('/') || relative.endsWith('.html');
}

function normalizeInternal(raw, currentUrl, baseUrl) {
  if (!raw || raw.startsWith('mailto:') || raw.startsWith('tel:') || raw.startsWith('javascript:')) return null;
  const resolved = new URL(raw, currentUrl);
  if (resolved.origin !== baseUrl.origin || !resolved.pathname.startsWith(baseUrl.pathname)) return null;
  resolved.hash = '';
  return resolved;
}

async function assertPageStructure(page, url) {
  const errors = [];
  const consoleErrors = [];
  page.on('pageerror', error => errors.push(String(error)));
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });

  const response = await page.goto(url.href, { waitUntil: 'networkidle' });
  if (!response || response.status() >= 400) fail(`${url.href}: HTTP ${response?.status() ?? 'no response'}`);

  const counts = await page.evaluate(() => ({
    h1: document.querySelectorAll('h1').length,
    main: document.querySelectorAll('main').length,
    nav: document.querySelectorAll('nav[aria-label="Primary"]').length,
    footer: document.querySelectorAll('footer').length,
    brand: document.querySelectorAll('.brand .brand-mark').length,
    theme: document.querySelectorAll('#theme-select').length,
    skip: document.querySelectorAll('a.skip-link[href="#main-content"]').length,
    lang: document.documentElement.getAttribute('lang') || '',
    horizontalOverflow: document.documentElement.scrollWidth - window.innerWidth,
  }));

  if (counts.lang.toLowerCase() !== 'en') fail(`${url.href}: html lang must be en`);
  if (counts.h1 !== 1) fail(`${url.href}: expected exactly one h1, found ${counts.h1}`);
  if (counts.main !== 1) fail(`${url.href}: expected exactly one main landmark`);
  if (counts.nav !== 1) fail(`${url.href}: expected one named primary navigation landmark`);
  if (counts.footer !== 1) fail(`${url.href}: expected one footer landmark`);
  if (counts.brand !== 1) fail(`${url.href}: expected one branded header icon`);
  if (counts.theme !== 1) fail(`${url.href}: expected one theme selector`);
  if (counts.skip !== 1) fail(`${url.href}: expected one skip-to-content link`);
  if (counts.horizontalOverflow > 1) fail(`${url.href}: page overflows horizontally by ${counts.horizontalOverflow}px`);

  const headings = await page.locator('h1,h2,h3,h4,h5,h6').evaluateAll(nodes => nodes.map(node => Number(node.tagName.slice(1))));
  for (let i = 1; i < headings.length; i += 1) {
    if (headings[i] - headings[i - 1] > 1) fail(`${url.href}: heading level jumps from h${headings[i - 1]} to h${headings[i]}`);
  }

  const imagesMissingAlt = await page.locator('img:not([alt])').count();
  if (imagesMissingAlt) fail(`${url.href}: ${imagesMissingAlt} image(s) missing alt attributes`);

  const currentMarkers = await page.locator('[aria-current="page"]').count();
  if (currentMarkers !== 1) fail(`${url.href}: expected exactly one aria-current=page marker, found ${currentMarkers}`);

  const axe = async () => new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22a', 'wcag22aa'])
    .analyze();

  let scan = await axe();
  if (scan.violations.length) {
    const summary = scan.violations.map(v => `${v.id}(${v.impact ?? 'unknown'}): ${v.nodes.length}`).join(', ');
    fail(`${url.href}: accessibility violations in light/system mode: ${summary}`);
  }

  await page.emulateMedia({ colorScheme: 'dark' });
  await page.waitForFunction(() => document.querySelector('meta[name="theme-color"]')?.dataset.effectiveTheme === 'dark');
  scan = await axe();
  if (scan.violations.length) {
    const summary = scan.violations.map(v => `${v.id}(${v.impact ?? 'unknown'}): ${v.nodes.length}`).join(', ');
    fail(`${url.href}: accessibility violations in dark/system mode: ${summary}`);
  }

  if (errors.length) fail(`${url.href}: browser page errors: ${errors.join(' | ')}`);
  if (consoleErrors.length) fail(`${url.href}: console errors: ${consoleErrors.join(' | ')}`);

  const hrefs = await page.locator('a[href]').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
  const fragments = await page.locator('a[href^="#"]').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
  for (const fragment of fragments) {
    if (!fragment || fragment === '#') continue;
    const id = decodeURIComponent(fragment.slice(1));
    const exists = await page.evaluate(value => document.getElementById(value) !== null, id);
    if (!exists) fail(`${url.href}: broken fragment link ${fragment}`);
  }

  return hrefs;
}

async function testThemeAndKeyboard(page, baseUrl) {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto(baseUrl.href, { waitUntil: 'networkidle' });
  await page.evaluate(() => localStorage.removeItem('supracraft-theme'));
  await page.reload({ waitUntil: 'networkidle' });

  const select = page.locator('#theme-select');
  if (await select.inputValue() !== 'system') fail('theme selector must default to System');
  const systemMode = await page.locator('meta[name="theme-color"]').getAttribute('data-effective-theme');
  if (systemMode !== 'light') fail(`system theme should follow emulated light OS setting; got ${systemMode}`);

  await select.selectOption('dark');
  if (await page.evaluate(() => document.documentElement.dataset.theme) !== 'dark') fail('Dark override did not apply');
  await page.reload({ waitUntil: 'networkidle' });
  if (await page.locator('#theme-select').inputValue() !== 'dark') fail('Dark override did not persist after reload');

  await page.locator('#theme-select').selectOption('light');
  if (await page.evaluate(() => document.documentElement.dataset.theme) !== 'light') fail('Light override did not apply');

  await page.locator('#theme-select').selectOption('system');
  if (await page.evaluate(() => document.documentElement.dataset.theme || '') !== '') fail('System selection should remove explicit theme override');

  await page.keyboard.press('Home');
  await page.evaluate(() => document.activeElement?.blur());
  await page.keyboard.press('Tab');
  const firstFocus = await page.evaluate(() => document.activeElement?.classList.contains('skip-link') === true);
  if (!firstFocus) fail('skip-to-content link is not the first keyboard focus target');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(50);
  const targetReached = await page.evaluate(() => location.hash === '#main-content' && document.activeElement?.id === 'main-content');
  if (!targetReached) fail('skip-to-content link did not move focus to main content');
}

async function main() {
  const args = parseArgs(process.argv);
  const baseUrl = new URL(args.baseUrl);
  const browser = await chromium.launch({ headless: true });
  const report = { schema: 'supracraft-public-site-browser-readiness/1', base_url: baseUrl.href, pages: [], internal_resources: [], external_links: [] };

  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: 'light' });
    const page = await context.newPage();
    const queue = [baseUrl];
    const visited = new Set();
    const internalResources = new Set();
    const external = new Set();

    while (queue.length) {
      const url = queue.shift();
      const key = url.href;
      if (visited.has(key)) continue;
      visited.add(key);

      const hrefs = await assertPageStructure(page, url);
      report.pages.push(url.href);

      for (const raw of hrefs) {
        if (!raw) continue;
        const absolute = new URL(raw, url);
        if (absolute.origin !== baseUrl.origin || !absolute.pathname.startsWith(baseUrl.pathname)) {
          if (absolute.protocol === 'http:' || absolute.protocol === 'https:') external.add(absolute.href);
          continue;
        }
        absolute.hash = '';
        if (isHumanRoute(absolute, baseUrl)) {
          if (!visited.has(absolute.href)) queue.push(absolute);
        } else {
          internalResources.add(absolute.href);
        }
      }
    }

    for (const resource of [...internalResources].sort()) {
      const response = await context.request.get(resource, { timeout: 15000, failOnStatusCode: false });
      if (response.status() >= 400) fail(`${resource}: internal resource HTTP ${response.status()}`);
      report.internal_resources.push({ url: resource, status: response.status() });
    }

    await testThemeAndKeyboard(page, baseUrl);

    await page.setViewportSize({ width: 320, height: 800 });
    for (const url of report.pages) {
      await page.goto(url, { waitUntil: 'networkidle' });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (overflow > 1) fail(`${url}: 320px reflow overflows horizontally by ${overflow}px`);
      const hiddenPrimaryLinks = await page.locator('nav[aria-label="Primary"] a').evaluateAll(nodes => nodes.filter(node => {
        const style = getComputedStyle(node);
        return style.display === 'none' || style.visibility === 'hidden';
      }).length);
      if (hiddenPrimaryLinks) fail(`${url}: ${hiddenPrimaryLinks} primary navigation link(s) hidden at 320px`);
    }

    report.external_links = [...external].sort();
    report.status = 'pass';
    console.log(`Browser release-readiness OK: ${report.pages.length} human pages, ${report.internal_resources.length} internal resources, ${report.external_links.length} external links observed.`);
    await context.close();
  } catch (error) {
    report.status = 'fail';
    report.error = String(error?.stack || error);
    throw error;
  } finally {
    if (args.report) {
      fs.mkdirSync(path.dirname(path.resolve(args.report)), { recursive: true });
      fs.writeFileSync(args.report, JSON.stringify(report, null, 2) + '\n', 'utf8');
    }
    await browser.close();
  }
}

main().catch(error => {
  console.error(error?.stack || String(error));
  process.exit(1);
});
