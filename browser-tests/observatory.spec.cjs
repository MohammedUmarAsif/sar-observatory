const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const fs = require('node:fs');

for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
  test(`render and interactions ${viewport.width}`, async ({ page }) => {
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.setViewportSize(viewport);
    await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
    await page.goto('./');
    await page.locator('#quality').scrollIntoViewIfNeeded();
    await expect(page.locator('#experiment')).toBeEnabled();
    await expect(page.locator('#earth-results table')).toBeVisible();
    await expect(page.locator('#load-error')).toBeHidden();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    await page.locator('#experiment').selectOption('doppler');
    await expect(page.locator('#gate-status')).toContainText('localization');
    await page.locator('#experiment').selectOption('velocity-3');
    await expect(page.locator('#gate-status')).toContainText('width');
    await page.locator('[data-stage="compressed"]').click();
    await expect(page.locator('#stage-image')).toHaveAttribute('src', 'assets/compressed.png');
    await page.locator('#angle').fill('60');
    await expect(page.locator('#angle-value')).toHaveText('60°');
    await page.locator('#angle').focus();
    await page.keyboard.press('ArrowLeft');
    await expect(page.locator('#angle-value')).toHaveText('59°');
    await page.locator('#corrupt').click();
    await expect(page.locator('#corrupt-output')).toContainText('NaN/Inf');
    await page.locator('#earth-method').selectOption('otsu');
    await expect(page.locator('#earth-after')).toHaveAttribute('src', 'assets/earth-after-otsu.png');
    await page.getByText('Try a live threshold on the display grid').click();
    await page.locator('#threshold').fill('-18');
    await expect(page.locator('#live-result')).toContainText('Live 40 m');
    await page.locator('#theme').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    for (const image of await page.locator('img').all()) {
      await image.scrollIntoViewIfNeeded();
      await expect(image).toHaveJSProperty('complete', true);
      expect(await image.evaluate(element => element.naturalWidth)).toBeGreaterThan(0);
    }
    const access = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
    expect(access.violations).toEqual([]);
    await page.locator('#theme').click();
    const dark = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
    expect(dark.violations).toEqual([]);
    fs.mkdirSync('verification/screenshots', { recursive: true });
    await page.screenshot({ path: `verification/screenshots/${viewport.width}-dark.png`, fullPage: true });
    await page.locator('#theme').click();
    await page.screenshot({ path: `verification/screenshots/${viewport.width}-light.png`, fullPage: true });
    expect(errors).toEqual([]);
    await page.goto('notes/report.html');
    await expect(page.locator('h1')).toHaveText('Research report');
    await page.reload();
    await expect(page.locator('h1')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  });
}

test('all local links and artifacts resolve', async ({ page, request }) => {
  await page.goto('./');
  const paths = await page.locator('a[href]').evaluateAll(anchors => [...new Set(anchors.map(a => a.getAttribute('href')).filter(href => href && !href.startsWith('http') && !href.startsWith('#')))]);
  for (const path of paths) expect((await request.get(path)).ok()).toBeTruthy();
});

test('browser geometry and mask math', async () => {
  const { geometry, thresholdMask } = await import('../site/science.mjs');
  expect(geometry(45).groundM).toBeCloseTo(1000, 8);
  expect(geometry(45).groundWidthM / geometry(45).slantWidthM).toBeCloseTo(Math.SQRT2, 8);
  expect(thresholdMask([[-20,-10],[-15,-30]], [[1,1],[0,1]], -17).fraction).toBeCloseTo(2/3, 8);
  expect(() => geometry(0)).toThrow();
});
