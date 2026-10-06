from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DOCUMENTS_DIR: Path = DATA_DIR / "documents"
    CHROMA_PATH: str = str(DATA_DIR / "chroma")
    SQLITE_PATH: str = str(DATA_DIR / "university.db")
    SOURCE_REGISTER_PATH: str = str(DATA_DIR / "source_register.csv")

    # LLM & Embedding Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:270m"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # API Settings
    API_PORT: int = 8000
    FRONTEND_PORT: int = 8501
    LOG_LEVEL: str = "INFO"

    # Security
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".txt", ".docx", ".md"]


settings = Settings()

# Ensure required directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_PATH).mkdir(parents=True, exist_ok=True)
