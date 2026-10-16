# import uuid
# import logging
# from datetime import datetime
# from typing import Optional
# from fastapi import APIRouter, HTTPException
# from bson import ObjectId
# from app.database import get_db
# from app.models.schemas import AccountVerificationRequest
# from app.services.x_service import fetch_x_profile, sanitize_x_identifier
# from app.services.risk_assessment_service import assess_account_risk

# logger = logging.getLogger("brandshield.routes.x_twitter")
# router = APIRouter(prefix="/x", tags=["X Risk Analyzer"])

# @router.post("/analyze")
# async def analyze_x_account(req: AccountVerificationRequest):
#     """
#     Dedicated X (Twitter) Profile Analyzer endpoint.
#     Retrieves X API v2 telemetry, evaluates brand impersonation likeness,
#     and returns explainable risk analysis.
#     """
#     clean_handle = sanitize_x_identifier(req.account_identifier)
#     if not clean_handle:
#         raise HTTPException(status_code=400, detail="X (Twitter) handle or profile URL is required.")

#     db = get_db()
#     brand = None
#     official_assets = []

#     if db is not None and req.brand_id and ObjectId.is_valid(req.brand_id):
#         brand = await db.brands.find_one({"_id": ObjectId(req.brand_id)})
#         if brand:
#             off_cursor = db.official_assets.find({"brand_id": req.brand_id})
#             official_assets = await off_cursor.to_list(length=100)

#     if not brand and db is not None:
#         brand = await db.brands.find_one({"is_archived": {"$ne": True}})
#         if brand:
#             off_cursor = db.official_assets.find({"brand_id": str(brand["_id"])})
#             official_assets = await off_cursor.to_list(length=100)

#     profile = await fetch_x_profile(clean_handle, force_live_api=req.force_live_api)
#     risk_data = assess_account_risk(profile, brand, official_assets)

#     scan_id = str(uuid.uuid4())
#     now = datetime.utcnow()

#     result = {
#         "analysis_id": scan_id,
#         "platform": "X",
#         "profile": profile,
#         "risk": risk_data,
#         "brand_name": brand.get("name") if brand else "Brand",
#         "brand_id": str(brand["_id"]) if brand and "_id" in brand else req.brand_id,
#         "created_at": now
#     }

#     if db is not None:
#         try:
#             await db.scan_history.insert_one({
#                 "scan_id": scan_id,
#                 "brand_id": result["brand_id"],
#                 "brand_name": result["brand_name"],
#                 "platform": "X",
#                 "username": profile["username"],
#                 "display_name": profile["display_name"],
#                 "profile_url": profile["profile_url"],
#                 "official_platform_verification": profile["official_platform_verification"],
#                 "risk_score": risk_data["risk_score"],
#                 "risk_category": risk_data["risk_category"],
#                 "primary_threat": risk_data["reasons"][0] if risk_data.get("reasons") else "Profile Checked",
#                 "data_source": profile["data_source"],
#                 "scanned_at": now
#             })
#         except Exception as e:
#             logger.warning(f"Error saving X scan history: {e}")

#     return result
import uuid
import logging
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    readable_brand_filter,
    shared_demo_brand_filter,
)
from app.models.schemas import AccountVerificationRequest
from app.services.auth_service import require_current_user
from app.services.x_service import fetch_x_profile, sanitize_x_identifier
from app.services.risk_assessment_service import assess_account_risk

logger = logging.getLogger("brandshield.routes.x_twitter")

router = APIRouter(prefix="/x", tags=["X Risk Analyzer"])


def get_user_id(user: dict) -> str:
    user_id = user.get("_id") or user.get("id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid user session")
    return str(user_id)


async def get_readable_brand(db, brand_id: str, user_id: str):
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
        "is_archived": {"$ne": True},
    })

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    return brand


@router.post("/analyze")
async def analyze_x_account(
    req: AccountVerificationRequest,
    current_user: dict = Depends(require_current_user),
):
    """Analyze an X profile using an accessible brand and save private history."""
    user_id = get_user_id(current_user)

    clean_handle = sanitize_x_identifier(req.account_identifier)
    if not clean_handle:
        raise HTTPException(
            status_code=400,
            detail="X (Twitter) handle or profile URL is required.",
        )

    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Please try again later.",
        )

    brand = None
    official_assets = []

    try:
        if req.brand_id:
            brand = await get_readable_brand(db, req.brand_id, user_id)
        else:
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
            cursor = db.official_assets.find(
                brand_child_filter(brand, user_id)
            )
            official_assets = await cursor.to_list(length=100)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unable to load X analysis brand data")
        raise HTTPException(
            status_code=500,
            detail="Unable to prepare X analysis",
        )

    try:
        profile = await fetch_x_profile(
            clean_handle,
            force_live_api=req.force_live_api,
        )
        risk_data = assess_account_risk(profile, brand, official_assets)
    except HTTPException:
        raise
    except Exception:
        logger.exception("X profile analysis failed")
        raise HTTPException(
            status_code=502,
            detail="Unable to analyze this X profile right now",
        )

    scan_id = str(uuid.uuid4())
    now = datetime.utcnow()

    result = {
        "analysis_id": scan_id,
        "platform": "X",
        "profile": profile,
        "risk": risk_data,
        "brand_name": brand.get("name") if brand else "Brand",
        "brand_id": str(brand["_id"]) if brand else None,
        "created_at": now,
    }

    history_doc = {
        "scan_id": scan_id,
        "owner_id": user_id,
        "brand_id": result["brand_id"],
        "brand_name": result["brand_name"],
        "platform": "X",
        "username": profile.get("username"),
        "display_name": profile.get("display_name"),
        "profile_url": profile.get("profile_url"),
        "official_platform_verification": profile.get(
            "official_platform_verification"
        ),
        "risk_score": risk_data.get("risk_score"),
        "risk_category": risk_data.get("risk_category"),
        "primary_threat": (
            risk_data.get("reasons", ["Profile Checked"])[0]
            if risk_data.get("reasons")
            else "Profile Checked"
        ),
        "data_source": profile.get("data_source"),
        "scanned_at": now,
    }

    try:
        await db.scan_history.insert_one(history_doc)
    except Exception:
        logger.exception("Unable to save X scan history")
        raise HTTPException(
            status_code=500,
            detail="Analysis completed, but saving its history failed",
        )

    return result