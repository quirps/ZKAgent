# src/observability/tracer.py
import os
from pathlib import Path
from langfuse import Langfuse
from langfuse.types import TraceContext
from dotenv import load_dotenv
from loguru import logger

load_dotenv(Path(__file__).parent.parent.parent / ".env")


# Initialize eagerly at import time
def _init_client() -> Langfuse | None:
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_BASE_URL", os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com"))

    if not public_key or not secret_key:
        logger.warning("Langfuse keys not set — tracing disabled")
        return None

    try:
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        logger.info(f"Langfuse client initialized → {host}")
        return client
    except Exception as e:
        logger.warning(f"Langfuse init failed: {e}")
        return None


_client: Langfuse | None = _init_client()


def get_langfuse() -> Langfuse | None:
    return _client


def trace_llm_call(
    name: str,
    model: str,
    messages: list[dict],
    response_text: str,
    tokens_in: int,
    tokens_out: int,
    latency_ms: float,
    trace_id: str = None,
    metadata: dict = None,
):
    if not _client:
        return

    try:
        ctx = TraceContext(trace_id=trace_id) if trace_id else None
        obs = _client.start_observation(
            trace_context=ctx,
            name=name,
            as_type="generation",
            input=messages,
            output=response_text,
            model=model,
            usage_details={"input": tokens_in, "output": tokens_out},
            metadata={"latency_ms": latency_ms, **(metadata or {})},
        )
        obs.end()
        _client.flush()
        logger.debug(f"Traced: {name} trace_id={trace_id}")
    except Exception as e:
        logger.warning(f"Langfuse trace failed (non-blocking): {e}")


def flush():
    """Flush pending traces — call at process shutdown."""
    if _client:
        _client.flush()


def create_trace(name: str, metadata: dict = None) -> object:
    if not _client:
        return None

    try:
        obs = _client.start_observation(name=name, as_type="span", metadata=metadata or {})
        obs.end()
        return obs
    except Exception as e:
        logger.warning(f"Failed to create trace: {e}")
        return None
