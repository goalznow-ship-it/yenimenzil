import { devices } from '@playwright/test';

export default {
  testDir: './apps/web/e2e',
  timeout: 30000,
  retries: 0,
  expect: {
    timeout: 5000
  },
  use: {
    baseURL: 'http://localhost:2222',
    headless: true,
    viewport: { width: 390, height: 844 },
    actionTimeout: 5000,
    navigationTimeout: 30000,
    trace: 'on-first-retry'
  },

  projects: [
    {
      name: 'Chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 390, height: 844 }
      }
    },
    {
      name: 'Mobile Chrome',
      use: {
        ...devices['Pixel 2 XL']
      }
    }
  ]
};