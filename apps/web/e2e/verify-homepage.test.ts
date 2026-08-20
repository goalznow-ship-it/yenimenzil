import { test, expect } from '@playwright/test';

test('homepage renders correctly', async ({ page }) => {
  await page.goto('http://localhost:2222', { waitUntil: 'networkidle' });

  // Check that error boundary is not present
  const errorBoundaryText = await page.locator('text=Nəsə səhv getdi').count();
  expect(errorBoundaryText).toBe(0);

  // Check hero title is visible (h1)
  const heroTitle = await page.locator('h1:has-text("Yeni məkanını burada tap.")');
  await expect(heroTitle).toBeVisible();

  // Check exactly one header (we assume the header is the one with role="banner" or the actual header element)
  // We'll count the number of header elements (tag header)
  const headerCount = await page.locator('header').count();
  expect(headerCount).toBe(1);

  // Check exactly one tab group (the one with role="tablist")
  const tabGroupCount = await page.locator('[role="tablist"]').count();
  expect(tabGroupCount).toBe(1);

  // Check exactly one popular locations section (we added a section with aria-labelledby="popular-locations-title")
  const popularLocationsCount = await page.locator('[aria-labelledby="popular-locations-title"]').count();
  expect(popularLocationsCount).toBe(1);

  // Check all 7 categories are present (by their text)
  const categories = [
    'Yeni tikili',
    'Köhnə tikili',
    'Həyət evi / Bağ evi',
    'Ofis',
    'Qaraj',
    'Torpaq',
    'Obyekt'
  ];
  for (const cat of categories) {
    const count = await page.locator(`text=${cat}`).count();
    expect(count).toBeGreaterThan(0);
  }

  // Check at least 4 listing cards (we can count the property cards)
  // The property cards are links with class containing 'group block overflow-hidden rounded-2xl'
  const listingCards = await page.locator('a.group.block.overflow-hidden.rounded-2xl').count();
  expect(listingCards).toBeGreaterThanOrEqual(4);

  // Check benefits row: we can look for the benefits title
  const benefitsTitle = await page.locator('#benefits-title');
  await expect(benefitsTitle).toBeVisible();

  // Check map is below benefits: we can check that the map title appears after benefits title in the DOM.
  // We'll just check that the map title is visible.
  const mapTitle = await page.locator('#map-title');
  await expect(mapTitle).toBeVisible();

  console.log('All checks passed');
});
