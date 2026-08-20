import { test } from '@playwright/test';

test('check homepage errors', async ({ page }) => {
  const errors: string[] = [];
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];
  const badResponses: string[] = [];

  page.on('pageerror', (err) => {
    errors.push(err.message);
    console.log('PAGE ERROR:', err);
  });

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.log('CONSOLE ERROR:', msg.text());
    }
  });

  page.on('requestfailed', (req) => {
    failedRequests.push(`${req.method()} ${req.url()} ${req.failure()?.errorText || 'failed'}`);
    console.log('REQUEST FAILED:', req.method(), req.url(), req.failure());
  });

  page.on('response', (res) => {
    if (res.status() >= 400) {
      badResponses.push(`${res.status()} ${res.url()}`);
      console.log('BAD RESPONSE:', res.status(), res.url());
    }
  });

  await page.goto('http://localhost:2222', { waitUntil: 'networkidle' });

  // Wait a bit for any delayed errors
  await page.waitForTimeout(2000);

  // Output collected info
  console.log('=== COLLECTED ERRORS ===');
  console.log('PAGEERRORS:', errors);
  console.log('CONSOLE ERRORS:', consoleErrors);
  console.log('FAILED REQUESTS:', failedRequests);
  console.log('BAD RESPONSES:', badResponses);

  // Also get the page content to see if error boundary is present
  const content = await page.content();
  if (content.includes('Nəsə səhv getdi')) {
    console.log('ERROR BOUNDARY PRESENT: Nəsə səhv getdi found');
  } else {
    console.log('ERROR BOUNDARY NOT FOUND');
  }
});
