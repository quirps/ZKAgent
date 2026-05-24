from pathlib import Path
from dataclasses import dataclass
import yaml
from loguru import logger


@dataclass
class TaskPolicy:
    task_type: str
    description: str
    primary: str
    fallback: str
    max_tokens: int
    temperature: float


class PolicyEngine:
    """
    Loads routing policy from config and resolves the correct
    model and parameters for a given task type
    """

    def __init__(self, policy_path: Path = None):
        if policy_path is None:
            policy_path = (
                Path(__file__).parent.parent.parent / "config" / "routing_policy.yml"
            )
        logger.debug(f"Policy Path - {policy_path}")
        with open(policy_path) as f:
            raw = yaml.safe_load(f)

        self.policies: dict[str, TaskPolicy] = {}
        for task_type, config in raw["task_types"].items():
            self.policies[task_type] = TaskPolicy(task_type=task_type, **config)
        logger.info(f"PolicyEngine loaded {len(self.policies)} task policies")

    def resolve(self, task_type: str) -> TaskPolicy:
        if task_type not in self.policies:
            logger.warning(
                f"Unknown task type '{task_type}', falling back to simple_qa"
            )
            return self.policies["simple_qa"]
        return self.policies[task_type]

    def all_task_types(self) -> list[str]:
        return list(self.policies.keys())
