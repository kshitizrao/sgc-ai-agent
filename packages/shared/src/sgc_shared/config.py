from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="sg_ai_", env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://sgc:sgc@localhost:5432/sgc_agent"
    database_url_sync: str = "postgresql://sgc:sgc@localhost:5432/sgc_agent"
    redis_url: str = "redis://localhost:6379/0"
    agent_api_key: str = "dev-api-key-change-in-production"
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    default_llm_model: str = "ollama/llama3.1:8b"
    fallback_llm_model: str = "gpt-4o-mini"
    environment: str = "development"


def get_settings() -> Settings:
    return Settings()
