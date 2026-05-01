import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 60000,
  retries: 2,          // bump to 2 retries
  workers: 1,
  reporter: 'list',

  use: {
    baseURL: 'http://localhost:8000',
    extraHTTPHeaders: {
      'Content-Type': 'application/json',
    },
  },

  projects: [
    {
      name: 'api',
      use: {},
    }
  ],
});