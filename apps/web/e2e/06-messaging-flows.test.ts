import { test } from '@playwright/test';

test.describe('IDEALEV.AZ - Messaging Flow', () => {
  test('send message', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'testuser@idealev.az');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('text=Daxil ol');
    await page.waitForLoadState('networkidle');
    await page.goto('/messages');
  });
});