
import logging
from datetime import datetime

from pymongo.errors import DuplicateKeyError


logger = logging.getLogger("brandshield.demo_service")


async def ensure_sample_brands(db):
    """
    Create shared, read-only starter brands when they do not exist.

    Never modify existing records or treat a private user's brand
    as a shared demo brand merely because its name matches.
    """
    now = datetime.utcnow()

    sample_brands = [
        {
            "name": "Puma",
            "website": "https://us.puma.com",
            "industry": "Sportswear & Apparel",
            "description": "Shared demo profile for Puma digital asset monitoring.",
            "brand_keywords": ["puma", "sportswear", "sneakers", "running"],
            "brand_aliases": ["PUMA SE"],
        },
        {
            "name": "OneNight",
            "industry": "Other",
            "description": "Shared starter profile for OneNight.",
            "brand_keywords": ["onenight", "one night"],
            "brand_aliases": [],
        },
        {
            "name": "Sparks",
            "industry": "Other",
            "description": "Shared starter profile for Sparks.",
            "brand_keywords": ["sparks"],
            "brand_aliases": [],
        },
    ]

    for sample in sample_brands:
        # Match only a record explicitly marked as shared demo data.
        # A private brand with the same name does not count as a match.
        existing_demo = await db.brands.find_one(
            {
                "name": sample["name"],
                "owner_id": None,
                "is_demo": True,
                "is_shared": True,
            },
            {"_id": 1},
        )

        if existing_demo:
            continue

        brand_document = {
            **sample,
            "owner_id": None,
            "is_demo": True,
            "is_shared": True,
            "is_archived": False,
            "created_at": now,
            "updated_at": now,
        }

        try:
            await db.brands.insert_one(brand_document)
            logger.info(
                "Created shared starter brand: %s",
                sample["name"],
            )
        except DuplicateKeyError:
            # Another startup may have inserted the same record.
            # Do not update or overwrite any existing document.
            logger.info(
                "Starter brand already exists: %s",
                sample["name"],
            )