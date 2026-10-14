import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """
    Centralized application configuration loaded from environment variables and .env file.
    """
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Personalized Medical Recommendation System"
    APP_ENV: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = Field(
        default="change-this-insecure-key-to-a-secure-random-token",
        description="Application secret key used for session/cookie signing"
    )

    # External AI Provider (Google Gemini)
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key for intelligent symptom fallback"
    )

    # Optional healthcare API credentials
    RAPIDAPI_KEY: str = ""
    OPENFDA_KEY: str = ""

    # Paths
    BASE_DIR: Path = BASE_DIR
    MODEL_PATH: Path = BASE_DIR / "models" / "svc.pkl"
    CHECKPOINT_MODEL_PATH: Path = BASE_DIR / "models" / ".ipynb_checkpoints" / "svc.pkl"
    DATASETS_DIR: Path = BASE_DIR / "datasets"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def has_gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip() and not self.GEMINI_API_KEY.startswith("replace_"))

settings = Settings()
