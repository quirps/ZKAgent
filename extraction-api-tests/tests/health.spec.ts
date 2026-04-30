import { test, expect } from "@playwright/test";
import { ExtractionPage } from "../pages/ExtractionPage";

const BASE_URL = "http://localhost:8000";

test.describe("Health Check", () => {
  test("API is reachable and healthy", async ({ request }) => {
    const page = new ExtractionPage(request, BASE_URL);
    const response = await page.health();
    
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("ok");
  });
});