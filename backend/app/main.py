import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import (
    connect_to_mongo,
    close_mongo_connection,
    get_db,
)
from app.services.demo_service import ensure_sample_brands

from app.routes import (
    brands,
    social,
    apps,
    scan_link,
    threats,
    investigations,
    campaigns,
    analytics,
    alerts,
    evidence,
    demo,
    instagram,
    authenticity,
    verification,
    duplicate_detection,
    facebook,
    x_twitter,
    linkedin,
    reports,
    user_profile,
    auth,
    users,
)


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("brandshield.main")


# --------------------------------------------------
# Application lifecycle
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing BrandShield AI backend...")

    # Fail startup if the database connection fails.
    await connect_to_mongo()

    try:
        db = get_db()

        # Add only missing shared starter brands.
        # Do not run the destructive demo-data loader here.
        await ensure_sample_brands(db)

        logger.info("Shared starter brand initialization completed.")

        yield

    except Exception:
        logger.exception("Backend initialization or runtime failed.")
        raise

    finally:
        logger.info("Shutting down BrandShield AI backend...")
        await close_mongo_connection()


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="BrandShield AI - Digital Risk Protection Platform API",
    description=(
        "Enterprise API for Social Media Monitoring, "
        "App Store Monitoring, and Brand Impersonation Detection."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------
# CORS configuration
# --------------------------------------------------

# Use the validated origins from config.py consistently.
allowed_origins = [
    origin.strip().rstrip("/")
    for origin in settings.CORS_ORIGINS
    if origin.strip()
]

if not allowed_origins:
    raise RuntimeError(
        "CORS is not configured. Set CORS_ORIGINS in the backend environment."
    )

if "*" in allowed_origins:
    raise RuntimeError(
        "Wildcard CORS origins are not allowed."
    )

logger.info("CORS configured for %d origin(s).", len(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
    ],
)


# --------------------------------------------------
# Static files
# --------------------------------------------------

STATIC_DIR = Path(__file__).resolve().parent / "static"
LOGOS_DIR = STATIC_DIR / "logos"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
LOGOS_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


@app.middleware("http")
async def protect_static_uploads(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.lower().endswith(".svg"):
            response.headers["Content-Disposition"] = (
                'attachment; filename="download.svg"'
            )
    return response


# --------------------------------------------------
# API routes
# --------------------------------------------------

app.include_router(brands.router, prefix=settings.API_V1_STR)
app.include_router(social.router, prefix=settings.API_V1_STR)
app.include_router(apps.router, prefix=settings.API_V1_STR)
app.include_router(scan_link.router, prefix=settings.API_V1_STR)
app.include_router(threats.router, prefix=settings.API_V1_STR)
app.include_router(investigations.router, prefix=settings.API_V1_STR)
app.include_router(campaigns.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(evidence.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)
app.include_router(instagram.router, prefix=settings.API_V1_STR)
app.include_router(authenticity.router, prefix=settings.API_V1_STR)
app.include_router(verification.router, prefix=settings.API_V1_STR)
app.include_router(duplicate_detection.router, prefix=settings.API_V1_STR)
app.include_router(facebook.router, prefix=settings.API_V1_STR)
app.include_router(x_twitter.router, prefix=settings.API_V1_STR)
app.include_router(linkedin.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(user_profile.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)


# --------------------------------------------------
# Health endpoints
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "platform": "BrandShield AI",
        "tagline": "Detect impersonation before it harms your brand.",
        "status": "OPERATIONAL",
        "version": "1.0.0",
        "documentation": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "brandshield-backend",
    }