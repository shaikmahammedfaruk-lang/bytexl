
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