from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="sg_ai_", env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database connections ───────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://sgc:sgc@localhost:5432/prod_pikpart"
    database_url_sync: str = "postgresql://sgc:sgc@localhost:5432/prod_pikpart"
    agent_database_url: str = "postgresql+asyncpg://sgc:sgc@localhost:5432/sgc_agent"
    agent_database_url_sync: str = "postgresql://sgc:sgc@localhost:5432/sgc_agent"

    # ── Redis ──────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── LLM providers ─────────────────────────────────────────────────
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    default_llm_model: str = "gpt-4o-mini"
    fallback_llm_model: str = "gpt-4o-mini"

    # ── MCP Server ─────────────────────────────────────────────────────
    mcp_transport: str = "sse"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001

    # ── Logging ────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "text"  # "json" for production, "text" for development

    # ── Environment ────────────────────────────────────────────────────
    environment: str = "development"


def get_settings() -> Settings:
    return Settings()
