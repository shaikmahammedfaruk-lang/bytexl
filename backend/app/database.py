import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger("brandshield.db")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}...")
    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
        db_instance.db = db_instance.client[settings.DB_NAME]
        # Quick ping to verify connectivity
        await db_instance.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB database: {settings.DB_NAME}")
        
        # Create helpful indexes
        await db_instance.db.brands.create_index("name", unique=True)
        await db_instance.db.official_assets.create_index([("brand_id", 1), ("url", 1)])
        await db_instance.db.threats.create_index([("brand_id", 1), ("risk_score", -1)])
        await db_instance.db.threats.create_index("url")
        await db_instance.db.threats.create_index("status")
        await db_instance.db.campaigns.create_index("brand_id")
        await db_instance.db.investigations.create_index("threat_id")
        await db_instance.db.alerts.create_index([("brand_id", 1), ("created_at", -1)])
        await db_instance.db.instagram_analyses.create_index([("username", 1), ("created_at", -1)])
        await db_instance.db.instagram_analyses.create_index("brand_id")
        await db_instance.db.instagram_profiles.create_index("username", unique=True)
        
        # User & Auth Indexes
        await db_instance.db.users.create_index("email", unique=True)
        await db_instance.db.users.create_index("google_id", sparse=True)
        await db_instance.db.password_resets.create_index("token_hash", unique=True)
        await db_instance.db.email_verifications.create_index("token_hash", unique=True)
        
        # Ensure default Analyst user exists
        await ensure_default_user(db_instance.db)
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}. Will use fallback or retry on request.")

async def ensure_default_user(db):
    try:
        import bcrypt
        from datetime import datetime, timezone
        user = await db.users.find_one({"email": "analyst@brandshield.ai"})
        if not user:
            pw_hash = bcrypt.hashpw(b"BrandShield@2026", bcrypt.gensalt()).decode("utf-8")
            default_doc = {
                "username": "secops_analyst",
                "email": "analyst@brandshield.ai",
                "password_hash": pw_hash,
                "full_name": "Security Operations Analyst",
                "role": "Tier 2 SOC Lead",
                "organization": "Global SOC Ops",
                "phone": "+1 (555) 019-2834",
                "department": "Cyber Digital Risk Protection",
                "provider": "local",
                "email_verified": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }
            await db.users.insert_one(default_doc)
            logger.info("Default SecOps Analyst user ensured in database.")
    except Exception as e:
        logger.warning(f"Could not ensure default user: {e}")

async def close_mongo_connection():
    if db_instance.client:
        logger.info("Closing MongoDB connection...")
        db_instance.client.close()

def get_db():
    return db_instance.db
