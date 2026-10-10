import os
import secrets
from urllib.parse import urlsplit
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "BrandShield AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "brandshield_ai")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: list[str] = ["*"]

    # Meta Graph & Instagram API Configuration
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    META_GRAPH_API_VERSION: str = os.getenv("META_GRAPH_API_VERSION", "v21.0")
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    INSTAGRAM_DEMO_MODE: bool = os.getenv("INSTAGRAM_DEMO_MODE", "true").lower() in ("true", "1", "yes")

    # Facebook Meta Graph API Configuration
    FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    FACEBOOK_APP_ID: str = os.getenv("FACEBOOK_APP_ID", "")
    FACEBOOK_APP_SECRET: str = os.getenv("FACEBOOK_APP_SECRET", "")

    # X (Twitter) API v2 Configuration
    X_BEARER_TOKEN: str = os.getenv("X_BEARER_TOKEN", "")
    X_API_KEY: str = os.getenv("X_API_KEY", "")
    X_API_SECRET: str = os.getenv("X_API_SECRET", "")
    X_API_TIER: str = os.getenv("X_API_TIER", "v2_free_basic")

    # LinkedIn Community & Organizational API Configuration
    LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")

    # Multi-Platform Sandbox & Graceful Fallback Mode
    PLATFORM_SANDBOX_MODE: bool = os.getenv("PLATFORM_SANDBOX_MODE", "true").lower() in ("true", "1", "yes")

    # Authentication & JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    # Email & SMTP Configuration for Password Reset & Verification
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "security@brandshield.ai")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    REQUIRE_EMAIL_VERIFICATION: bool = os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").lower() in ("true", "1", "yes")

    class Config:
        env_file = ".env"

settings = Settings()
settings.FRONTEND_URL = settings.FRONTEND_URL.rstrip("/")

if settings.ENVIRONMENT.lower() == "production":
    if len(settings.JWT_SECRET_KEY) < 32 or "replace_" in settings.JWT_SECRET_KEY.lower():
        raise RuntimeError("Set JWT_SECRET_KEY to a unique random value of at least 32 characters in production.")

    mongo_host = urlsplit(settings.MONGO_URI).hostname
    if not mongo_host or mongo_host in ("localhost", "127.0.0.1", "::1"):
        raise RuntimeError("Set MONGO_URI to the reachable MongoDB URL for this deployment.")

    frontend_url = urlsplit(settings.FRONTEND_URL)
    frontend_host = frontend_url.hostname
    if (
        frontend_url.scheme != "https"
        or not frontend_url.netloc
        or not frontend_host
        or frontend_host in ("localhost", "127.0.0.1", "::1")
        or frontend_host.endswith(".example")
    ):
        raise RuntimeError("Set FRONTEND_URL to the public HTTPS URL of this deployment.")
elif not settings.JWT_SECRET_KEY:
    settings.JWT_SECRET_KEY = secrets.token_urlsafe(32)
