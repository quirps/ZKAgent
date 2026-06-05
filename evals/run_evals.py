import json
import sys
from pathlib import Path

# Change import at top
from datetime import datetime, UTC
from loguru import logger

from rich.console import Console
from rich.table import Table

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.extractor import extract_job_posting
from evals.scorer import score_extraction, EvalResult

console = Console()

PASS_THRESHOLD = 0.75  # minimum average score to pass CI
DATASET_PATH = Path(__file__).parent / "datasets" / "extraction_evals.json"


def run_evals() -> tuple[float, list[EvalResult]]:
    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    results: list[EvalResult] = []

    table = Table(title="Extraction Eval Results")
    table.add_column("ID")
    table.add_column("Pass")
    table.add_column("Score")
    table.add_column("Checks")
    table.add_column("Failures")

    for case in dataset:
        logger.info(f"Running eval: {case['id']}")

        try:
            actual = extract_job_posting(case["input"])
            actual_dict = actual.model_dump()
        except Exception as e:
            logger.error(f"Eval {case['id']} extraction failed: {e}")
            results.append(
                EvalResult(
                    eval_id=case["id"],
                    passed=False,
                    score=0.0,
                    checks_passed=0,
                    checks_total=1,
                    failures=[f"Extraction exception: {e}"],
                )
            )
            continue

        result = score_extraction(case, actual_dict)
        results.append(result)

        table.add_row(
            result.eval_id,
            "✅" if result.passed else "❌",
            f"{result.score:.2f}",
            f"{result.checks_passed}/{result.checks_total}",
            "\n".join(result.failures) if result.failures else "-",
        )

    console.print(table)

    avg_score = sum(r.score for r in results) / len(results)
    passed_count = sum(1 for r in results if r.passed)

    console.print(f"\n[bold]Average score:[/bold] {avg_score:.2f}")
    console.print(f"[bold]Cases passed:[/bold] {passed_count}/{len(results)}")
    console.print(f"[bold]Threshold:[/bold] {PASS_THRESHOLD}")

    # Write results to disk for CI artifact
    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "average_score": avg_score,
        "passed": avg_score >= PASS_THRESHOLD,
        "cases": [
            {
                "id": r.eval_id,
                "passed": r.passed,
                "score": r.score,
                "failures": r.failures,
            }
            for r in results
        ],
    }

    output_path = (
        Path("traces") / f"eval_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
    )
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Eval results written: {output_path}")
    return avg_score, results


if __name__ == "__main__":
    avg_score, results = run_evals()

    # Exit code 1 if below threshold — CI will catch this
    if avg_score < PASS_THRESHOLD:
        console.print(
            f"\n[bold red]FAILED — score {avg_score:.2f} below threshold {PASS_THRESHOLD}[/bold red]"
        )
        sys.exit(1)
    else:
        console.print(f"\n[bold green]PASSED — score {avg_score:.2f}[/bold green]")
        sys.exit(0)
