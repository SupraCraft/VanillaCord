import { test, expect } from '@playwright/test';

const siteBaseUrl = new URL(process.env.SITE_BASE_URL || 'http://127.0.0.1:4173/');
const routes = ['/', '/download/', '/support/', '/guide/', '/releases/', '/accessibility/'];
const genericStandaloneName = /^(?:click here|here|more|read more|learn more|link|button|open)$/i;
const primarySelector = '.brand, nav[aria-label="Primary"] a, .theme-option input, a.button';
const keyboardPrimarySelector = '.brand, nav[aria-label="Primary"] a, .theme-option input:checked, a.button';

function routeUrl(route) {
  return new URL(route.replace(/^\/+/, ''), siteBaseUrl).toString();
}

async function assertPrimaryTargets(page, label) {
  const controls = page.locator(primarySelector);
  expect(await controls.count(), `${label} should expose declared primary controls`).toBeGreaterThan(0);

  for (let index = 0; index < await controls.count(); index += 1) {
    const control = controls.nth(index);
    await expect(control, `${label} primary control ${index}`).toBeVisible();
    const geometry = await control.evaluate(node => {
      const rect = node.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    });
    expect(geometry.width, `${label} primary control ${index} width`).toBeGreaterThanOrEqual(44);
    expect(geometry.height, `${label} primary control ${index} height`).toBeGreaterThanOrEqual(44);
  }
}

async function assertKeyboardFocusPath(page, label) {
  const expected = await page.locator(keyboardPrimarySelector).count();
  expect(expected, `${label} should expose keyboard-primary controls`).toBeGreaterThan(0);

  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    window.scrollTo(0, 0);
  });

  const seen = new Set();
  const maxTabs = Math.max(24, expected * 3);
  for (let index = 0; index < maxTabs && seen.size < expected; index += 1) {
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(selector => {
      const node = document.activeElement;
      if (!(node instanceof HTMLElement) || !node.matches(selector)) return { primary: false };

      const text = (node.getAttribute('aria-label') || node.textContent || '').replace(/\s+/g, ' ').trim();
      return {
        primary: true,
        identity: [node.tagName, node.getAttribute('href') || '', node.getAttribute('name') || '', node.getAttribute('value') || '', text].join('|'),
      };
    }, keyboardPrimarySelector);

    if (!focused.primary) continue;

    await expect.poll(async () => page.evaluate(selector => {
      const node = document.activeElement;
      if (!(node instanceof HTMLElement) || !node.matches(selector)) return false;

      const rect = node.getBoundingClientRect();
      const left = Math.max(rect.left, 0);
      const right = Math.min(rect.right, innerWidth);
      const topEdge = Math.max(rect.top, 0);
      const bottom = Math.min(rect.bottom, innerHeight);
      return right > left && bottom > topEdge;
    }, keyboardPrimarySelector), {
      message: `${label} keyboard-focused ${focused.identity} must be visible in the viewport`,
    }).toBe(true);

    const coveredAtVisibleCenter = await page.evaluate(selector => {
      const node = document.activeElement;
      if (!(node instanceof HTMLElement) || !node.matches(selector)) return true;

      const rect = node.getBoundingClientRect();
      const left = Math.max(rect.left, 0);
      const right = Math.min(rect.right, innerWidth);
      const topEdge = Math.max(rect.top, 0);
      const bottom = Math.min(rect.bottom, innerHeight);
      const x = (left + right) / 2;
      const y = (topEdge + bottom) / 2;
      const top = document.elementFromPoint(x, y);
      return Boolean(top && top !== node && !node.contains(top) && !top.contains(node));
    }, keyboardPrimarySelector);

    expect(coveredAtVisibleCenter, `${label} keyboard-focused ${focused.identity} must not be obscured at its visible center`).toBe(false);
    seen.add(focused.identity);
  }

  expect(seen.size, `${label} keyboard traversal should reach every declared primary tab stop`).toBe(expected);
}

for (const route of routes) {
  test(`${route} satisfies automation-only static HCI invariants`, async ({ page }, testInfo) => {
    const response = await page.goto(routeUrl(route), { waitUntil: 'networkidle' });
    expect(response?.status(), `${route} response`).toBeLessThan(400);

    const title = (await page.title()).trim();
    expect(title.length, `${route} needs a descriptive document title`).toBeGreaterThanOrEqual(4);
    expect(title, `${route} title should identify VanillaCord`).toMatch(/VanillaCord/i);

    const h1 = page.locator('h1');
    await expect(h1, `${route} should have one page-purpose heading`).toHaveCount(1);
    expect((await h1.textContent())?.trim().length || 0, `${route} H1 should not be empty`).toBeGreaterThanOrEqual(3);

    const headings = await page.locator('h1,h2,h3,h4,h5,h6').evaluateAll(nodes => nodes.map(node => Number(node.tagName.slice(1))));
    for (let index = 1; index < headings.length; index += 1) {
      expect(headings[index] - headings[index - 1], `${route} heading levels should not skip downward`).toBeLessThanOrEqual(1);
    }

    const standaloneActions = page.locator('a[href], button');
    for (let index = 0; index < await standaloneActions.count(); index += 1) {
      const name = await standaloneActions.nth(index).evaluate(node => {
        const explicit = node.getAttribute('aria-label')?.trim();
        return (explicit || node.textContent || '').replace(/\s+/g, ' ').trim();
      });
      expect(name.length, `${route} standalone action ${index} should not be unnamed`).toBeGreaterThan(0);
      expect(genericStandaloneName.test(name), `${route} standalone action ${index} should not use a context-free generic label: ${name}`).toBe(false);
    }

    await assertPrimaryTargets(page, `${testInfo.project.name} ${route}`);
    if (testInfo.project.name.startsWith('desktop-')) {
      await assertKeyboardFocusPath(page, `${testInfo.project.name} ${route}`);
    }

    const icons = page.locator('.theme-icon');
    await expect(icons, `${route} theme icons`).toHaveCount(3);
    for (let index = 0; index < await icons.count(); index += 1) {
      await expect(icons.nth(index)).toHaveAttribute('viewBox', '0 0 24 24');
      const box = await icons.nth(index).evaluate(node => {
        const rect = node.getBoundingClientRect();
        return { width: rect.width, height: rect.height };
      });
      expect(box.width, `${route} theme icon ${index} rendered width`).toBeGreaterThan(0);
      expect(box.height, `${route} theme icon ${index} rendered height`).toBeGreaterThan(0);
      expect(Math.abs(box.width / box.height - 1), `${route} theme icon ${index} should not be distorted`).toBeLessThan(0.05);
    }
  });
}

test('320px responsive layout keeps keyboard-primary controls reachable and unobscured', async ({ page }, testInfo) => {
  test.skip(!testInfo.project.name.startsWith('desktop-'), 'Playwright mobile device emulation does not model OS-level external-keyboard focus scrolling');
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto(routeUrl('/'), { waitUntil: 'networkidle' });
  await assertKeyboardFocusPath(page, `${testInfo.project.name} 320px homepage`);
});
