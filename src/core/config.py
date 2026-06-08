import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AI keys - system uses Groq API
    OPENAI_API_KEY: str = "hf_placeholder"
    GROQ_API_KEY: str = "your_groq_api_key"
    APP_ENV: str = "development"

    GCP_CREDENTIALS_PATH: str = "src/core/credentials.json"
    GMAIL_TOKEN_PATH: str = "src/core/token.json"
    # Optional: JSON payloads for headless deployments (Render, etc.)
    GMAIL_CREDENTIALS_JSON: str = ""
    GMAIL_TOKEN_JSON: str = ""

    NOTIFICATION_EMAIL: str = "your_email@domain.com"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your_email@domain.com"
    SMTP_PASSWORD: str = "your_app_password_here"

    MIN_DELAY_SECONDS: int = 30
    MAX_DELAY_SECONDS: int = 90
    MAX_EMAILS_PER_DAY: int = 100
    
    # Rate limiting (Gmail API safeguards)
    RATE_LIMIT_PER_SECOND: float = 0.5  # 1 email per 2 seconds
    RATE_LIMIT_PER_MINUTE: int = 15     # 15 emails per minute
    RATE_LIMIT_PER_HOUR: int = 100      # 100 emails per hour

    def is_headless(self) -> bool:
        return self.APP_ENV.lower() in {"production", "prod", "staging"} or os.getenv("RENDER") == "true"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
