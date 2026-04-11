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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
