import { test } from '@playwright/test';

test.describe('IDEALEV.AZ - Favorites Flow', () => {
  test('add property to favorites', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'testuser@idealev.az');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('text=Daxil ol');
    await page.waitForLoadState('networkidle');
    await page.goto('/search?deal=sale');
  });

  test('remove favorite', async ({ page }) => {
    await page.goto('/favorites');
  });

  test('favorites persistence after refresh', async ({ page }) => {
    await page.goto('/favorites');
    await page.reload();
  });
});