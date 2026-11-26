import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 120_000,
  fullyParallel: false,
  workers: 2,
  reporter: [['list']],
  use: { baseURL: 'http://localhost:3100', browserName: 'chromium' },
  // Serves the static export (run `npm run build` first).
  webServer: { command: 'npx serve out -l 3100 --no-clipboard', url: 'http://localhost:3100/overview/', reuseExistingServer: true, timeout: 60_000 },
});
