import uuid
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.database import get_db
from app.models.schemas import AccountVerificationRequest
from app.services.facebook_service import fetch_facebook_profile, sanitize_facebook_identifier
from app.services.risk_assessment_service import assess_account_risk

logger = logging.getLogger("brandshield.routes.facebook")
router = APIRouter(prefix="/facebook", tags=["Facebook Risk Analyzer"])

@router.post("/analyze")
async def analyze_facebook_account(req: AccountVerificationRequest):
    """
    Dedicated Facebook Page & Profile Analyzer endpoint.
    Retrieves Meta Graph telemetry, evaluates brand impersonation likeness,
    and returns explainable risk analysis.
    """
    clean_id = sanitize_facebook_identifier(req.account_identifier)
    if not clean_id:
        raise HTTPException(status_code=400, detail="Facebook Page URL or username is required.")

    db = get_db()
    brand = None
    official_assets = []

    if db is not None and req.brand_id and ObjectId.is_valid(req.brand_id):
        brand = await db.brands.find_one({"_id": ObjectId(req.brand_id)})
        if brand:
            off_cursor = db.official_assets.find({"brand_id": req.brand_id})
            official_assets = await off_cursor.to_list(length=100)

    if not brand and db is not None:
        brand = await db.brands.find_one({"is_archived": {"$ne": True}})
        if brand:
            off_cursor = db.official_assets.find({"brand_id": str(brand["_id"])})
            official_assets = await off_cursor.to_list(length=100)

    profile = await fetch_facebook_profile(clean_id, force_live_api=req.force_live_api)
    risk_data = assess_account_risk(profile, brand, official_assets)

    scan_id = str(uuid.uuid4())
    now = datetime.utcnow()

    result = {
        "analysis_id": scan_id,
        "platform": "Facebook",
        "profile": profile,
        "risk": risk_data,
        "brand_name": brand.get("name") if brand else "Brand",
        "brand_id": str(brand["_id"]) if brand and "_id" in brand else req.brand_id,
        "created_at": now
    }

    if db is not None:
        try:
            await db.scan_history.insert_one({
                "scan_id": scan_id,
                "brand_id": result["brand_id"],
                "brand_name": result["brand_name"],
                "platform": "Facebook",
                "username": profile["username"],
                "display_name": profile["display_name"],
                "profile_url": profile["profile_url"],
                "official_platform_verification": profile["official_platform_verification"],
                "risk_score": risk_data["risk_score"],
                "risk_category": risk_data["risk_category"],
                "primary_threat": risk_data["reasons"][0] if risk_data.get("reasons") else "Profile Checked",
                "data_source": profile["data_source"],
                "scanned_at": now
            })
        except Exception as e:
            logger.warning(f"Error saving FB scan history: {e}")

    return result
