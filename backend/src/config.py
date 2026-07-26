from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    port: int = 3000
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333


settings = Settings()
