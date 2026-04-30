from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_api_key: str
    groq_api_key: str = ""  # optional for now
    tavily_api_key: str = ""
    # Default models
    primary_model: str = "groq/llama-3.3-70b-versatile"
    fast_model : str = "gemini/gemini-2.5-flash"

    class Config:
        env_file = ".env"

settings = Settings()