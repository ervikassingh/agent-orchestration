"""Environment configuration via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", PACKAGE_ENV_FILE),
        extra="ignore",
    )

    # OpenRouter / LLM
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    MODEL: str = "openai/gpt-4o-mini"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4096

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    # Agent loop
    MAX_TOOL_ITERATIONS: int = 10


settings = Settings()
