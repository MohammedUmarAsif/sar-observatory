const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './browser-tests', timeout: 60000, workers: 1,
  use: { baseURL: process.env.SAR_BASE_URL || 'http://127.0.0.1:8080/', headless: true },
  webServer: process.env.SAR_BASE_URL ? undefined : {
    command: 'uv run python -m http.server 8080 --directory site',
    url: 'http://127.0.0.1:8080', reuseExistingServer: true,
  },
});
