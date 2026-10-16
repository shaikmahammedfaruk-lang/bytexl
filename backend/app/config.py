# import os
# import secrets
# from urllib.parse import urlsplit
# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     PROJECT_NAME: str = "BrandShield AI"
#     VERSION: str = "1.0.0"
#     API_V1_STR: str = "/api"
#     MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
#     DB_NAME: str = os.getenv("DB_NAME", "brandshield_ai")
#     ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
#     CORS_ORIGINS: list[str] = ["*"]

#     # Meta Graph & Instagram API Configuration
#     INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
#     META_GRAPH_API_VERSION: str = os.getenv("META_GRAPH_API_VERSION", "v21.0")
#     INSTAGRAM_BUSINESS_ACCOUNT_ID: str = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
#     INSTAGRAM_DEMO_MODE: bool = os.getenv("INSTAGRAM_DEMO_MODE", "true").lower() in ("true", "1", "yes")

#     # Facebook Meta Graph API Configuration
#     FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
#     FACEBOOK_APP_ID: str = os.getenv("FACEBOOK_APP_ID", "")
#     FACEBOOK_APP_SECRET: str = os.getenv("FACEBOOK_APP_SECRET", "")

#     # X (Twitter) API v2 Configuration
#     X_BEARER_TOKEN: str = os.getenv("X_BEARER_TOKEN", "")
#     X_API_KEY: str = os.getenv("X_API_KEY", "")
#     X_API_SECRET: str = os.getenv("X_API_SECRET", "")
#     X_API_TIER: str = os.getenv("X_API_TIER", "v2_free_basic")

#     # LinkedIn Community & Organizational API Configuration
#     LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
#     LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
#     LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")

#     # Multi-Platform Sandbox & Graceful Fallback Mode
#     PLATFORM_SANDBOX_MODE: bool = os.getenv("PLATFORM_SANDBOX_MODE", "true").lower() in ("true", "1", "yes")

#     # Authentication & JWT Configuration
#     JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
#     JWT_ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

#     # Google OAuth 2.0 Credentials
#     GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

#     # Email & SMTP Configuration for Password Reset & Verification
#     SMTP_HOST: str = os.getenv("SMTP_HOST", "")
#     SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
#     SMTP_USER: str = os.getenv("SMTP_USER", "")
#     SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
#     EMAIL_FROM: str = os.getenv("EMAIL_FROM", "security@brandshield.ai")
#     FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
#     REQUIRE_EMAIL_VERIFICATION: bool = os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").lower() in ("true", "1", "yes")

#     class Config:
#         env_file = ".env"

# settings = Settings()
# settings.FRONTEND_URL = settings.FRONTEND_URL.rstrip("/")

# if settings.ENVIRONMENT.lower() == "production":
#     if len(settings.JWT_SECRET_KEY) < 32 or "replace_" in settings.JWT_SECRET_KEY.lower():
#         raise RuntimeError("Set JWT_SECRET_KEY to a unique random value of at least 32 characters in production.")

#     mongo_host = urlsplit(settings.MONGO_URI).hostname
#     if not mongo_host or mongo_host in ("localhost", "127.0.0.1", "::1"):
#         raise RuntimeError("Set MONGO_URI to the reachable MongoDB URL for this deployment.")

#     frontend_url = urlsplit(settings.FRONTEND_URL)
#     frontend_host = frontend_url.hostname
#     if (
#         frontend_url.scheme != "https"
#         or not frontend_url.netloc
#         or not frontend_host
#         or frontend_host in ("localhost", "127.0.0.1", "::1")
#         or frontend_host.endswith(".example")
#     ):
#         raise RuntimeError("Set FRONTEND_URL to the public HTTPS URL of this deployment.")
# elif not settings.JWT_SECRET_KEY:
#     settings.JWT_SECRET_KEY = secrets.token_urlsafe(32)





import os
import secrets
from urllib.parse import urlsplit
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "BrandShield AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "brandshield_ai"
    ENVIRONMENT: str = "development"

    # Explicit origins only. Configure these for your actual frontend.
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    # Instagram / Meta
    INSTAGRAM_ACCESS_TOKEN: str = ""
    META_GRAPH_API_VERSION: str = "v21.0"
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    INSTAGRAM_DEMO_MODE: bool = True

    FACEBOOK_ACCESS_TOKEN: str = ""
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""

    # X / Twitter
    X_BEARER_TOKEN: str = ""
    X_API_KEY: str = ""
    X_API_SECRET: str = ""
    X_API_TIER: str = "v2_free_basic"

    # LinkedIn
    LINKEDIN_ACCESS_TOKEN: str = ""
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""

    # Platform sandbox
    PLATFORM_SANDBOX_MODE: bool = True

    # Authentication
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=5, le=1440)

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # Email and SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "security@brandshield.ai"
    FRONTEND_URL: str = "http://localhost:5173"
    REQUIRE_EMAIL_VERIFICATION: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        validate_assignment=True,
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            # Accept a comma-separated environment value.
            value = [part.strip() for part in value.split(",") if part.strip()]

        if not isinstance(value, (list, tuple)):
            raise ValueError("CORS_ORIGINS must be a list of origins.")

        origins = []
        for origin in value:
            if not isinstance(origin, str):
                raise ValueError("Each CORS origin must be a string.")

            origin = origin.strip().rstrip("/")
            if not origin:
                continue

            parsed = urlsplit(origin)
            if (
                parsed.scheme not in ("http", "https")
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(
                    "Each CORS origin must be a valid origin URL, "
                    "such as https://example.com."
                )

            origins.append(origin)

        if "*" in origins:
            raise ValueError(
                "Wildcard CORS origins are not allowed. "
                "List the exact frontend origins."
            )

        if not origins:
            raise ValueError("At least one CORS origin must be configured.")

        return list(dict.fromkeys(origins))

    @model_validator(mode="after")
    def validate_security_configuration(self):
        environment = self.ENVIRONMENT.strip().lower()

        if environment not in ("development", "test", "production"):
            raise ValueError(
                "ENVIRONMENT must be development, test, or production."
            )

        object.__setattr__(self, "ENVIRONMENT", environment)
        object.__setattr__(
            self,
            "FRONTEND_URL",
            self.FRONTEND_URL.strip().rstrip("/"),
        )

        frontend = urlsplit(self.FRONTEND_URL)

        if (
            frontend.scheme not in ("http", "https")
            or not frontend.hostname
            or frontend.username
            or frontend.password
            or frontend.query
            or frontend.fragment
            or frontend.path not in ("", "/")
        ):
            raise ValueError(
                "FRONTEND_URL must be a frontend origin URL, "
                "such as http://localhost:5173."
            )

        if environment == "production":
            if (
                len(self.JWT_SECRET_KEY) < 32
                or self.JWT_SECRET_KEY.lower() in ("changeme", "secret")
                or "replace_" in self.JWT_SECRET_KEY.lower()
            ):
                raise ValueError(
                    "Production requires a unique JWT_SECRET_KEY "
                    "of at least 32 characters."
                )

            if self.JWT_ALGORITHM != "HS256":
                raise ValueError(
                    "JWT_ALGORITHM must be HS256 for this configuration."
                )

            mongo = urlsplit(self.MONGO_URI)
            if (
                mongo.scheme not in ("mongodb", "mongodb+srv")
                or not mongo.hostname
                or not mongo.username
                or not mongo.password
                or mongo.hostname.lower() in (
                    "localhost",
                    "127.0.0.1",
                    "::1",
                )
            ):
                raise ValueError(
                    "Production requires a reachable MongoDB URI with authentication."
                )

            if (
                frontend.scheme != "https"
                or frontend.hostname.lower() in (
                    "localhost",
                    "127.0.0.1",
                    "::1",
                )
                or frontend.hostname.endswith(".example")
            ):
                raise ValueError(
                    "Production FRONTEND_URL must use a public HTTPS origin."
                )

            for origin in self.CORS_ORIGINS:
                parsed_origin = urlsplit(origin)
                if parsed_origin.scheme != "https":
                    raise ValueError(
                        "Production CORS origins must use HTTPS."
                    )

            if self.FRONTEND_URL not in self.CORS_ORIGINS:
                raise ValueError(
                    "FRONTEND_URL must also be included in CORS_ORIGINS."
                )

            if not self.DB_NAME.strip():
                raise ValueError("DB_NAME must not be empty.")

        elif not self.JWT_SECRET_KEY:
            # Convenient for local development only. Set a stable secret
            # in backend/.env if you need tokens to survive restarts.
            object.__setattr__(
                self,
                "JWT_SECRET_KEY",
                secrets.token_urlsafe(32),
            )

        return self


settings = Settings()