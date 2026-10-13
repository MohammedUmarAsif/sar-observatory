const { chromium } = require('@playwright/test');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch();
  fs.mkdirSync('verification/screenshots', { recursive: true });
  for (const width of [1440,390]) {
    const page = await browser.newPage({ viewport: { width, height: width === 1440 ? 1000 : 844 }, colorScheme: 'dark' });
    await page.goto(process.env.SAR_BASE_URL || 'http://127.0.0.1:8080/');
    await page.screenshot({ path: `verification/screenshots/${width}-hero.png` });
    await page.locator('#quality').scrollIntoViewIfNeeded();
    await page.locator('#experiment:not([disabled])').waitFor();
    await page.locator('#quality').screenshot({ path: `verification/screenshots/${width}-quality.png` });
    await page.locator('#earth').screenshot({ path: `verification/screenshots/${width}-earth.png` });
    await page.close();
  }
  await browser.close();
})();
