import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  await page.goto('http://localhost:2222/?gutter-final=1', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);
  
  // Check computed width of left aside
  const computedWidth = await page.evaluate(() => {
    const aside = document.querySelector('aside:first-child');
    if (!aside) return 'not found';
    return window.getComputedStyle(aside).getPropertyValue('width');
  });
  console.log('Left aside computed width:', computedWidth);
  
  // Check main display and grid
  const mainDisplay = await page.evaluate(() => {
    const main = document.querySelector('main');
    if (!main) return 'not found';
    return window.getComputedStyle(main).getPropertyValue('display');
  });
  console.log('Main display:', mainDisplay);
  
  const gridColumns = await page.evaluate(() => {
    const main = document.querySelector('main');
    if (!main) return 'not found';
    return window.getComputedStyle(main).getPropertyValue('grid-template-columns');
  });
  console.log('Main grid-template-columns:', gridColumns);
  
  await browser.close();
})().catch(e => console.error('Error:', e));
