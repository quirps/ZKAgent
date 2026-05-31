from typing import Annotated, Any
from dataclasses import dataclass, field
from langgraph.graph.message import add_messages
import uuid


@dataclass
class AgentState:
    """
    The shared state that flows through every node in the graph. Every field is explicitly typed
     nodes declare what they read and write.
    """

    # The original user query
    query: str = ""

    # Classified task type rfom the router
    task_type: str = ""

    # which model was selected for this run
    model_selected: str = ""

    # tool calls made during research (list of dicts)
    tool_results: list[dict] = field(default_factory=list)

    # final synthesized answer
    final_answer: str = " "

    # extracted structured data if task was extraction
    extracted_data: dict = field(default_factory=dict)

    # how many iterations the agent has taken
    iteration_count: int = 0

    # whether the agent has finished
    is_complete: bool = False

    # running cost for this graph execution
    total_cost_usd: float = 0.0

    # full message history for llm calls
    messages: Annotated[list, add_messages] = field(default_factory=list)

    # Observability — generated once per graph run, shared across all nodes
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
