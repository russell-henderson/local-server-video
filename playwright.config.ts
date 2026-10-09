import {defineConfig, devices} from '@playwright/test';
import path from 'node:path';

const python = process.env.LVS_TEST_PYTHON || (process.platform === 'win32' ? path.resolve('.venv/Scripts/python.exe') : 'python');
export default defineConfig({
  testDir: './tests/browser',
  fullyParallel: false,
  workers: 1,
  timeout: 30000,
  expect: {timeout: 10000, toHaveScreenshot: {animations: 'disabled', maxDiffPixelRatio: 0.002}},
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', {open: 'never'}]],
  use: {
    baseURL: 'http://127.0.0.1:8765', trace: 'retain-on-failure', screenshot: 'only-on-failure',
    locale: 'en-US', timezoneId: 'UTC', colorScheme: 'dark', reducedMotion: 'reduce'
  },
  webServer: {
    command: '"' + python + '" scripts/browser_server.py --port 8765',
    url: 'http://127.0.0.1:8765/ping', reuseExistingServer: false, timeout: 120000
  },
  projects: [
    {name: 'desktop-chromium', use: {...devices['Desktop Chrome'], viewport: {width:1440,height:900}}},
    {name: 'desktop-firefox', use: {...devices['Desktop Firefox'], viewport: {width:1440,height:900}}},
    {name: 'desktop-webkit', use: {...devices['Desktop Safari'], viewport: {width:1440,height:900}}},
    {name: 'narrow-desktop', use: {browserName:'chromium', viewport:{width:1024,height:768}}},
    {name: 'mobile-chromium', use: {...devices['Pixel 5'], viewport:{width:360,height:800}}},
    {name: 'mobile-webkit', use: {...devices['iPhone 13'], viewport:{width:390,height:844}}},
    {name: 'tablet', use: {...devices['iPad Mini'], viewport:{width:768,height:1024}}},
    {name: 'quest-like', use: {browserName:'chromium', viewport:{width:1200,height:800}, hasTouch:true,
      userAgent:'Mozilla/5.0 (Linux; Android 12; Quest 2) AppleWebKit/537.36 Chrome/145.0.0.0 OculusBrowser/40.0 Safari/537.36'}}
  ]
});
