from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(alias="DATABASE_URL")
    alembic_database_url: str = Field(alias="ALEMBIC_DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    jwt_ttl_hours: int = Field(default=24, alias="JWT_TTL_HOURS")

    teller_token_enc_key: str = Field(alias="TELLER_TOKEN_ENC_KEY")
    teller_app_id: str = Field(default="", alias="TELLER_APP_ID")
    teller_environment: str = Field(default="development", alias="TELLER_ENVIRONMENT")
    teller_cert_path: str = Field(default="/certs/certificate.pem", alias="TELLER_CERT_PATH")
    teller_key_path: str = Field(default="/certs/private_key.pem", alias="TELLER_KEY_PATH")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
