# Extraction API - Playwright Test Suite

End-to-end QA suite for the Job Posting Extraction API, an LLM-powered service that converts unstructured job posting text into validated, typed JSON using Gemini 2.5 Flash. 

## What this suite covers

| Area  |  Tests |
| ---   |        |
| Api Health  | Reachability, response shape |
| Happy path extraction | Schema validation, salary disclosure, currency handling |
| Data-driven | All posting types return valid confidence scores |
| Edge cases | Empty input, whitespace, gibberish |
| Negative cases | 422 on invalid input, confidence thresholds on ambigious data |

## How to run

Start the API first (from `ai-orchestration`)

\`\`\`bash
uv run uvicorn src.api.main:app --port 8000
\`\`\`

Then run the suite:
\`\`\`bash
npm ci
npx playwright install chromium
npx playwright test
\`\`\`

View the HTML report:
\`\`\`bash
npx playwright show-report
\`\`\`

## How to read results

- **Green** — behavior matches spec
- **Red** — either a regression or an LLM non-determinism issue; 
  check `extraction_notes` in the response for model reasoning
- Flaky confidence threshold tests are expected occasionally — 
  LLMs are non-deterministic, thresholds are probabilistic assertions

## CI

GitHub Actions runs the full suite on every push to main. 
Secrets required: `GOOGLE_API_KEY`, `TAVILY_API_KEY`.