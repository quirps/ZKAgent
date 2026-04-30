from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.extraction.extractor import extract_job_posting
from src.extraction.models import JobPosting
import time

app = FastAPI(
    title="Job Extraction API",
    description="Extracts structured data from raw job postings using LLMs",
    version="0.1.0"
)

class ExtractionRequest(BaseModel):
    text: str

class ExtractionResponse(BaseModel):
    result: JobPosting
    latency_ms: float

    model_config = {"arbitrary_types_allowed": True}

# Force Pydantic to resolve all forward refs now that JobPosting is in scope
ExtractionResponse.model_rebuild()

@app.get("/health")
def health():
    import os
    groq_present = bool(os.getenv("GROQ_API_KEY"))
    google_present = bool(os.getenv("GOOGLE_API_KEY"))
    return {
        "status": "ok",
        "groq_key_present": groq_present,
        "google_key_present": google_present,
    }

@app.post("/extract", response_model=ExtractionResponse)
def extract(request: ExtractionRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=422, detail="text field cannot be empty")

    start = time.perf_counter()
    result = extract_job_posting(request.text)
    latency_ms = (time.perf_counter() - start) * 1000

    return ExtractionResponse(result=result, latency_ms=latency_ms)