from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    port: int = 3000
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    postgres_host: str = "localhost"
    postgres_port: int = 5431
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = "postgres"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
