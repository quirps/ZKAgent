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
- For salary: only mark is_disclosed=true if actual numbers are present
- For seniority: infer from title and requirements if not stated explicitly
- For skills: separate required vs nice-to-have carefully
- Never hallucinate information not present in the posting
- If a field is genuinely unknown, use null or the UNKNOWN enum value
- Use confidence (0.0-1.0) to reflect how complete and unambiguous the posting was
- Use extraction_notes to flag contradictions, unusual patterns, or low-confidence fields
YOU MUST RESPOND WITH ONLY A JSON OBJECT. No markdown, no backticks, no explanation.
Start your response with { and end with }."""


def extract_job_posting(raw_text: str) -> JobPosting:
    """
    Extract a structured JobPosting from raw job posting text.
    Includes retry logic on validation failure.
    """
    schema = JobPosting.model_json_schema()

    messages = [
        {
            "role": "user",
            "content": f"""Extract the job posting information from this text and return JSON matching this schema exactly:

Schema:
{json.dumps(schema, indent=2)}

Job Posting:
{raw_text}

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
            error_str = str(e).lower()

            if "429" in str(e) or "rate limit" in error_str:
                wait = 10 * (attempt + 1)  # 10s, 20s, 30s
                logger.warning(f"Rate limited, waiting {wait}s before retry")
                time.sleep(wait)
            else:
                logger.error(f"Unexpected error attempt {attempt + 1}: {e}")
                time.sleep(2**attempt)

    raise RuntimeError(
        f"Extraction failed after {max_retries} attempts. Last error: {last_error}"
    )
