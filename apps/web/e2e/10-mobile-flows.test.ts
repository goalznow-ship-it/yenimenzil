import { test } from '@playwright/test';

test.describe('IDEALEV.AZ - Mobile Responsive', () => {
  test('mobile 390x844 viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
  });

  test('mobile 320x700 viewport', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 700 });
    await page.goto('/');
  });
});