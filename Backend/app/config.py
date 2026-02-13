# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    data_dir: str = "app/data"
    pdf_dir: str = "app/data/pdfs"
    artifacts_dir: str = "app/data/artifacts"
    backend_origin: str = "http://localhost:8000"

    class Config:
        env_file = ".env"

settings = Settings()
