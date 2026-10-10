import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection, get_db
from app.services.demo_service import ensure_sample_brands, load_demo_data

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
    users
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("brandshield.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing BrandShield AI Backend...")
    await connect_to_mongo()
    
    # Check if database has any brands; if empty, automatically seed initial demo data
    try:
        db = get_db()
        count = await db.brands.count_documents({})
        if count == 0:
            logger.info("Database is empty. Automatically loading initial ABC Bank demo environment...")
            await load_demo_data(db)
        await ensure_sample_brands(db)
    except Exception as e:
        logger.warning(f"Could not auto-seed demo data on startup: {e}")
        
    yield
    logger.info("Shutting down BrandShield AI Backend...")
    await close_mongo_connection()

app = FastAPI(
    title="BrandShield AI - Digital Risk Protection Platform API",
    description="Enterprise API for Social Media Monitoring, App Store Monitoring, and Brand Impersonation Detection.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Directory for Persistent Brand Logos
from pathlib import Path
from fastapi.staticfiles import StaticFiles
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "logos").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount Routes
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

@app.get("/")
async def root():
    return {
        "platform": "BrandShield AI",
        "tagline": "Detect impersonation before it harms your brand.",
        "status": "OPERATIONAL",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "brandshield-backend"}
