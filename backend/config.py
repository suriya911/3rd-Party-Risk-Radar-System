from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    brightdata_api_token: str = Field("", env="BRIGHTDATA_API_TOKEN")
    brightdata_serp_zone: str = Field("serp", env="BRIGHTDATA_SERP_ZONE")
    brightdata_unlocker_zone: str = Field("web_unlocker1", env="BRIGHTDATA_UNLOCKER_ZONE")
    brightdata_username: str = Field("", env="BRIGHTDATA_USERNAME")
    brightdata_password: str = Field("", env="BRIGHTDATA_PASSWORD")
    brightdata_proxy_host: str = Field("brd.superproxy.io", env="BRIGHTDATA_PROXY_HOST")
    brightdata_proxy_port: int = Field(22225, env="BRIGHTDATA_PROXY_PORT")

    anthropic_api_key: str = Field("", env="ANTHROPIC_API_KEY")
    claude_model: str = Field("claude-sonnet-4-6", env="CLAUDE_MODEL")

    # LLM provider for signal extraction — OpenAI-compatible endpoint.
    # Default targets AI/ML API (aimlapi.com), which serves Claude + GPT models.
    # LLM_API_KEY falls back to ANTHROPIC_API_KEY if unset.
    llm_api_key: str = Field("", env="LLM_API_KEY")
    llm_base_url: str = Field("https://api.aimlapi.com/v1", env="LLM_BASE_URL")
    llm_model: str = Field("claude-sonnet-4-5", env="LLM_MODEL")

    database_url: str = Field("./risk_radar.db", env="DATABASE_URL")
    vendors_csv: str = Field("./vendors.csv", env="VENDORS_CSV")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    cors_origins: str = Field("http://localhost:5173,http://localhost:3000", env="CORS_ORIGINS")

    mcp_server_host: str = Field("127.0.0.1", env="MCP_SERVER_HOST")
    mcp_server_port: int = Field(8001, env="MCP_SERVER_PORT")

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def effective_llm_key(self) -> str:
        """LLM_API_KEY if provided, else fall back to ANTHROPIC_API_KEY."""
        return self.llm_api_key or self.anthropic_api_key

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def brightdata_proxy_url(self) -> str:
        return (
            f"http://{self.brightdata_username}:{self.brightdata_password}"
            f"@{self.brightdata_proxy_host}:{self.brightdata_proxy_port}"
        )


settings = Settings()
