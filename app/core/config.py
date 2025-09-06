from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseSettings):
    postgres_user: str = os.environ.get("POSTGRES_USER", "testuser")
    postgres_password: str = os.environ.get("POSTGRES_PASSWORD", "testpass")
    postgres_db: str = os.environ.get("POSTGRES_DB", "testdb")
    postgres_host: str = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.environ.get("POSTGRES_PORT", 5432))

    api_v1_prefix: str = "/api/v1"

    database_url: str = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
