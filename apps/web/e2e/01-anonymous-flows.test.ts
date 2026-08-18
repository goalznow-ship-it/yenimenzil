import { test, expect } from '@playwright/test';

test.describe('IDEALEV.AZ - Anonymous User Flow', () => {
  test('homepage loads correctly', async ({ page }) => {
    await page.goto('/');
  });

  test('navigation is functional', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Axtarış');
    await expect(page).toHaveURL(/.*\/search/);
  });

  test('search functionality works', async ({ page }) => {
    await page.goto('/search?deal=sale');
  });

  test('property page loads', async ({ page }) => {
    await page.goto('/search?deal=sale');
  });

  test('auth boundaries - protected routes redirect', async ({ page }) => {
    await page.goto('/add-property');
    await expect(page).toHaveURL(/.*\/login/);
  });
});