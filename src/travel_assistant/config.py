from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    azure_openai_endpoint: str = Field(default="", validation_alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(default="", validation_alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(
        default="2024-10-21", validation_alias="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_chat_deployment: str = Field(
        default="", validation_alias="AZURE_OPENAI_CHAT_DEPLOYMENT"
    )
    azure_openai_embedding_deployment: str = Field(
        default="", validation_alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )

    weather_mcp_command: str = Field(default="python", validation_alias="WEATHER_MCP_COMMAND")
    weather_mcp_args: str = Field(default="", validation_alias="WEATHER_MCP_ARGS")
    currency_mcp_command: str = Field(default="python", validation_alias="CURRENCY_MCP_COMMAND")
    currency_mcp_args: str = Field(default="", validation_alias="CURRENCY_MCP_ARGS")
    currency_api_url: str = Field(
        default="https://api.frankfurter.app", validation_alias="CURRENCY_API_URL"
    )
    currency_api_key: str = Field(default="", validation_alias="CURRENCY_API_KEY")

    singapore_latitude: float = Field(default=1.3521, validation_alias="SINGAPORE_LATITUDE")
    singapore_longitude: float = Field(default=103.8198, validation_alias="SINGAPORE_LONGITUDE")
    singapore_timezone: str = Field(
        default="Asia/Singapore", validation_alias="SINGAPORE_TIMEZONE"
    )
    retrieval_top_k: int = Field(default=5, validation_alias="RETRIEVAL_TOP_K", ge=1, le=20)


@lru_cache
def get_settings() -> Settings:
    return Settings()