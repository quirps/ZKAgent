from dataclasses import dataclass
from loguru import logger


@dataclass
class EvalResult:
    eval_id: str
    passed: bool
    score: float  # 0.0 - 1.0
    checks_passed: int
    checks_total: int
    failures: list[str]


def score_extraction(eval_case: dict, actual: dict) -> EvalResult:
    """
    Deterministic scorer for extraction results.
    Compares actual JobPosting output against expected spec.
    Returns a score and list of specific failures.
    """
    expected = eval_case["expected"]
    eval_id = eval_case["id"]
    failures = []
    checks_passed = 0
    checks_total = 0

    def check(condition: bool, failure_msg: str):
        nonlocal checks_passed, checks_total
        checks_total += 1
        if condition:
            checks_passed += 1
        else:
            failures.append(failure_msg)

    # Seniority check
    if "seniority" in expected:
        check(
            actual.get("seniority") == expected["seniority"],
            f"seniority: expected={expected['seniority']} actual={actual.get('seniority')}",
        )

    # Remote policy check
    if "remote_policy" in expected:
        check(
            actual.get("remote_policy") == expected["remote_policy"],
            f"remote_policy: expected={expected['remote_policy']} actual={actual.get('remote_policy')}",
        )

    # Salary checks
    if "salary" in expected:
        exp_salary = expected["salary"]
        act_salary = actual.get("salary", {})

        if "is_disclosed" in exp_salary:
            check(
                act_salary.get("is_disclosed") == exp_salary["is_disclosed"],
                f"salary.is_disclosed: expected={exp_salary['is_disclosed']} actual={act_salary.get('is_disclosed')}",
            )

        if "currency" in exp_salary:
            check(
                act_salary.get("currency") == exp_salary["currency"],
                f"salary.currency: expected={exp_salary['currency']} actual={act_salary.get('currency')}",
            )

        if "min_value" in exp_salary:
            check(
                act_salary.get("min_value") == exp_salary["min_value"],
                f"salary.min_value: expected={exp_salary['min_value']} actual={act_salary.get('min_value')}",
            )

        if "max_value" in exp_salary:
            check(
                act_salary.get("max_value") == exp_salary["max_value"],
                f"salary.max_value: expected={exp_salary['max_value']} actual={act_salary.get('max_value')}",
            )

    # Required skills — subset check (actual must contain all expected)
    if "required_skills_contains" in expected:
        actual_skills = set(actual.get("required_skills", []))
        for skill in expected["required_skills_contains"]:
            check(skill.lower() in actual_skills, f"required_skills missing: {skill}")

    # Confidence bounds
    if "confidence_min" in expected:
        check(
            actual.get("confidence", 0) >= expected["confidence_min"],
            f"confidence too low: expected>={expected['confidence_min']} actual={actual.get('confidence')}",
        )

    if "confidence_max" in expected:
        check(
            actual.get("confidence", 1) <= expected["confidence_max"],
            f"confidence too high: expected<={expected['confidence_max']} actual={actual.get('confidence')}",
        )

    # Extraction notes non-empty
    if expected.get("extraction_notes_nonempty"):
        check(
            len(actual.get("extraction_notes", [])) > 0,
            "extraction_notes expected to be non-empty",
        )

    score = checks_passed / checks_total if checks_total > 0 else 0.0
    passed = len(failures) == 0

    return EvalResult(
        eval_id=eval_id,
        passed=passed,
        score=score,
        checks_passed=checks_passed,
        checks_total=checks_total,
        failures=failures,
    )
