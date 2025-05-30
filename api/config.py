import os

class Settings:
    PROJECT_NAME: str = "Smart Agence API"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smart_agence.db")

settings = Settings()