import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Ghost-Typer Auto-Documenter"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LLM_PROVIDER: str = "ollama"  # Options 'ollama' or 'dummy'
    OLLAMA_MODEL: str = "llama3.2" # Adjust according to the local model you have

    class Config:
        env_file = ".env"

settings = Settings()
