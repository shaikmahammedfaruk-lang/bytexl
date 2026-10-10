import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import (
    AccountVerificationRequest,
    AccountVerificationResponse,
    AccountProfileData,
    IdentityConsistencyIndicators,
    RiskAssessmentResult,
    ScanHistoryItem
)
from app.services.facebook_service import fetch_facebook_profile
from app.services.x_service import fetch_x_profile
from app.services.linkedin_service import fetch_linkedin_profile
from app.services.instagram_service import fetch_instagram_profile, sanitize_instagram_username
from app.services.risk_assessment_service import assess_account_risk

logger = logging.getLogger("brandshield.routes.verification")
router = APIRouter(prefix="/verification", tags=["Multi-Platform Verification"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.post("/verify-account", response_model=AccountVerificationResponse)
async def verify_account(req: AccountVerificationRequest):
    """
    Unified multi-platform account verification endpoint.
    Supports Instagram, Facebook, X (Twitter), and LinkedIn.
    Returns official platform verification badge, BrandShield authenticity risk assessment,
    identity consistency telemetry, and audit timestamps.
    """
    platform = req.platform.strip()
    identifier = req.account_identifier.strip()
    if not identifier:
        raise HTTPException(status_code=400, detail="Account URL or identifier is required.")

    db = get_db()
    brand = None
    official_assets = []

    # Retrieve protected brand ground truth
    if db is not None:
        try:
            if req.brand_id and ObjectId.is_valid(req.brand_id):
                brand = await db.brands.find_one({"_id": ObjectId(req.brand_id)})
                if brand:
                    off_cursor = db.official_assets.find({"brand_id": req.brand_id})
                    official_assets = await off_cursor.to_list(length=100)
            
            if not brand and req.brand_name:
                brand = await db.brands.find_one({"name": {"$regex": f"^{re.escape(req.brand_name)}$", "$options": "i"}})
            
            if not brand:
                all_brands = await db.brands.find({"is_archived": {"$ne": True}}).to_list(10)
                if all_brands:
                    brand = all_brands[0]
                    off_cursor = db.official_assets.find({"brand_id": str(brand["_id"])})
                    official_assets = await off_cursor.to_list(length=100)
        except Exception as e:
            logger.warning(f"Error fetching brand context: {e}")

    brand_name = (brand.get("name") if brand else "") or req.brand_name or "Protected Brand"
    brand_id = str(brand["_id"]) if brand and "_id" in brand else req.brand_id

    # Dispatch to platform service
    try:
        if platform.lower() in ("instagram", "ig"):
            clean_user = sanitize_instagram_username(identifier)
            ig_raw = await fetch_instagram_profile(clean_user, force_demo=not req.force_live_api)
            is_verif = ig_raw.get("is_verified", False)
            profile_dict = {
                "platform": "Instagram",
                "profile_url": f"https://www.instagram.com/{clean_user}/",
                "username": clean_user,
                "display_name": ig_raw.get("display_name") or clean_user.title(),
                "official_platform_verification": "Verified" if is_verif else "Not Verified",
                "verification_badge_type": "Meta Verified" if is_verif else "None",
                "avatar_url": ig_raw.get("profile_picture_url"),
                "bio": ig_raw.get("biography"),
                "followers_count": ig_raw.get("followers_count", 0),
                "following_count": ig_raw.get("following_count", 0),
                "media_or_posts_count": ig_raw.get("media_count", 0),
                "account_created_date": None,
                "website": ig_raw.get("website"),
                "page_category": "Instagram Profile",
                "data_source": "Meta Graph API (Instagram Graph)",
                "api_limitations_notice": None
            }
        elif platform.lower() in ("facebook", "fb"):
            profile_dict = await fetch_facebook_profile(identifier, force_live_api=req.force_live_api)
        elif platform.lower() in ("x", "twitter"):
            profile_dict = await fetch_x_profile(identifier, force_live_api=req.force_live_api)
        elif platform.lower() in ("linkedin", "li"):
            profile_dict = await fetch_linkedin_profile(identifier, force_live_api=req.force_live_api)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform '{platform}'. Choose Instagram, Facebook, X, or LinkedIn.")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching profile from {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to retrieve profile from {platform}: {str(e)}")

    # Execute explainable risk assessment
    risk_data = assess_account_risk(
        profile_data=profile_dict,
        brand_data=brand,
        official_assets=official_assets
    )

    # Derive identity consistency signals
    exact_match = (profile_dict["username"].lower() == brand_name.lower().replace(" ", ""))
    lookalike_detected = risk_data["risk_score"] >= 35.0
    official_mismatch = (risk_data["risk_score"] > 0)

    identity_indicators = {
        "exact_name_match": exact_match,
        "lookalike_detected": lookalike_detected,
        "brand_keyword_presence": any(kw.lower() in (profile_dict.get("bio") or "").lower() for kw in (brand.get("brand_keywords", []) if brand else [])),
        "official_registry_mismatch": official_mismatch,
        "suspicious_contact_patterns": any(w in (profile_dict.get("bio") or "").lower() for w in ["whatsapp", "otp", "dm for help", "helpline"]),
        "phishing_indicators": [f["detail"] for f in risk_data.get("evidence_findings", []) if f.get("category") == "DECEPTIVE_CUSTOMER_TARGETING"]
    }

    scan_id = str(uuid.uuid4())
    now = datetime.utcnow()

    response_payload = {
        "scan_id": scan_id,
        "platform": profile_dict["platform"],
        "scanned_identifier": identifier,
        "profile": profile_dict,
        "identity_consistency": identity_indicators,
        "risk": risk_data,
        "brand_id": brand_id,
        "brand_name": brand_name,
        "timestamp": now
    }

    # Record scan history in MongoDB
    if db is not None:
        try:
            history_doc = {
                "scan_id": scan_id,
                "brand_id": brand_id,
                "brand_name": brand_name,
                "platform": profile_dict["platform"],
                "username": profile_dict["username"],
                "display_name": profile_dict["display_name"],
                "profile_url": profile_dict["profile_url"],
                "official_platform_verification": profile_dict["official_platform_verification"],
                "risk_score": risk_data["risk_score"],
                "risk_category": risk_data["risk_category"],
                "primary_threat": risk_data["reasons"][0] if risk_data.get("reasons") else "Profile Analyzed",
                "data_source": profile_dict["data_source"],
                "scanned_at": now
            }
            await db.scan_history.insert_one(history_doc)
        except Exception as e:
            logger.warning(f"Could not record scan history: {e}")

    return response_payload

@router.get("/scan-history", response_model=List[ScanHistoryItem])
async def get_scan_history(
    brand_id: Optional[str] = None,
    platform: Optional[str] = None,
    risk_category: Optional[str] = None,
    limit: int = Query(50, le=100)
):
    """
    Returns scan history for multi-platform verifications.
    """
    db = get_db()
    if db is None:
        return []

    query = {}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id
    if platform and platform != "ALL":
        query["platform"] = platform
    if risk_category and risk_category != "ALL":
        query["risk_category"] = risk_category

    cursor = db.scan_history.find(query).sort("scanned_at", -1).limit(limit)
    items = await cursor.to_list(length=limit)
    return [serialize_doc(it) for it in items]

@router.delete("/scan-history/{id}")
async def delete_scan_history_item(id: str):
    db = get_db()
    if db is None:
        return {"status": "ok"}
    if ObjectId.is_valid(id):
        await db.scan_history.delete_one({"_id": ObjectId(id)})
    else:
        await db.scan_history.delete_one({"scan_id": id})
    return {"status": "success", "message": "Scan history record deleted"}
