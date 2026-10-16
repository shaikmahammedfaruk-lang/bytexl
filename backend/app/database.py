# import logging
# from motor.motor_asyncio import AsyncIOMotorClient
# from app.config import settings

# logger = logging.getLogger("brandshield.db")

# class Database:
#     client: AsyncIOMotorClient = None
#     db = None

# db_instance = Database()

# async def connect_to_mongo():
#     logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}...")
#     try:
#         db_instance.client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
#         db_instance.db = db_instance.client[settings.DB_NAME]
#         # Quick ping to verify connectivity
#         await db_instance.client.admin.command('ping')
#         logger.info(f"Successfully connected to MongoDB database: {settings.DB_NAME}")
        
#         # Create helpful indexes
#         await db_instance.db.brands.create_index("name", unique=True)
#         await db_instance.db.official_assets.create_index([("brand_id", 1), ("url", 1)])
#         await db_instance.db.threats.create_index([("brand_id", 1), ("risk_score", -1)])
#         await db_instance.db.threats.create_index("url")
#         await db_instance.db.threats.create_index("status")
#         await db_instance.db.campaigns.create_index("brand_id")
#         await db_instance.db.investigations.create_index("threat_id")
#         await db_instance.db.alerts.create_index([("brand_id", 1), ("created_at", -1)])
#         await db_instance.db.instagram_analyses.create_index([("username", 1), ("created_at", -1)])
#         await db_instance.db.instagram_analyses.create_index("brand_id")
#         await db_instance.db.instagram_profiles.create_index("username", unique=True)
        
#         # User & Auth Indexes
#         await db_instance.db.users.create_index("email", unique=True)
#         await db_instance.db.users.create_index("google_id", sparse=True)
#         await db_instance.db.password_resets.create_index("token_hash", unique=True)
#         await db_instance.db.email_verifications.create_index("token_hash", unique=True)
        
#         # Ensure default Analyst user exists
#         await ensure_default_user(db_instance.db)
#     except Exception as e:
#         logger.error(f"Error connecting to MongoDB: {e}. Will use fallback or retry on request.")

# async def ensure_default_user(db):
#     try:
#         import bcrypt
#         from datetime import datetime, timezone
#         user = await db.users.find_one({"email": "analyst@brandshield.ai"})
#         if not user:
# Legacy built-in account credential seed removed; existing DB accounts require manual review.
#             default_doc = {
#                 "username": "secops_analyst",
#                 "email": "analyst@brandshield.ai",
#                 "password_hash": pw_hash,
#                 "full_name": "Security Operations Analyst",
#                 "role": "Tier 2 SOC Lead",
#                 "organization": "Global SOC Ops",
#                 "phone": "+1 (555) 019-2834",
#                 "department": "Cyber Digital Risk Protection",
#                 "provider": "local",
#                 "email_verified": True,
#                 "created_at": datetime.now(timezone.utc).isoformat(),
#                 "last_login": datetime.now(timezone.utc).isoformat(),
#                 "is_active": True
#             }
#             await db.users.insert_one(default_doc)
#             logger.info("Default SecOps Analyst user ensured in database.")
#     except Exception as e:
#         logger.warning(f"Could not ensure default user: {e}")

# async def close_mongo_connection():
#     if db_instance.client:
#         logger.info("Closing MongoDB connection...")
#         db_instance.client.close()

# def get_db():
#     return db_instance.db



# import logging

# from motor.motor_asyncio import AsyncIOMotorClient
# from app.config import settings

# logger = logging.getLogger("brandshield.db")


# class Database:
#     client: AsyncIOMotorClient = None
#     db = None


# db_instance = Database()


# async def connect_to_mongo():
#     """Connect to MongoDB and create indexes without exposing credentials."""
#     client = None

#     try:
#         logger.info("Connecting to MongoDB...")

#         client = AsyncIOMotorClient(
#             settings.MONGO_URI,
#             serverSelectionTimeoutMS=5000,
#         )

#         # Verify connectivity before publishing the connection.
#         await client.admin.command("ping")

#         database = client[settings.DB_NAME]

#         # Remove legacy global uniqueness constraints that conflict with
#         # separate users having their own brands or Instagram profiles.
#         # These are the default index names created by the previous code.
#         for collection_name, index_name in (
#             ("brands", "name_1"),
#             ("instagram_profiles", "username_1"),
#         ):
#             try:
#                 await database[collection_name].drop_index(index_name)
#                 logger.info(
#                     "Removed legacy index %s from %s",
#                     index_name,
#                     collection_name,
#                 )
#             except Exception as exc:
#                 # An absent index is normal. Do not expose connection details.
#                 logger.debug(
#                     "Legacy index %s on %s was not removed: %s",
#                     index_name,
#                     collection_name,
#                     type(exc).__name__,
#                 )

#         # Brand names and profile usernames may be repeated across users.
#         await database.brands.create_index(
#             [("owner_id", 1), ("name", 1)],
#             name="owner_brand_name_idx",
#         )

#         await database.official_assets.create_index(
#             [("brand_id", 1), ("url", 1)],
#             name="asset_brand_url_idx",
#         )

#         await database.threats.create_index(
#             [("brand_id", 1), ("risk_score", -1)],
#             name="threat_brand_risk_idx",
#         )
#         await database.threats.create_index("url", name="threat_url_idx")
#         await database.threats.create_index("status", name="threat_status_idx")

#         await database.campaigns.create_index(
#             "brand_id",
#             name="campaign_brand_idx",
#         )
#         await database.investigations.create_index(
#             "threat_id",
#             name="investigation_threat_idx",
#         )
#         await database.alerts.create_index(
#             [("brand_id", 1), ("created_at", -1)],
#             name="alert_brand_created_idx",
#         )

#         await database.instagram_analyses.create_index(
#             [("owner_id", 1), ("username", 1), ("created_at", -1)],
#             name="instagram_analysis_owner_user_created_idx",
#         )
#         await database.instagram_analyses.create_index(
#             "brand_id",
#             name="instagram_analysis_brand_idx",
#         )
#         await database.instagram_profiles.create_index(
#             [("owner_id", 1), ("username", 1)],
#             name="instagram_profile_owner_user_idx",
#         )

#         # Authentication indexes.
#         await database.users.create_index(
#             "email",
#             unique=True,
#             name="user_email_unique_idx",
#         )
#         await database.users.create_index(
#             [("google_id", 1)],
#             sparse=True,
#             name="user_google_id_idx",
#         )
#         await database.password_resets.create_index(
#             "token_hash",
#             unique=True,
#             name="password_reset_token_unique_idx",
#         )
#         await database.email_verifications.create_index(
#             "token_hash",
#             unique=True,
#             name="email_verification_token_unique_idx",
#         )

#         # Publish only a verified connection.
#         db_instance.client = client
#         db_instance.db = database

#         logger.info("MongoDB connection established successfully.")

#     except Exception as exc:
#         if client is not None:
#             client.close()

#         db_instance.client = None
#         db_instance.db = None

#         # Do not log the MongoDB URI or exception text, which may expose
#         # connection details in some driver error messages.
#         logger.error(
#             "MongoDB connection or initialization failed (%s).",
#             type(exc).__name__,
#         )


# async def close_mongo_connection():
#     """Close the client and clear the stored connection state."""
#     if db_instance.client is not None:
#         logger.info("Closing MongoDB connection.")
#         db_instance.client.close()

#     db_instance.client = None
#     db_instance.db = None


# def get_db():
#     """FastAPI dependency that returns the database or None if unavailable."""
#     return db_instance.db



import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

logger = logging.getLogger("brandshield.db")


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None


db_instance = Database()


async def connect_to_mongo():
    """
    Connect to MongoDB and create required indexes.

    If connection or index initialization fails, close the client,
    clear the connection state, and fail startup.
    """
    if db_instance.client is not None and db_instance.db is not None:
        logger.info("MongoDB connection is already initialized.")
        return

    client = None

    try:
        logger.info("Connecting to MongoDB...")

        client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
        )

        # Verify the connection before creating indexes.
        await client.admin.command("ping")

        database = client[settings.DB_NAME]

        # Do not drop indexes automatically during application startup.
        # Any legacy index changes must be reviewed and migrated separately.

        # Brand names can be repeated by different users.
        await database.brands.create_index(
            [("owner_id", 1), ("name", 1)],
            name="owner_brand_name_idx",
        )

        await database.official_assets.create_index(
            [("brand_id", 1), ("url", 1)],
            name="asset_brand_url_idx",
        )

        await database.threats.create_index(
            [("brand_id", 1), ("risk_score", -1)],
            name="threat_brand_risk_idx",
        )
        await database.threats.create_index(
            "url",
            name="threat_url_idx",
        )
        await database.threats.create_index(
            "status",
            name="threat_status_idx",
        )

        await database.campaigns.create_index(
            "brand_id",
            name="campaign_brand_idx",
        )
        await database.investigations.create_index(
            "threat_id",
            name="investigation_threat_idx",
        )
        await database.alerts.create_index(
            [("brand_id", 1), ("created_at", -1)],
            name="alert_brand_created_idx",
        )

        await database.instagram_analyses.create_index(
            [("owner_id", 1), ("username", 1), ("created_at", -1)],
            name="instagram_analysis_owner_user_created_idx",
        )
        await database.instagram_analyses.create_index(
            "brand_id",
            name="instagram_analysis_brand_idx",
        )
        await database.instagram_profiles.create_index(
            [("owner_id", 1), ("username", 1)],
            name="instagram_profile_owner_user_idx",
        )

        # Authentication indexes.
        await database.users.create_index(
            "email",
            unique=True,
            name="user_email_unique_idx",
        )
        await database.users.create_index(
            [("google_id", 1)],
            sparse=True,
            name="user_google_id_idx",
        )
        await database.password_resets.create_index(
            "token_hash",
            unique=True,
            name="password_reset_token_unique_idx",
        )
        await database.email_verifications.create_index(
            "token_hash",
            unique=True,
            name="email_verification_token_unique_idx",
        )

        # Publish the connection only after initialization succeeds.
        db_instance.client = client
        db_instance.db = database

        logger.info("MongoDB connection and index initialization succeeded.")

    except Exception as exc:
        if client is not None:
            client.close()

        db_instance.client = None
        db_instance.db = None

        # Do not log the URI or raw exception details.
        logger.error(
            "MongoDB initialization failed (%s).",
            type(exc).__name__,
        )

        # Fail startup instead of running without a usable database.
        raise RuntimeError(
            "MongoDB initialization failed. Check backend configuration "
            "and database indexes."
        ) from None


async def close_mongo_connection():
    """Close the MongoDB client and clear connection state."""
    if db_instance.client is not None:
        logger.info("Closing MongoDB connection.")
        db_instance.client.close()

    db_instance.client = None
    db_instance.db = None


def get_db():
    """Return the initialized database."""
    if db_instance.db is None:
        raise RuntimeError("Database is not initialized.")

    return db_instance.db