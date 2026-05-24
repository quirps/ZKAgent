import litellm
from loguru import logger
from dotenv import load_dotenv
from config.settings import settings

load_dotenv()

# use the cheapest/fastest model for classification
CLASSIFIER_MODEL = "groq/llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a task classifier. Given a user request,
classify it into exactly one of these categories:

simple_qa
complex_reasoning
code_generation
extraction
summarization

Rules:
- Respond with ONLY the category name
- Use underscores exactly as shown above
- No punctuation, no explanation, no extra words"""


def classify_task(request: str) -> str:
    """
    Classify a request into a task type.
    Returns one of the known task type strings.
    Fast, cheap call - always uses the smallest model
    """
    logger.info(f"Classifying : '{request[:80]}...")

    response = litellm.completion(
        model=CLASSIFIER_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request},
        ],
        temperature=0,
        max_tokens=20,
    )

    # Normalize separators before matching
    raw = response.choices[0].message.content.strip().lower()
    raw = raw.replace("-", "_").replace(" ", "_")  # add this line
    # sanitzie output as model may add superflous characters
    known_types = {
        "simple_qa",
        "complex_reasoning",
        "code_generation",
        "extraction",
        "summarization",
    }
    if raw in known_types:
        logger.info(f"Classified as: {raw}")
        return raw

    # fuzzy fallback - check if any known type appears in teh respone
    for known in known_types:
        if known in raw:
            logger.warning(f"Fuzzy match '{raw}' > '{known}'")
            return known
    logger.warning(f"Could not classify '{raw}' defaulting to simple_qa")
    return "simple_qa"
