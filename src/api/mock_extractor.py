from src.extraction.models import JobPosting, SeniorityLevel, RemotePolicy, SalaryRange


def mock_extract_job_posting(raw_text: str) -> JobPosting:
    """
    Deterministic mock extractor for CI testing.
    Returns predictable responses based on input content.
    No LLM calls made.
    """
    text_lower = raw_text.lower().strip()

    # Empty/whitespace — should never reach here due to API validation
    if not text_lower:
        raise ValueError("Empty input")

    # Gibberish detection — no recognizable job keywords
    job_keywords = [
        "engineer",
        "developer",
        "manager",
        "analyst",
        "salary",
        "remote",
        "hybrid",
        "skills",
        "experience",
        "python",
        "javascript",
        "required",
        "role",
        "position",
    ]
    has_job_content = any(kw in text_lower for kw in job_keywords)

    if not has_job_content:
        return JobPosting(
            role_title="unknown",
            company="unknown",
            seniority=SeniorityLevel.UNKNOWN,
            remote_policy=RemotePolicy.UNKNOWN,
            location=None,
            salary=SalaryRange(is_disclosed=False),
            required_skills=[],
            nice_to_have_skills=[],
            years_experience_required=None,
            summary="",
            confidence=0.1,
            extraction_notes=["Input does not appear to be a job posting"],
        )

    # Conflicting signals detection
    has_conflicts = (
        ("senior" in text_lower and "entry level" in text_lower)
        or ("senior" in text_lower and "new grad" in text_lower)
        or ("required" in text_lower and "or maybe required" in text_lower)
    )

    # Currency detection
    is_eur = "€" in raw_text or "eur" in text_lower
    currency = "EUR" if is_eur else "USD"

    # Salary detection
    import re

    salary_numbers = re.findall(
        r"[\$€£]?\s*(\d{2,3}(?:,\d{3})?(?:k)?)", raw_text, re.IGNORECASE
    )
    has_salary = len(salary_numbers) >= 1

    def parse_salary(s: str) -> int:
        s = s.replace(",", "").replace("k", "000").replace("K", "000")
        return int(s)

    min_val, max_val = None, None
    if has_salary and len(salary_numbers) >= 2:
        try:
            vals = sorted([parse_salary(s) for s in salary_numbers[:2]])
            min_val, max_val = vals[0], vals[1]
        except Exception:
            pass
    elif has_salary:
        try:
            min_val = parse_salary(salary_numbers[0])
        except Exception:
            pass

    return JobPosting(
        role_title=(
            "Senior Python Engineer" if "python" in text_lower else "Software Engineer"
        ),
        company="Acme Corp" if "acme" in text_lower else "unknown",
        seniority=SeniorityLevel.UNKNOWN if has_conflicts else SeniorityLevel.SENIOR,
        remote_policy=(
            RemotePolicy.REMOTE if "remote" in text_lower else RemotePolicy.HYBRID
        ),
        location=(
            "Paris"
            if "paris" in text_lower
            else "New York" if "nyc" in text_lower else None
        ),
        salary=SalaryRange(
            min_value=min_val,
            max_value=max_val,
            currency=currency,
            is_disclosed=has_salary,
        ),
        required_skills=["python"] if "python" in text_lower else ["javascript"],
        summary=(
            "Senior Python Engineer role"
            if "python" in text_lower
            else "Software Engineer role"
        ),
        nice_to_have_skills=[],
        years_experience_required=None,
        confidence=0.75 if has_conflicts else 0.95,
        extraction_notes=(
            [
                "Conflicting seniority signals detected",
                "Experience requirements ambiguous",
            ]
            if has_conflicts
            else []
        ),
    )
