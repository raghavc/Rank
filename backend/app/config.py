from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(alias="DATABASE_URL")
    alembic_database_url: str = Field(alias="ALEMBIC_DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    jwt_iss: str = Field(default="rank-api", alias="JWT_ISS")
    jwt_aud: str = Field(default="rank-ios", alias="JWT_AUD")
    jwt_access_ttl_minutes: int = Field(default=15, alias="JWT_ACCESS_TTL_MINUTES")
    jwt_refresh_ttl_days: int = Field(default=30, alias="JWT_REFRESH_TTL_DAYS")

    teller_token_enc_key: str = Field(alias="TELLER_TOKEN_ENC_KEY")
    teller_app_id: str = Field(default="", alias="TELLER_APP_ID")
    teller_environment: str = Field(default="development", alias="TELLER_ENVIRONMENT")
    teller_cert_path: str = Field(default="/certs/certificate.pem", alias="TELLER_CERT_PATH")
    teller_key_path: str = Field(default="/certs/private_key.pem", alias="TELLER_KEY_PATH")

    teller_connect_signing_public_key_pem: str = Field(
        default="",
        alias="TELLER_CONNECT_SIGNING_PUBLIC_KEY",
        description="PEM Ed25519 public key from Teller dashboard (Token Signing Key).",
    )

    cors_origins: str = Field(
        default="",
        alias="CORS_ORIGINS",
        description="Comma-separated list; empty disables CORS middleware (typical for iOS-only).",
    )
    trusted_hosts: str = Field(
        default="",
        alias="TRUSTED_HOSTS",
        description="Comma-separated hostnames for TrustedHostMiddleware; empty disables.",
    )
    rate_limit_storage_uri: str = Field(
        default="",
        alias="RATE_LIMIT_STORAGE_URI",
        description="Redis URL for SlowAPI (e.g. redis://redis:6379/1); empty uses in-memory store.",
    )

    use_memory_nonce_store: bool = Field(
        default=False,
        alias="RANK_MEMORY_NONCE_STORE",
        description="Use in-process nonce store (tests only).",
    )

    @field_validator("teller_connect_signing_public_key_pem", mode="before")
    @classmethod
    def _normalize_pem(cls, v: object) -> object:
        if isinstance(v, str) and "\\n" in v:
            return v.replace("\\n", "\n")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
            return []
        return [p.strip() for p in raw.split(",") if p.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        raw = (self.trusted_hosts or "").strip()
        if not raw:
            return []
        return [p.strip() for p in raw.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
