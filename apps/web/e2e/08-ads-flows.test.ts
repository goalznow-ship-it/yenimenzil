import { test } from '@playwright/test';

test.describe('IDEALEV.AZ - Advertising Flow', () => {
  test('verify ads render', async ({ page }) => {
    await page.goto('/');
  });
});