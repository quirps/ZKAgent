import { test, expect } from "@playwright/test";
import { ExtractionPage } from "../pages/ExtractionPage";
import { invalidPostings, validPostings } from "../fixtures/jobPostings";

const BASE_URL = "http://localhost:8000";

test.describe("Edge Cases & Negative Tests", () => {
  let page: ExtractionPage;

  test.beforeEach(({ request }) => {
    page = new ExtractionPage(request, BASE_URL);
  });

  test("returns 422 for empty text", async () => {
    const response = await page.extract(invalidPostings.empty);
    expect(response.status()).toBe(422);
  });

  test("returns 422 for whitespace-only input", async () => {
    const response = await page.extract(invalidPostings.whitespaceOnly);
    expect(response.status()).toBe(422);
  });

  test("conflicting signals produce extraction_notes", async () => {
    const data = await page.extractAndParse(validPostings.conflicting);
    expect(data.result.extraction_notes.length).toBeGreaterThan(0);
  });

  test("conflicting signals produce confidence below 0.9", async () => {
    const data = await page.extractAndParse(validPostings.conflicting);
    expect(data.result.confidence).toBeLessThan(0.9);
  });

  test("gibberish input returns unknown seniority", async () => {
    const data = await page.extractAndParse(invalidPostings.gibberish);
    expect(data.result.seniority).toBe("unknown");
  });
  test.beforeEach(async () => {
  // Respect Groq free tier rate limits in CI (30 RPM = 1 req/2s)
  await new Promise(resolve => setTimeout(resolve, 2500));
});
});