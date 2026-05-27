import litellm
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

from src.orchestration.state import AgentState
from src.router.classifier import classify_task
from src.router.policy import PolicyEngine
from src.agent.tools import TOOLS, TOOL_SCHEMAS
from src.router.router import estimate_cost
import json

policy_engine = PolicyEngine()


def _to_dict(msg) -> dict:
    """Convert any message type to a plain dict LiteLLM can send."""
    if isinstance(msg, dict):
        return msg
    # LangChain message objects
    if hasattr(msg, "type") and hasattr(msg, "content"):
        role_map = {
            "human": "user",
            "ai": "assistant",
            "system": "system",
            "tool": "tool",
        }
        return {"role": role_map.get(msg.type, msg.type), "content": msg.content}
    # Fallback
    return {"role": "user", "content": str(msg)}


def router_node(state: AgentState) -> AgentState:
    task_type = classify_task(state.query)
    policy = policy_engine.resolve(task_type)

    logger.info(f"[router_node] task={task_type} model={policy.primary}")

    return AgentState(
        **{
            **state.__dict__,
            "task_type": task_type,
            "model_selected": policy.primary,
            "messages": [{"role": "user", "content": state.query}],
        }  # plain dict
    )


def research_node(state: AgentState) -> AgentState:
    """
    Runs one iteration of the agent loop — calls the LLM,
    dispatches any tool calls, appends results to state.
    Writes: messages, tool_results, iteration_count, total_cost_usd
    """
    logger.info(f"[research_node] iteration={state.iteration_count + 1}")

    AGENT_SYSTEM = """You are a research agent. Use your tools to find accurate information.
Always use web_search to find current data before answering.
When you have enough information, stop calling tools and provide your final answer directly."""

    response = litellm.completion(
        model=state.model_selected,
        messages=[
            {"role": "system", "content": AGENT_SYSTEM},
            *[_to_dict(m) for m in state.messages],
        ],
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        temperature=0.2,
    )

    message = response.choices[0].message
    usage = response.usage
    cost = estimate_cost(
        state.model_selected, usage.prompt_tokens, usage.completion_tokens
    )

    # Convert to plain dict immediately — LangGraph can't handle LiteLLM types
    assistant_message = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        assistant_message["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]

    new_messages = list(state.messages) + [assistant_message]
    new_tool_results = []

    if message.tool_calls:
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_input = json.loads(tool_call.function.arguments)

            logger.info(f"[research_node] tool={tool_name} input={tool_input}")

            tool_output = (
                TOOLS[tool_name](**tool_input)
                if tool_name in TOOLS
                else f"Unknown tool: {tool_name}"
            )

            new_tool_results.append(
                {"tool": tool_name, "input": tool_input, "output": tool_output[:500]}
            )

            new_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                }
            )

    return AgentState(
        **{
            **state.__dict__,
            "messages": new_messages,
            "tool_results": state.tool_results + new_tool_results,
            "iteration_count": state.iteration_count + 1,
            "total_cost_usd": state.total_cost_usd + cost,
        }
    )


def synthesis_node(state: AgentState) -> AgentState:
    """
    Takes all research results and produces a final answer.
    Builds a clean message history — no tool call/result pairs —
    so Gemini's message converter doesn't choke.
    """
    logger.info(
        f"[synthesis_node] synthesizing from {len(state.tool_results)} tool results"
    )

    policy = policy_engine.resolve(state.task_type)

    # Build a clean summary of what the tools found
    tool_summary = "\n\n".join(
        [
            f"Tool: {r['tool']}\nInput: {r['input']}\nResult: {r['output']}"
            for r in state.tool_results
        ]
    )

    synthesis_messages = [
        {
            "role": "system",
            "content": f"""You are a research synthesizer. 
Based on the following research results, answer the user's question clearly and accurately.
Cite sources where relevant.

Research gathered:
{tool_summary}""",
        },
        {"role": "user", "content": state.query},
    ]

    response = litellm.completion(
        model=state.model_selected,
        messages=synthesis_messages,
        temperature=0.1,
        max_tokens=policy.max_tokens,
    )

    answer = response.choices[0].message.content
    usage = response.usage
    cost = estimate_cost(
        state.model_selected, usage.prompt_tokens, usage.completion_tokens
    )

    logger.info(f"[synthesis_node] complete cost=${state.total_cost_usd + cost:.5f}")

    return AgentState(
        **{
            **state.__dict__,
            "final_answer": answer,
            "is_complete": True,
            "total_cost_usd": state.total_cost_usd + cost,
        }
    )


def extraction_node(state: AgentState) -> AgentState:
    """
    Runs the extraction pipeline directly for extraction tasks.
    Bypasses the agent loop entirely.
    Writes: extracted_data, final_answer, is_complete
    """
    logger.info(f"[extraction_node] running extraction pipeline")

    from src.extraction.extractor import extract_job_posting

    try:
        result = extract_job_posting(state.query)
        extracted = result.model_dump()
        answer = f"Extracted successfully. Confidence: {result.confidence}"
    except Exception as e:
        extracted = {}
        answer = f"Extraction failed: {e}"

    return AgentState(
        **{
            **state.__dict__,
            "extracted_data": extracted,
            "final_answer": answer,
            "is_complete": True,
        }
    )
