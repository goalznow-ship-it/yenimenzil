import { test, expect } from '@playwright/test';

test.describe('IDEALEV.AZ - Listings Flow', () => {
  test('add property page loads', async ({ page }) => {
    await page.goto('/add-property');
    await expect(page).toHaveTitle(/IdealEv/);
  });

  test('search page loads', async ({ page }) => {
    await page.goto('/search?deal=sale');
    await expect(page).toHaveTitle(/IdealEv/);
  });
});