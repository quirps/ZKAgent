import { test, expect } from "@playwright/test";
import { ExtractionPage } from "../pages/ExtractionPage";
import { validPostings } from "../fixtures/jobPostings";

const BASE_URL = "http://localhost:8000";

test.describe("Extraction — Happy Path", () => {
  let page: ExtractionPage;

  test.beforeEach(({ request }) => {
    page = new ExtractionPage(request, BASE_URL);
  });

  test("returns valid schema shape for standard posting", async () => {
    const data = await page.extractAndParse(validPostings.standard);

    expect(data.result).toHaveProperty("role_title");
    expect(data.result).toHaveProperty("salary");
    expect(data.result.salary).toHaveProperty("is_disclosed");
    expect(data.result.required_skills).toBeInstanceOf(Array);
    expect(data.result.confidence).toBeGreaterThan(0);
  });

  test("correctly marks salary as disclosed when numbers present", async () => {
    const data = await page.extractAndParse(validPostings.standard);
    expect(data.result.salary.is_disclosed).toBe(true);
    expect(data.result.salary.min_value).toBeGreaterThan(0);
  });

  test("correctly marks salary as not disclosed when absent", async () => {
    const data = await page.extractAndParse(validPostings.noSalary);
    expect(data.result.salary.is_disclosed).toBe(false);
    expect(data.result.salary.min_value).toBeNull();
  });

  test("preserves non-USD currency without converting", async () => {
    const data = await page.extractAndParse(validPostings.multiCurrency);
    expect(data.result.salary.currency).toBe("EUR");
    expect(data.result.salary.min_value).toBe(90000);
  });

  test("returns latency measurement", async () => {
    const data = await page.extractAndParse(validPostings.standard);
    expect(data.latency_ms).toBeGreaterThan(0);
  });

test.beforeEach(async () => {
  // Respect Groq free tier rate limits in CI (30 RPM = 1 req/2s)
  await new Promise(resolve => setTimeout(resolve, 2500));
});
});



const postingEntries = Object.entries(validPostings) as [string, string][];

for (const [name, text] of postingEntries) {
  test(`posting type '${name}' returns confidence > 0`, async ({ request }) => {
    const page = new ExtractionPage(request, BASE_URL);
    const data = await page.extractAndParse(text);
    expect(data.result.confidence).toBeGreaterThan(0);
  });
}