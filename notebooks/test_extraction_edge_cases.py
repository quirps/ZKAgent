from src.extraction.extractor import extract_job_posting
from rich import print as rprint
from loguru import logger

cases = {
    "no_salary": """
        Join our startup as a Python developer. We're building the future of fintech.
        You'll work with our small team on backend services. 2+ years experience needed.
        We offer competitive compensation. Remote OK. Apply at jobs@startup.io
    """,

    "inflated_title": """
        ROCKSTAR NINJA 10x ENGINEER WANTED
        Must know everything. React, Python, Rust, Kubernetes, ML, blockchain, 
        and whatever else we think of. We move fast and break things.
        Salary: exposure and equity (no base disclosed).
        Must be in San Francisco office 5 days a week.
    """,

    "conflicting_signals": """
        Senior Frontend Engineer - Entry Level Welcome
        3-5 years experience preferred but will consider new grads with strong portfolios.
        Skills: JavaScript required. TypeScript nice to have. Or maybe required. 
        We use React mostly but are migrating to Vue. Salary $60k-$180k DOE.
        Hybrid - 2 days in NYC office, rest remote. Or fully remote for right candidate.
    """,

    "non_english_noise": """
        Nous recherchons un ingénieur backend senior.
        Requirements: Python (5+ yrs), FastAPI, PostgreSQL, Docker.
        Salary: €90,000 - €120,000. Location: Paris (hybrid).
        Must have EU work authorization.
    """,

    "empty": "",
}

for case_name, text in cases.items():
    logger.info(f"Testing case: {case_name}")
    print(f"\n{'='*50}")
    print(f"CASE: {case_name}")
    print('='*50)
    
    try:
        result = extract_job_posting(text)
        rprint(result)
    except Exception as e:
        print(f"FAILED: {e}")