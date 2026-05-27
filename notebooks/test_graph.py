from src.orchestration.graph import orchestration_graph
from src.orchestration.state import AgentState
from rich.console import Console
from rich import print as rprint

console = Console()

queries = [
    "What is the current price of Ethereum?",
    "Senior Python Engineer at Stripe. Remote. $200k. Python, Go required.",
]

for query in queries:
    console.rule(f"[bold cyan]{query[:60]}")

    initial_state = AgentState(query=query)
    final_state = orchestration_graph.invoke(initial_state)

    console.print(f"\n[bold]Task type:[/bold] {final_state['task_type']}")
    console.print(f"[bold]Model:[/bold]     {final_state['model_selected']}")
    console.print(f"[bold]Iterations:[/bold] {final_state['iteration_count']}")
    console.print(f"[bold]Cost:[/bold]      ${final_state['total_cost_usd']:.5f}")
    console.print(f"\n[bold green]Answer:[/bold green]")
    console.print(final_state["final_answer"])
