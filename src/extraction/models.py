from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum

class SeniorityLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    UNKNOWN = "unknown"

class RemotePolicy(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"

class SalaryRange(BaseModel):
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    currency: str = "USD"
    is_disclosed: bool = False

class JobPosting(BaseModel):
    confidence: float  # 0.0 - 1.0, model's self-assessed extraction confidence
    extraction_notes: list[str]  # flags like "conflicting seniority signals", "salary currency non-USD"
    role_title: str
    company: str
    seniority: SeniorityLevel
    remote_policy: RemotePolicy
    location: Optional[str] = None
    salary: SalaryRange
    required_skills: list[str]
    nice_to_have_skills: list[str]
    years_experience_required: Optional[int] = None
    summary: str  # 1-2 sentence summary in your own words

    @field_validator("required_skills", "nice_to_have_skills", mode="before")
    @classmethod
    def dedupe_skills(cls, v):
        return list(dict.fromkeys([s.strip().lower() for s in v]))