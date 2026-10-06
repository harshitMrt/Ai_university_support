"""
Configuration management using Pydantic Settings.
Loads environment variables from .env with fallback defaults and directory auto-creation.
"""

from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DOCUMENTS_DIR: Path = DATA_DIR / "documents"
    CHROMA_PATH: str = str(DATA_DIR / "chroma")
    SQLITE_PATH: str = str(DATA_DIR / "university.db")
    SOURCE_REGISTER_PATH: str = str(DATA_DIR / "source_register.csv")
    AUDIT_DB_PATH: str = str(DATA_DIR / "university.db")

    # LLM & Embedding Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:270m"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    LLM_CONNECT_TIMEOUT_SEC: float = 1.0
    LLM_READ_TIMEOUT_SEC: float = 12.0

    # API Settings
    API_PORT: int = 8000
    FRONTEND_PORT: int = 8501
    LOG_LEVEL: str = "INFO"

    # Security
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".docx", ".md"]

    def ensure_directories(self) -> None:
        """Ensures all necessary data directories exist on startup."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_PATH).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    s.ensure_directories()
    return s


settings = get_settings()
