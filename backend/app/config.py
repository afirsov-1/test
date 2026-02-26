from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/csv_to_db"
    SECRET_KEY: str = "your-super-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
