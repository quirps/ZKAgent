from src.extraction.extractor import extract_job_posting
from rich import print as rprint

# Real-world messy job posting
raw_posting = """
About the Role
We're looking for a Senior or Staff engineer to join our infra team. 
You'll own our data pipeline and help us scale to 10x our current load.

We're a remote-first company but do ask folks to be within US timezones.

What you'll do:
- Design and implement scalable distributed systems
- Lead architecture decisions for our backend services  
- Mentor junior engineers and conduct code reviews

What we're looking for:
- 6+ years of backend engineering experience
- Strong Python and Go skills (Python is a must, Go is a plus)
- Experience with Kafka, Kubernetes, and PostgreSQL
- Experience with Spark or Flink would be a nice bonus
- Nice to have: experience with dbt or data warehousing

We offer $180,000 - $240,000 depending on experience. 
Benefits include equity, 401k, and unlimited PTO.

Location: Remote (US timezones preferred)
"""

result = extract_job_posting(raw_posting)
rprint(result)
print(f"\nRequired skills count: {len(result.required_skills)}")
print(f"Salary disclosed: {result.salary.is_disclosed}")
print(f"Seniority: {result.seniority.value}")