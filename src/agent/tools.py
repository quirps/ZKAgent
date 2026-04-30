import httpx
from tavily import TavilyClient
from loguru import logger
from dotenv import load_dotenv
from config.settings import settings

load_dotenv()

tavily = TavilyClient(api_key=settings.tavily_api_key)

def web_search(query: str) -> str:
    """
    Search the web for current information on a topic.
    Returns a summary of the top results with sources.
    Use this when you need facts, recent events, or information
    you don't already know.
    
    Args:
        query: The search query string
    
    Returns:
        Search results as formatted text with sources
    """
    logger.info(f"Tool: web_search | query='{query}'")
    
    try:
        response = tavily.search(
            query=query,
            max_results=5,
            search_depth="basic"
        )
        
        results = []
        for r in response.get("results", []):
            results.append(f"Source: {r['url']}\n{r['content']}\n")
        
        output = "\n---\n".join(results)
        logger.debug(f"web_search returned {len(results)} results")
        return output
    
    except Exception as e:
        logger.error(f"web_search failed: {e}")
        return f"Search failed: {str(e)}"


def fetch_url(url: str) -> str:
    """
    Fetch and read the content of a specific URL.
    Use this when you have a specific page you need to read in full,
    such as an article, documentation page, or search result.
    
    Args:
        url: The full URL to fetch
    
    Returns:
        The text content of the page (truncated to 8000 chars)
    """
    logger.info(f"Tool: fetch_url | url='{url}'")
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (research-agent/1.0)"}
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
        
        # Truncate — you don't want to blow your context window on one page
        content = response.text[:8000]
        logger.debug(f"fetch_url returned {len(content)} chars")
        return content
    
    except Exception as e:
        logger.error(f"fetch_url failed: {e}")
        return f"Failed to fetch URL: {str(e)}"


def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.
    Use this for any arithmetic, percentages, or numerical calculations.
    Do not attempt mental math — always use this tool for calculations.
    
    Args:
        expression: A valid Python mathematical expression, e.g. '(180000 + 240000) / 2'
    
    Returns:
        The result as a string
    """
    logger.info(f"Tool: calculator | expression='{expression}'")
    
    try:
        # Safe eval — only allow math operations
        allowed = {
            "__builtins__": {},
            "abs": abs, "round": round, "min": min, "max": max,
            "pow": pow, "sum": sum,
        }
        result = eval(expression, allowed)  # noqa: S307
        logger.debug(f"calculator result: {result}")
        return str(result)
    
    except Exception as e:
        logger.error(f"calculator failed: {e}")
        return f"Calculation failed: {str(e)}"


# Registry — the agent uses this to look up and dispatch tools
TOOLS = {
    "web_search": web_search,
    "fetch_url": fetch_url,
    "calculator": calculator,
}

# Schema for the LLM — tells it what tools exist and how to call them
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": web_search.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": fetch_url.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": calculator.__doc__,
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression to evaluate"}
                },
                "required": ["expression"]
            }
        }
    }
]