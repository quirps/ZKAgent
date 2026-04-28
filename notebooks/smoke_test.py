from config.settings import settings
import litellm
from dotenv import load_dotenv

load_dotenv()

response = litellm.completion(
    model=settings.primary_model,
    messages=[{"role": "user", "content": "Respond with exactly: ENV OK"}]
)

print(f"Model: {settings.primary_model}")
print(f"Response: {response.choices[0].message.content}")