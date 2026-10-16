# import uuid
# import logging
# from datetime import datetime
# from typing import List, Optional
# from fastapi import APIRouter, HTTPException, Query
# from bson import ObjectId
# from app.database import get_db
# from app.models.schemas import (
#     DuplicateDetectionRequest,
#     DuplicateDetectionResponse
# )
# from app.services.duplicate_detection_service import detect_duplicate_accounts

# logger = logging.getLogger("brandshield.routes.duplicate_detection")
# router = APIRouter(prefix="/duplicate-detection", tags=["Duplicate & Impersonation Detection"])

# def serialize_doc(doc: dict) -> dict:
#     if not doc:
#         return doc
#     doc["id"] = str(doc.pop("_id"))
#     return doc

# @router.post("/scan", response_model=DuplicateDetectionResponse)
# async def scan_duplicates(req: DuplicateDetectionRequest):
#     """
#     Scans for duplicate or impersonating accounts matching a reference account or protected brand.
#     Combines existing active threat feeds with multi-signal lookalike discovery across platforms.
#     """
#     db = get_db()
#     brand = None
#     existing_threats = []

#     if db is not None:
#         try:
#             if req.brand_id and ObjectId.is_valid(req.brand_id):
#                 brand = await db.brands.find_one({"_id": ObjectId(req.brand_id)})
#                 cursor = db.threats.find({"brand_id": req.brand_id, "is_official_safe": {"$ne": True}})
#                 existing_threats = await cursor.to_list(length=100)
            
#             if not brand:
#                 all_brands = await db.brands.find({"is_archived": {"$ne": True}}).to_list(1)
#                 if all_brands:
#                     brand = all_brands[0]
#                     cursor = db.threats.find({"brand_id": str(brand["_id"]), "is_official_safe": {"$ne": True}})
#                     existing_threats = await cursor.to_list(length=100)
#         except Exception as e:
#             logger.warning(f"Error accessing brand threats for duplicate scan: {e}")

#     brand_name = (brand.get("name") if brand else "") or req.target_keyword or "Protected Brand"

#     result = detect_duplicate_accounts(
#         brand_name=brand_name,
#         platform=req.platform or "ALL",
#         reference_account_url=req.reference_account_url,
#         threshold=req.threshold or 40.0,
#         existing_threats=existing_threats
#     )

#     now = datetime.utcnow()
#     result["timestamp"] = now

#     # Store detection run in MongoDB for audit history
#     if db is not None:
#         try:
#             doc_to_save = dict(result)
#             doc_to_save["brand_id"] = str(brand["_id"]) if brand and "_id" in brand else req.brand_id
#             doc_to_save["created_at"] = now
#             await db.duplicate_scans.insert_one(doc_to_save)
#         except Exception as e:
#             logger.warning(f"Error storing duplicate scan: {e}")

#     return result

# @router.get("/history")
# async def get_duplicate_history(brand_id: Optional[str] = None, limit: int = 10):
#     db = get_db()
#     if db is None:
#         return []
#     query = {}
#     if brand_id and ObjectId.is_valid(brand_id):
#         query["brand_id"] = brand_id
#     cursor = db.duplicate_scans.find(query).sort("created_at", -1).limit(limit)
#     items = await cursor.to_list(length=limit)
#     return [serialize_doc(it) for it in items]



import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    readable_brand_filter,
    shared_demo_brand_filter,
)
from app.models.schemas import (
    DuplicateDetectionRequest,
    DuplicateDetectionResponse,
)
from app.services.duplicate_detection_service import detect_duplicate_accounts
from app.services.auth_service import require_current_user

logger = logging.getLogger("brandshield.routes.duplicate_detection")

router = APIRouter(
    prefix="/duplicate-detection",
    tags=["Duplicate & Impersonation Detection"],
)


def get_user_id(user: dict) -> str:
    """Return the authenticated user's ID."""
    user_id = user.get("_id") or user.get("id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid user session")
    return str(user_id)


def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB documents into JSON-compatible dictionaries."""
    if not doc:
        return doc

    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


async def get_readable_brand(db, brand_id: str, user_id: str):
    """Allow access only to the user's own brand or a shared demo brand."""
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
    })

    if not brand or brand.get("is_archived", False):
        raise HTTPException(status_code=404, detail="Brand not found")

    return brand


@router.post("/scan", response_model=DuplicateDetectionResponse)
async def scan_duplicates(
    req: DuplicateDetectionRequest,
    current_user: dict = Depends(require_current_user),
):
    """
    Scan for duplicate or impersonating accounts using an accessible brand.
    Only the authenticated user's brands and shared demo brands are accessible.
    """
    user_id = get_user_id(current_user)
    db = get_db()

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Please try again later.",
        )

    brand = None
    existing_threats = []

    try:
        if req.brand_id:
            brand = await get_readable_brand(db, req.brand_id, user_id)
        else:
            # Do not silently select another user's first brand.
            brand = await db.brands.find_one(
                {
                    "owner_id": user_id,
                    "is_archived": {"$ne": True},
                }
            )

            if not brand:
                brand = await db.brands.find_one(
                    {
                        **shared_demo_brand_filter(),
                        "is_archived": {"$ne": True},
                    }
                )

        if brand:
            brand_id = str(brand["_id"])
            threat_query = {
                **brand_child_filter(brand, user_id),
                "is_official_safe": {"$ne": True},
            }

            cursor = db.threats.find(threat_query)
            existing_threats = await cursor.to_list(length=100)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error accessing brand threats for duplicate scan")
        raise HTTPException(
            status_code=500,
            detail="Unable to prepare duplicate scan",
        )

    brand_name = (
        (brand.get("name") if brand else None)
        or req.target_keyword
        or "Protected Brand"
    )

    result = detect_duplicate_accounts(
        brand_name=brand_name,
        platform=req.platform or "ALL",
        reference_account_url=req.reference_account_url,
        threshold=(
            req.threshold if req.threshold is not None else 40.0
        ),
        existing_threats=existing_threats,
    )

    now = datetime.utcnow()
    result["timestamp"] = now

    # Keep each scan private to the authenticated user.
    doc_to_save = dict(result)
    doc_to_save["owner_id"] = user_id
    doc_to_save["brand_id"] = str(brand["_id"]) if brand else None
    doc_to_save["created_at"] = now
    doc_to_save["is_demo"] = False

    try:
        await db.duplicate_scans.insert_one(doc_to_save)
    except Exception:
        logger.exception("Error storing duplicate scan")
        raise HTTPException(
            status_code=500,
            detail="Unable to save scan history",
        )

    return result


@router.get("/history")
async def get_duplicate_history(
    brand_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: dict = Depends(require_current_user),
):
    """Return only the authenticated user's duplicate-scan history."""
    user_id = get_user_id(current_user)
    db = get_db()

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Please try again later.",
        )

    query = {"owner_id": user_id}

    if brand_id:
        brand = await get_readable_brand(db, brand_id, user_id)
        query["brand_id"] = str(brand["_id"])

    cursor = (
        db.duplicate_scans.find(query)
        .sort("created_at", -1)
        .limit(limit)
    )
    items = await cursor.to_list(length=limit)

    return [serialize_doc(item) for item in items]