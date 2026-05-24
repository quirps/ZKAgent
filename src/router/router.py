import time
import litellm
from dataclasses import dataclass
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

from src.router.classifier import classify_task
from src.router.policy import PolicyEngine

policy_engine = PolicyEngine()


@dataclass
class RouteResult:
    task_type: str
    model_used: str
    response: str
    tokens_in: int
    tokens_out: int
    latency_ms: float
    estimated_cost_usd: float
    fallback_used: bool


# rough cost per 1M tokens - update as pricing changes
COST_PER_1M = {
    "groq/llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "gemini/gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    rates = COST_PER_1M.get(model, {"input": 1.0, "output": 1.0})
    return (tokens_in * rates["input"] + tokens_out * rates["output"]) / 1_000_000


def route(request: str, messages: list[dict] = None) -> RouteResult:
    """
    Classify the requst, resolve the policy, dispatch to the correct model and return a structured result with cost tracking.
    """
    # Step 1 Classify
    task_type = classify_task(request)
    policy = policy_engine.resolve(task_type)

    logger.info(
        f"Routing | task={task_type} "
        f"primary={policy.primary} "
        f"fallback={policy.fallback}"
    )

    # build messages if not provided
    if messages is None:
        messages = [{"role": "user", "content": request}]

    # Step 2 dispatch with fallback
    fallback_used = False
    model_used = policy.primary

    start = time.perf_counter()

    try:
        response = litellm.completion(
            messages=messages,
            model=policy.primary,
            temperature=0,
            max_tokens=policy.max_tokens,
        )
    except Exception as e:
        logger.warning(f"Primary model failed: {e} - trying fallback")
        fallback_used = True
        model_used = policy.fallback

        response = litellm.completion(
            messages=messages,
            model=model_used,
            temperature=0,
            max_tokens=policy.max_tokens,
        )
    latency_ms = (time.perf_counter() - start) * 1000
    usage = response.usage
    content = response.choices[0].message.content

    cost = estimate_cost(model_used, usage.prompt_tokens, usage.completion_tokens)

    logger.info(
        f"Completed | model={model_used} "
        f"tokens_in={usage.prompt_tokens} "
        f"tokens_out={usage.completion_tokens} "
        f"latency={latency_ms:.0f}ms "
        f"cost=${cost:.6f} "
        f"fallback={fallback_used}"
    )

    return RouteResult(
        task_type=task_type,
        model_used=model_used,
        response=content,
        tokens_in=usage.prompt_tokens,
        tokens_out=usage.completion_tokens,
        latency_ms=latency_ms,
        estimated_cost_usd=cost,
        fallback_used=fallback_used,
    )
