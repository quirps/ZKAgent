import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 60000,        // LLM calls are slow, give them room
  retries: 1,            // one retry for LLM non-determinism
  workers: 1,            // sequential — avoid hammering the rate limit
  reporter: 'list',

  use: {
    baseURL: 'http://localhost:8000',
    extraHTTPHeaders: {
      'Content-Type': 'application/json',
    },
  },

  // No browser projects — pure API testing
  projects: [
    {
      name: 'api',
      use: {},
    }
  ],
});