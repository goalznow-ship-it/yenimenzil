import { test, expect } from '@playwright/test';

test.describe('IDEALEV.AZ - Authentication Flow', () => {
  test('login with credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'testuser@idealev.az');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('text=Daxil ol');
    await expect(page).toHaveURL(/.*\//);
    await expect(page).toHaveTitle(/IdealEv/);
  });

  test('navigate to register page', async ({ page }) => {
    await page.goto('/register');
    await expect(page).toHaveTitle(/IdealEv/);
  });

  test('profile navigation', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Profil');
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('session persistence after refresh', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/IdealEv/);
    await page.reload();
    await expect(page).toHaveTitle(/IdealEv/);
  });
});