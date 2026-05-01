from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from src.extraction.models import JobPosting
from typing import Callable
import time

app = FastAPI(title="Job Extraction API", version="0.1.0")


class ExtractionRequest(BaseModel):
    text: str


class ExtractionResponse(BaseModel):
    result: JobPosting
    latency_ms: float
    model_config = {"arbitrary_types_allowed": True}


ExtractionResponse.model_rebuild()


# Default extractor — uses real LLM
def get_extractor():
    import os
    from dotenv import load_dotenv
    from pathlib import Path
    from loguru import logger

    load_dotenv(Path(__file__).parent.parent.parent / ".env")

    use_mock = os.getenv("USE_MOCK_EXTRACTOR", "").lower() == "true"
    logger.info(f"Extractor mode: {'MOCK' if use_mock else 'LIVE'}")

    if use_mock:
        from src.api.mock_extractor import mock_extract_job_posting

        return mock_extract_job_posting
    from src.extraction.extractor import extract_job_posting

    return extract_job_posting


@app.get("/health")
def health():
    import os

    return {
        "status": "ok",
        "groq_key_present": bool(os.getenv("GROQ_API_KEY")),
        "google_key_present": bool(os.getenv("GOOGLE_API_KEY")),
    }


@app.post("/extract", response_model=ExtractionResponse)
def extract(request: ExtractionRequest, extractor: Callable = Depends(get_extractor)):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=422, detail="text field cannot be empty")

    try:
        start = time.perf_counter()
        result = extractor(request.text)
        latency_ms = (time.perf_counter() - start) * 1000
        return ExtractionResponse(result=result, latency_ms=latency_ms)
    except Exception as e:
        from loguru import logger
        import traceback

        logger.error(f"Extraction failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
