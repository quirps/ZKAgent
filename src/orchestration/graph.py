from langgraph.graph import StateGraph, END
from loguru import logger

from src.orchestration.state import AgentState
from src.orchestration.nodes import (
    router_node,
    research_node,
    synthesis_node,
    extraction_node,
)

MAX_ITERATIONS = 5


def should_continue_research(state: AgentState) -> str:
    last_message = state.messages[-1] if state.messages else None

    if not last_message:
        return "synthesize"

    # Plain dict check
    has_tool_calls = (
        isinstance(last_message, dict)
        and last_message.get("tool_calls")
        and len(last_message["tool_calls"]) > 0
    )

    if not has_tool_calls:
        logger.info("[edge] no tool calls → synthesis")
        return "synthesize"

    if state.iteration_count >= MAX_ITERATIONS:
        logger.warning("[edge] max iterations hit → synthesis")
        return "synthesize"

    logger.info("[edge] tool calls present → continue research")
    return "research"


def route_by_task(state: AgentState) -> str:
    """
    Conditional edge after router — decides which subgraph to enter.
    """
    if state.task_type == "extraction":
        logger.info("[edge] extraction task → extraction_node")
        return "extraction"

    logger.info(f"[edge] {state.task_type} → research")
    return "research"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("research", research_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("extraction", extraction_node)

    # Entry point
    graph.set_entry_point("router")

    # Router → branch on task type
    graph.add_conditional_edges(
        "router",
        route_by_task,
        {
            "research": "research",
            "extraction": "extraction",
        },
    )

    # Research loop — conditional back to self or forward to synthesis
    graph.add_conditional_edges(
        "research",
        should_continue_research,
        {
            "research": "research",
            "synthesize": "synthesis",
        },
    )

    # Terminal nodes
    graph.add_edge("synthesis", END)
    graph.add_edge("extraction", END)

    return graph.compile()


# Singleton — compile once, reuse
orchestration_graph = build_graph()
