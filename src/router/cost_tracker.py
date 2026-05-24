import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
from src.router.router import RouteResult


@dataclass
class SessionCosts:
    total_cost_usd: float = 0.0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    calls: int = 0
    by_model: dict = field(default_factory=dict)
    by_task_type: dict = field(default_factory=dict)


class CostTracker:
    """
    Tracks spend across a session and persists a cost log to disk.
    Every production AI system needs this — you cannot manage
    what you cannot measure.
    """

    def __init__(self, log_dir: Path = Path("traces")):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.session = SessionCosts()
        self.session_start = datetime.utcnow().isoformat()

    def record(self, result: RouteResult):
        self.session.total_cost_usd += result.estimated_cost_usd
        self.session.total_tokens_in += result.tokens_in
        self.session.total_tokens_out += result.tokens_out
        self.session.calls += 1

        # By model
        m = self.session.by_model.setdefault(
            result.model_used,
            {"calls": 0, "cost_usd": 0.0, "tokens_in": 0, "tokens_out": 0},
        )
        m["calls"] += 1
        m["cost_usd"] += result.estimated_cost_usd
        m["tokens_in"] += result.tokens_in
        m["tokens_out"] += result.tokens_out

        # By task type
        t = self.session.by_task_type.setdefault(
            result.task_type, {"calls": 0, "cost_usd": 0.0}
        )
        t["calls"] += 1
        t["cost_usd"] += result.estimated_cost_usd

    def summary(self) -> dict:
        return {
            "session_start": self.session_start,
            "total_calls": self.session.calls,
            "total_cost_usd": round(self.session.total_cost_usd, 6),
            "total_tokens_in": self.session.total_tokens_in,
            "total_tokens_out": self.session.total_tokens_out,
            "by_model": self.session.by_model,
            "by_task_type": self.session.by_task_type,
        }

    def flush(self, filename: str = None):
        if filename is None:
            filename = f"cost_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        path = self.log_dir / filename
        with open(path, "w") as f:
            json.dump(self.summary(), f, indent=2)

        logger.info(f"Cost log written: {path}")
        return path
