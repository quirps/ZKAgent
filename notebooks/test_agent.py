import json
from src.agent.react_agent import run_agent
from rich import print as rprint

queries = [
    "What is the current price of Bitcoin and how does it compare to its all time high?",
    "If I invest $5000 at 7% annual return compounded monthly for 10 years, what do I end up with?",
]

for query in queries:
    answer, trace = run_agent(query)
    summary = trace.summary()
    
    print(f"\n{'='*50}")
    print(f"Iterations: {summary['total_iterations']}")
    print(f"Total tokens: {summary['total_tokens_in']} in / {summary['total_tokens_out']} out")
    print(f"Elapsed: {summary['elapsed_seconds']}s")
    
    # Save trace to disk
    with open(f"traces/trace_{summary['query'][:30].replace(' ', '_')}.json", "w") as f:
        json.dump(summary, f, indent=2)