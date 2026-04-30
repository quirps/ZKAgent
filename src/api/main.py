# src/api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.extraction.extractor import extract_job_posting
from src.extraction.models import JobPosting
from loguru import logger
import time
import traceback

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

ExtractionResponse.model_rebuild()

@app.get("/health")
def health():
    import os
    return {
        "status": "ok",
        "groq_key_present": bool(os.getenv("GROQ_API_KEY")),
        "google_key_present": bool(os.getenv("GOOGLE_API_KEY")),
    }

@app.post("/extract", response_model=ExtractionResponse)
def extract(request: ExtractionRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=422, detail="text field cannot be empty")

    try:
        start = time.perf_counter()
        result = extract_job_posting(request.text)
        latency_ms = (time.perf_counter() - start) * 1000
        return ExtractionResponse(result=result, latency_ms=latency_ms)
    except Exception as e:
        logger.error(f"Extraction failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))