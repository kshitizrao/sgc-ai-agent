from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


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
    mcp_server_url: str = "http://localhost:8001/sse/"
    start_local_mcp_server: bool = True

    # ── Logging ────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "text"  # "json" for production, "text" for development

    # ── Environment ────────────────────────────────────────────────────
    environment: str = "development"

    @model_validator(mode="after")
    def default_sync_urls(self) -> "Settings":
        if self.database_url and "localhost" in self.database_url_sync and "localhost" not in self.database_url:
            self.database_url_sync = self.database_url.replace("+asyncpg", "")
        if self.agent_database_url and "localhost" in self.agent_database_url_sync and "localhost" not in self.agent_database_url:
            self.agent_database_url_sync = self.agent_database_url.replace("+asyncpg", "")
        return self


def get_settings() -> Settings:
    return Settings()
