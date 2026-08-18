import { test } from '@playwright/test';

test.describe('IDEALEV.AZ - Saved Searches Flow', () => {
  test('create saved search', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'testuser@idealev.az');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('text=Daxil ol');
    await page.waitForLoadState('networkidle');
    await page.goto('/search?deal=sale');
  });

  test('toggle alert for saved search', async ({ page }) => {
    await page.goto('/saved-searches');
  });

  test('delete saved search', async ({ page }) => {
    await page.goto('/saved-searches');
  });
});