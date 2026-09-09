import { test, expect } from '@playwright/test';

const siteBaseUrl = new URL(process.env.SITE_BASE_URL || 'http://127.0.0.1:4173/');

function routeUrl(route) {
  return new URL(route.replace(/^\/+/, ''), siteBaseUrl).toString();
}

test('theme tooltip supports keyboard dismissal and hover persistence', async ({ page }, testInfo) => {
  await page.goto(routeUrl('/'));

  const system = page.getByRole('radio', { name: 'System' });
  const systemOption = page.locator('.theme-option').filter({ has: system });
  const tooltip = systemOption.locator('.theme-tooltip');

  await system.focus();
  await expect(tooltip, `${testInfo.project.name} focus should reveal the tooltip`).toBeVisible();

  await page.keyboard.press('Escape');
  await expect(tooltip, `${testInfo.project.name} Escape should dismiss the tooltip without moving focus`).toBeHidden();
  await expect(system).toBeFocused();

  await page.keyboard.press('Tab');
  await page.keyboard.press('Shift+Tab');
  await expect(system).toBeFocused();
  await expect(tooltip, `${testInfo.project.name} a new focus encounter should restore the tooltip`).toBeVisible();

  test.skip(!testInfo.project.name.startsWith('desktop-'), 'pointer-hover persistence applies to pointer desktop projects');
  await page.keyboard.press('Tab');
  await systemOption.hover();
  await expect(tooltip, `${testInfo.project.name} hover should reveal the tooltip`).toBeVisible();
  await tooltip.hover();
  await expect(tooltip, `${testInfo.project.name} tooltip must remain visible while the pointer is over it`).toBeVisible();
  await page.mouse.move(0, 0);
  await expect(tooltip, `${testInfo.project.name} leaving the trigger and tooltip should hide it`).toBeHidden();
});
