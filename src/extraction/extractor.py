import time
import litellm
from pydantic import ValidationError
from loguru import logger
from dotenv import load_dotenv
from pathlib import Path
import json

# Explicit path — works regardless of working directory
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from config.settings import settings
from .models import JobPosting

SYSTEM_PROMPT = """You are a precise job posting parser.
Extract structured information from job postings exactly as described.

CRITICAL RULES:
- For salary: only mark is_disclosed=true if actual numbers are present
- For seniority: if the posting contains contradictory signals (e.g. 'Senior'
  AND 'Entry Level Welcome' or 'new grads welcome'), you MUST set
  seniority=unknown and add a note to extraction_notes explaining the conflict
- For confidence: if ANY field is ambiguous or contradictory, confidence MUST
  be below 0.85. A posting with contradictions cannot score above 0.85.
- For extraction_notes: ALWAYS populate this list when you detect contradictions,
  missing fields, or ambiguous information. An empty list means the posting
  was completely unambiguous.
- For skills: separate required vs nice-to-have carefully
- Never hallucinate information not present in the posting
- If a field is genuinely unknown, use null or the UNKNOWN enum value

EXAMPLE OF CONTRADICTORY SENIORITY — you must handle this pattern:
Input: "Senior Software Engineer - New Grads Welcome. 0-5 years experience."
Correct output must have:
  seniority: "unknown"
  confidence: 0.6
  extraction_notes: ["Contradictory seniority signals: title says Senior but posting welcomes new grads and lists 0 years minimum experience"]

YOU MUST RESPOND WITH ONLY A JSON OBJECT. No markdown, no backticks, no explanation.
Start your response with { and end with }."""

CONTRADICTION_PATTERNS = [
    ("senior", "entry level"),
    ("senior", "new grad"),
    ("senior", "junior"),
    ("lead", "entry level"),
    ("principal", "entry level"),
]


def detect_contradictions(text: str) -> list[str]:
    """
    Deterministic pre-check for known contradiction patterns.
    Injects explicit warnings into the prompt when found.
    """
    text_lower = text.lower()
    found = []
    for pattern_a, pattern_b in CONTRADICTION_PATTERNS:
        if pattern_a in text_lower and pattern_b in text_lower:
            found.append(
                f"CONTRADICTION DETECTED: posting contains both "
                f"'{pattern_a}' and '{pattern_b}' — "
                f"seniority MUST be 'unknown', confidence MUST be below 0.7"
            )
    return found


def extract_job_posting(raw_text: str) -> JobPosting:
    """
    Extract a structured JobPosting from raw job posting text.
    Includes retry logic on validation failure.
    """
    schema = JobPosting.model_json_schema()

    contradictions = detect_contradictions(raw_text)
    contradiction_warning = ""
    if contradictions:
        contradiction_warning = (
            "\n\nWARNING — CONTRADICTIONS FOUND:\n" + "\n".join(contradictions) + "\n"
        )

    messages = [
        {
            "role": "user",
            "content": f"""Extract the job posting information from this text and return JSON matching this schema exactly:

Schema:
{json.dumps(schema, indent=2)}

Job Posting:
{raw_text}
{contradiction_warning}
Return only the JSON object, no markdown, no explanation.""",
        }
    ]

    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        start = time.perf_counter()

        try:
            response = litellm.completion(
                model=settings.primary_model,
                messages=messages,
                temperature=0.1,
                fallbacks=[settings.fast_model],
                num_retries=1,
            )

            latency_ms = (time.perf_counter() - start) * 1000
            raw_output = response.choices[0].message.content
            usage = response.usage

            logger.info(
                f"LLM call attempt={attempt + 1} "
                f"latency={latency_ms:.0f}ms "
                f"tokens_in={usage.prompt_tokens} "
                f"tokens_out={usage.completion_tokens}"
            )

            parsed = JobPosting.model_validate_json(raw_output)
            logger.success(f"Extraction succeeded on attempt {attempt + 1}")
            return parsed

        except ValidationError as e:
            last_error = e
            logger.warning(
                f"Validation failed attempt {attempt + 1}: {e.error_count()} errors"
            )

            # Feed the error back into context so the model can self-correct
            messages.append({"role": "assistant", "content": raw_output})
            messages.append(
                {
                    "role": "user",
                    "content": f"That response had validation errors. Fix them and return corrected JSON:\n{e}",
                }
            )

        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error attempt {attempt + 1}: {e}")
            time.sleep(2**attempt)  # 1s, 2s, 4s — simple backoff

    raise RuntimeError(
        f"Extraction failed after {max_retries} attempts. Last error: {last_error}"
    )
