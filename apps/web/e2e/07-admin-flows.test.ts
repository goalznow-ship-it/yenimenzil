import { test } from '@playwright/test';

test.describe('IDEALEV.AZ - Admin Flow', () => {
  test('visit admin sections', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.goto('/admin/listings');
    await page.goto('/admin/users');
  });
});