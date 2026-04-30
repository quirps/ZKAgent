import { APIRequestContext, expect } from "@playwright/test";

export interface ExtractionResponse {
  result: {
    role_title: string;
    company: string;
    seniority: string;
    remote_policy: string;
    salary: {
      min_value: number | null;
      max_value: number | null;
      currency: string;
      is_disclosed: boolean;
    };
    required_skills: string[];
    nice_to_have_skills: string[];
    confidence: number;
    extraction_notes: string[];
  };
  latency_ms: number;
}

export class ExtractionPage {
  constructor(private request: APIRequestContext, private baseURL: string) {}

  async health() {
    const response = await this.request.get(`${this.baseURL}/health`);
    return response;
  }

  async extract(text: string) {
    const response = await this.request.post(`${this.baseURL}/extract`, {
      data: { text },
      headers: { "Content-Type": "application/json" },
    });
    return response;
  }

  async extractAndParse(text: string): Promise<ExtractionResponse> {
    const response = await this.extract(text);
    expect(response.status()).toBe(200);
    return response.json();
  }
}