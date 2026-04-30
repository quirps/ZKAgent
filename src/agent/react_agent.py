import json
import time
import litellm
from loguru import logger
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

load_dotenv()

from config.settings import settings
from src.agent.tools import TOOLS, TOOL_SCHEMAS

console = Console()

SYSTEM_PROMPT = """You are a research agent with access to tools.
Your job is to answer questions thoroughly and accurately by using your tools.

Rules:
- Always use web_search before claiming you don't know something
- Use calculator for any numerical computation, never mental math
- Use fetch_url when you need the full content of a specific page
- Think step by step before deciding which tool to use
- When you have enough information, provide a clear final answer
- Cite your sources in the final answer"""


class AgentTrace:
    """Captures the full execution trace of an agent run."""
    
    def __init__(self, query: str):
        self.query = query
        self.iterations: list[dict] = []
        self.start_time = time.perf_counter()
        self.total_tokens_in = 0
        self.total_tokens_out = 0
    
    def log_iteration(self, iteration: int, decision: str, 
                      tool_name: str | None, tool_input: dict | None,
                      tool_output: str | None, tokens_in: int, tokens_out: int):
        self.iterations.append({
            "iteration": iteration,
            "decision": decision,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output[:500] if tool_output else None,  # truncate for trace
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        })
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
    
    def summary(self) -> dict:
        elapsed = time.perf_counter() - self.start_time
        return {
            "query": self.query,
            "total_iterations": len(self.iterations),
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "elapsed_seconds": round(elapsed, 2),
            "iterations": self.iterations,
        }


def run_agent(query: str, max_iterations: int = 8) -> tuple[str, AgentTrace]:
    """
    Run the ReAct agent loop on a query.
    Returns the final answer and the full execution trace.
    """
    trace = AgentTrace(query)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]
    
    console.print(Panel(f"[bold cyan]Query:[/bold cyan] {query}", 
                        title="Agent Starting"))
    
    for iteration in range(1, max_iterations + 1):
        console.print(f"\n[dim]── Iteration {iteration} ──[/dim]")
        
        # ── LLM CALL ──────────────────────────────────────────────
        start = time.perf_counter()
        response = litellm.completion(
    model=settings.primary_model,
    messages=messages,
    temperature=0.1,
    response_format={"type": "json_object"},
    fallbacks=[{"model": settings.fast_model}],  # dict format, not string
    num_retries=2,
)
        latency_ms = (time.perf_counter() - start) * 1000
        
        message = response.choices[0].message
        usage = response.usage
        finish_reason = response.choices[0].finish_reason
        
        logger.info(
            f"Iteration={iteration} finish_reason={finish_reason} "
            f"latency={latency_ms:.0f}ms "
            f"tokens_in={usage.prompt_tokens} tokens_out={usage.completion_tokens}"
        )
        
        # Append assistant message to history
        messages.append(message.model_dump(exclude_none=True))
        
        # ── DONE — no tool calls ───────────────────────────────────
        if finish_reason == "stop" or not message.tool_calls:
            final_answer = message.content or "No answer generated."
            console.print(Panel(
                final_answer,
                title=f"[bold green]Final Answer[/bold green] "
                      f"(after {iteration} iterations)",
                border_style="green"
            ))
            trace.log_iteration(
                iteration, "final_answer", None, None, None,
                usage.prompt_tokens, usage.completion_tokens
            )
            return final_answer, trace
        
        # ── TOOL CALLS ────────────────────────────────────────────
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_input = json.loads(tool_call.function.arguments)
            
            console.print(
                f"  [yellow]→ Tool:[/yellow] [bold]{tool_name}[/bold] "
                f"[dim]{tool_input}[/dim]"
            )
            
            # Dispatch
            if tool_name in TOOLS:
                tool_output = TOOLS[tool_name](**tool_input)
            else:
                tool_output = f"Error: unknown tool '{tool_name}'"
                logger.error(f"Unknown tool called: {tool_name}")
            
            console.print(f"  [green]← Result:[/green] [dim]{tool_output[:200]}...[/dim]")
            
            # Append tool result to history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output,
            })
            
            trace.log_iteration(
                iteration, "tool_call", tool_name, tool_input, tool_output,
                usage.prompt_tokens, usage.completion_tokens
            )
    
    # ── MAX ITERATIONS HIT ────────────────────────────────────────
    logger.warning(f"Agent hit max_iterations={max_iterations} without finishing")
    fallback = "Agent reached maximum iterations without producing a final answer."
    return fallback, trace