# import uuid
# import logging
# from datetime import datetime
# from typing import List, Optional
# from fastapi import APIRouter, HTTPException, Query
# from bson import ObjectId
# from app.database import get_db
# from app.models.schemas import (
#     AccountVerificationRequest,
#     AccountVerificationResponse,
#     AccountProfileData,
#     IdentityConsistencyIndicators,
#     RiskAssessmentResult,
#     ScanHistoryItem
# )
# from app.services.facebook_service import fetch_facebook_profile
# from app.services.x_service import fetch_x_profile
# from app.services.linkedin_service import fetch_linkedin_profile
# from app.services.instagram_service import fetch_instagram_profile, sanitize_instagram_username
# from app.services.risk_assessment_service import assess_account_risk

# logger = logging.getLogger("brandshield.routes.verification")
# router = APIRouter(prefix="/verification", tags=["Multi-Platform Verification"])

# def serialize_doc(doc: dict) -> dict:
#     if not doc:
#         return doc
#     doc["id"] = str(doc.pop("_id"))
#     return doc

# @router.post("/verify-account", response_model=AccountVerificationResponse)
# async def verify_account(req: AccountVerificationRequest):
#     """
#     Unified multi-platform account verification endpoint.
#     Supports Instagram, Facebook, X (Twitter), and LinkedIn.
#     Returns official platform verification badge, BrandShield authenticity risk assessment,
#     identity consistency telemetry, and audit timestamps.
#     """
#     platform = req.platform.strip()
#     identifier = req.account_identifier.strip()
#     if not identifier:
#         raise HTTPException(status_code=400, detail="Account URL or identifier is required.")

#     db = get_db()
#     brand = None
#     official_assets = []

#     # Retrieve protected brand ground truth
#     if db is not None:
#         try:
#             if req.brand_id and ObjectId.is_valid(req.brand_id):
#                 brand = await db.brands.find_one({"_id": ObjectId(req.brand_id)})
#                 if brand:
#                     off_cursor = db.official_assets.find({"brand_id": req.brand_id})
#                     official_assets = await off_cursor.to_list(length=100)
            
#             if not brand and req.brand_name:
#                 brand = await db.brands.find_one({"name": {"$regex": f"^{re.escape(req.brand_name)}$", "$options": "i"}})
            
#             if not brand:
#                 all_brands = await db.brands.find({"is_archived": {"$ne": True}}).to_list(10)
#                 if all_brands:
#                     brand = all_brands[0]
#                     off_cursor = db.official_assets.find({"brand_id": str(brand["_id"])})
#                     official_assets = await off_cursor.to_list(length=100)
#         except Exception as e:
#             logger.warning(f"Error fetching brand context: {e}")

#     brand_name = (brand.get("name") if brand else "") or req.brand_name or "Protected Brand"
#     brand_id = str(brand["_id"]) if brand and "_id" in brand else req.brand_id

#     # Dispatch to platform service
#     try:
#         if platform.lower() in ("instagram", "ig"):
#             clean_user = sanitize_instagram_username(identifier)
#             ig_raw = await fetch_instagram_profile(clean_user, force_demo=not req.force_live_api)
#             is_verif = ig_raw.get("is_verified", False)
#             profile_dict = {
#                 "platform": "Instagram",
#                 "profile_url": f"https://www.instagram.com/{clean_user}/",
#                 "username": clean_user,
#                 "display_name": ig_raw.get("display_name") or clean_user.title(),
#                 "official_platform_verification": "Verified" if is_verif else "Not Verified",
#                 "verification_badge_type": "Meta Verified" if is_verif else "None",
#                 "avatar_url": ig_raw.get("profile_picture_url"),
#                 "bio": ig_raw.get("biography"),
#                 "followers_count": ig_raw.get("followers_count", 0),
#                 "following_count": ig_raw.get("following_count", 0),
#                 "media_or_posts_count": ig_raw.get("media_count", 0),
#                 "account_created_date": None,
#                 "website": ig_raw.get("website"),
#                 "page_category": "Instagram Profile",
#                 "data_source": "Meta Graph API (Instagram Graph)",
#                 "api_limitations_notice": None
#             }
#         elif platform.lower() in ("facebook", "fb"):
#             profile_dict = await fetch_facebook_profile(identifier, force_live_api=req.force_live_api)
#         elif platform.lower() in ("x", "twitter"):
#             profile_dict = await fetch_x_profile(identifier, force_live_api=req.force_live_api)
#         elif platform.lower() in ("linkedin", "li"):
#             profile_dict = await fetch_linkedin_profile(identifier, force_live_api=req.force_live_api)
#         else:
#             raise HTTPException(status_code=400, detail=f"Unsupported platform '{platform}'. Choose Instagram, Facebook, X, or LinkedIn.")
#     except ValueError as ve:
#         raise HTTPException(status_code=400, detail=str(ve))
#     except Exception as e:
#         logger.error(f"Error fetching profile from {platform}: {e}")
#         raise HTTPException(status_code=500, detail=f"Unable to retrieve profile from {platform}: {str(e)}")

#     # Execute explainable risk assessment
#     risk_data = assess_account_risk(
#         profile_data=profile_dict,
#         brand_data=brand,
#         official_assets=official_assets
#     )

#     # Derive identity consistency signals
#     exact_match = (profile_dict["username"].lower() == brand_name.lower().replace(" ", ""))
#     lookalike_detected = risk_data["risk_score"] >= 35.0
#     official_mismatch = (risk_data["risk_score"] > 0)

#     identity_indicators = {
#         "exact_name_match": exact_match,
#         "lookalike_detected": lookalike_detected,
#         "brand_keyword_presence": any(kw.lower() in (profile_dict.get("bio") or "").lower() for kw in (brand.get("brand_keywords", []) if brand else [])),
#         "official_registry_mismatch": official_mismatch,
#         "suspicious_contact_patterns": any(w in (profile_dict.get("bio") or "").lower() for w in ["whatsapp", "otp", "dm for help", "helpline"]),
#         "phishing_indicators": [f["detail"] for f in risk_data.get("evidence_findings", []) if f.get("category") == "DECEPTIVE_CUSTOMER_TARGETING"]
#     }

#     scan_id = str(uuid.uuid4())
#     now = datetime.utcnow()

#     response_payload = {
#         "scan_id": scan_id,
#         "platform": profile_dict["platform"],
#         "scanned_identifier": identifier,
#         "profile": profile_dict,
#         "identity_consistency": identity_indicators,
#         "risk": risk_data,
#         "brand_id": brand_id,
#         "brand_name": brand_name,
#         "timestamp": now
#     }

#     # Record scan history in MongoDB
#     if db is not None:
#         try:
#             history_doc = {
#                 "scan_id": scan_id,
#                 "brand_id": brand_id,
#                 "brand_name": brand_name,
#                 "platform": profile_dict["platform"],
#                 "username": profile_dict["username"],
#                 "display_name": profile_dict["display_name"],
#                 "profile_url": profile_dict["profile_url"],
#                 "official_platform_verification": profile_dict["official_platform_verification"],
#                 "risk_score": risk_data["risk_score"],
#                 "risk_category": risk_data["risk_category"],
#                 "primary_threat": risk_data["reasons"][0] if risk_data.get("reasons") else "Profile Analyzed",
#                 "data_source": profile_dict["data_source"],
#                 "scanned_at": now
#             }
#             await db.scan_history.insert_one(history_doc)
#         except Exception as e:
#             logger.warning(f"Could not record scan history: {e}")

#     return response_payload

# @router.get("/scan-history", response_model=List[ScanHistoryItem])
# async def get_scan_history(
#     brand_id: Optional[str] = None,
#     platform: Optional[str] = None,
#     risk_category: Optional[str] = None,
#     limit: int = Query(50, le=100)
# ):
#     """
#     Returns scan history for multi-platform verifications.
#     """
#     db = get_db()
#     if db is None:
#         return []

#     query = {}
#     if brand_id and ObjectId.is_valid(brand_id):
#         query["brand_id"] = brand_id
#     if platform and platform != "ALL":
#         query["platform"] = platform
#     if risk_category and risk_category != "ALL":
#         query["risk_category"] = risk_category

#     cursor = db.scan_history.find(query).sort("scanned_at", -1).limit(limit)
#     items = await cursor.to_list(length=limit)
#     return [serialize_doc(it) for it in items]

# @router.delete("/scan-history/{id}")
# async def delete_scan_history_item(id: str):
#     db = get_db()
#     if db is None:
#         return {"status": "ok"}
#     if ObjectId.is_valid(id):
#         await db.scan_history.delete_one({"_id": ObjectId(id)})
#     else:
#         await db.scan_history.delete_one({"scan_id": id})
#     return {"status": "success", "message": "Scan history record deleted"}



import uuid
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    readable_brand_filter,
    shared_demo_brand_filter,
)
from app.models.schemas import (
    AccountVerificationRequest,
    AccountVerificationResponse,
    ScanHistoryItem,
)
from app.services.auth_service import require_current_user
from app.services.facebook_service import fetch_facebook_profile
from app.services.x_service import fetch_x_profile
from app.services.linkedin_service import fetch_linkedin_profile
from app.services.instagram_service import (
    fetch_instagram_profile,
    sanitize_instagram_username,
)
from app.services.risk_assessment_service import assess_account_risk


logger = logging.getLogger("brandshield.routes.verification")
router = APIRouter(
    prefix="/verification",
    tags=["Multi-Platform Verification"],
)


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc

    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))

    return result


def get_user_id(current_user: dict) -> str:
    user_id = current_user.get("id")

    if not user_id and current_user.get("_id") is not None:
        user_id = str(current_user["_id"])

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Unable to identify the authenticated user.",
        )

    return str(user_id)


async def get_readable_brand(db, brand_id: str, user_id: str):
    """Return an owned brand or an explicitly shared demo brand."""
    if not brand_id or not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID.")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
        "is_archived": {"$ne": True},
    })

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found.")

    return brand


async def find_brand_for_verification(
    db,
    user_id: str,
    brand_id: Optional[str],
    brand_name: Optional[str],
):
    """Find only the current user's brand or a shared demo brand."""
    if brand_id:
        return await get_readable_brand(db, brand_id, user_id)

    if not brand_name or not brand_name.strip():
        return None

    safe_name = re.escape(brand_name.strip())
    name_filter = {
        "name": {
            "$regex": f"^{safe_name}$",
            "$options": "i",
        },
        "is_archived": {"$ne": True},
    }

    # Prefer a private brand owned by the authenticated user.
    owned_filter = {
        **name_filter,
        "owner_id": user_id,
    }
    brand = await db.brands.find_one(owned_filter)

    if brand:
        return brand

    # Otherwise, allow explicitly shared demo data only.
    return await db.brands.find_one({
        **name_filter,
        **shared_demo_brand_filter(),
    })


@router.post(
    "/verify-account",
    response_model=AccountVerificationResponse,
)
async def verify_account(
    req: AccountVerificationRequest,
    current_user: dict = Depends(require_current_user),
):
    """Verify a social profile and save history privately for this user."""
    user_id = get_user_id(current_user)

    platform = (req.platform or "").strip()
    identifier = (req.account_identifier or "").strip()

    if not identifier:
        raise HTTPException(
            status_code=400,
            detail="Account URL or identifier is required.",
        )

    normalized_platform = platform.lower()

    supported_platforms = {
        "instagram", "ig",
        "facebook", "fb",
        "x", "twitter",
        "linkedin", "li",
    }

    if normalized_platform not in supported_platforms:
        raise HTTPException(
            status_code=400,
            detail="Choose Instagram, Facebook, X, or LinkedIn.",
        )

    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )

    try:
        brand = await find_brand_for_verification(
            db=db,
            user_id=user_id,
            brand_id=req.brand_id,
            brand_name=req.brand_name,
        )

        official_assets = []
        if brand:
            official_assets = await db.official_assets.find(
                brand_child_filter(brand, user_id)
            ).to_list(length=100)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unable to retrieve verification brand context.")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve brand verification context.",
        )

    brand_name = (
        (brand.get("name") if brand else None)
        or req.brand_name
        or "Protected Brand"
    )
    brand_id = str(brand["_id"]) if brand else None

    try:
        if normalized_platform in ("instagram", "ig"):
            clean_user = sanitize_instagram_username(identifier)

            if not clean_user:
                raise HTTPException(
                    status_code=400,
                    detail="A valid Instagram username or URL is required.",
                )

            raw = await fetch_instagram_profile(
                clean_user,
                force_demo=not req.force_live_api,
            )

            verified = raw.get("is_verified", False)

            profile = {
                "platform": "Instagram",
                "profile_url": f"https://www.instagram.com/{clean_user}/",
                "username": clean_user,
                "display_name": raw.get("display_name") or clean_user.title(),
                "official_platform_verification": (
                    "Verified" if verified else "Not Verified"
                ),
                "verification_badge_type": (
                    "Meta Verified" if verified else "None"
                ),
                "avatar_url": raw.get("profile_picture_url"),
                "bio": raw.get("biography"),
                "followers_count": raw.get("followers_count", 0),
                "following_count": raw.get("following_count", 0),
                "media_or_posts_count": raw.get("media_count", 0),
                "account_created_date": None,
                "website": raw.get("website"),
                "page_category": "Instagram Profile",
                "data_source": "Meta Graph API (Instagram Graph)",
                "api_limitations_notice": None,
            }

        elif normalized_platform in ("facebook", "fb"):
            profile = await fetch_facebook_profile(
                identifier,
                force_live_api=req.force_live_api,
            )

        elif normalized_platform in ("x", "twitter"):
            profile = await fetch_x_profile(
                identifier,
                force_live_api=req.force_live_api,
            )

        else:
            profile = await fetch_linkedin_profile(
                identifier,
                force_live_api=req.force_live_api,
            )

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Profile retrieval failed for platform %s.", platform)
        raise HTTPException(
            status_code=502,
            detail=f"Unable to retrieve profile from {platform}.",
        )

    username = str(profile.get("username") or "").strip()
    if not username:
        raise HTTPException(
            status_code=502,
            detail="The platform service returned no account identifier.",
        )

    risk = assess_account_risk(
        profile_data=profile,
        brand_data=brand,
        official_assets=official_assets,
    )

    bio = (profile.get("bio") or "").lower()
    keywords = brand.get("brand_keywords", []) if brand else []

    identity_indicators = {
        "exact_name_match": (
            username.lower() == brand_name.lower().replace(" ", "")
        ),
        "lookalike_detected": risk["risk_score"] >= 35.0,
        "brand_keyword_presence": any(
            str(keyword).lower() in bio for keyword in keywords
        ),
        "official_registry_mismatch": risk["risk_score"] > 0,
        "suspicious_contact_patterns": any(
            phrase in bio
            for phrase in (
                "whatsapp",
                "otp",
                "dm for help",
                "helpline",
            )
        ),
        "phishing_indicators": [
            finding["detail"]
            for finding in risk.get("evidence_findings", [])
            if finding.get("category") == "DECEPTIVE_CUSTOMER_TARGETING"
            and finding.get("detail")
        ],
    }

    scan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    response_payload = {
        "scan_id": scan_id,
        "platform": profile.get("platform", platform),
        "scanned_identifier": identifier,
        "profile": profile,
        "identity_consistency": identity_indicators,
        "risk": risk,
        "brand_id": brand_id,
        "brand_name": brand_name,
        "timestamp": now,
    }

    history_doc = {
        "owner_id": user_id,
        "is_demo": False,
        "scan_id": scan_id,
        "brand_id": brand_id,
        "brand_name": brand_name,
        "platform": profile.get("platform", platform),
        "username": username,
        "display_name": profile.get("display_name", username),
        "profile_url": profile.get("profile_url"),
        "official_platform_verification": profile.get(
            "official_platform_verification"
        ),
        "risk_score": risk["risk_score"],
        "risk_category": risk["risk_category"],
        "primary_threat": (
            risk.get("reasons", ["Profile Analyzed"])[0]
            if risk.get("reasons")
            else "Profile Analyzed"
        ),
        "data_source": profile.get("data_source"),
        "scanned_at": now,
    }

    try:
        await db.scan_history.insert_one(history_doc)
    except Exception:
        logger.exception("Unable to save verification scan history.")
        raise HTTPException(
            status_code=503,
            detail="The verification result could not be saved. Please try again.",
        )

    return response_payload


@router.get(
    "/scan-history",
    response_model=List[ScanHistoryItem],
)
async def get_scan_history(
    brand_id: Optional[str] = None,
    platform: Optional[str] = None,
    risk_category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_current_user),
):
    """Return only the authenticated user's verification history."""
    user_id = get_user_id(current_user)

    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )

    query = {"owner_id": user_id}

    if brand_id:
        if not ObjectId.is_valid(brand_id):
            raise HTTPException(status_code=400, detail="Invalid brand ID.")

        # Verify the user may access the selected brand.
        await get_readable_brand(db, brand_id, user_id)
        query["brand_id"] = brand_id

    if platform and platform.upper() != "ALL":
        query["platform"] = platform

    if risk_category and risk_category.upper() != "ALL":
        query["risk_category"] = risk_category

    cursor = (
        db.scan_history.find(query)
        .sort("scanned_at", -1)
        .limit(limit)
    )
    documents = await cursor.to_list(length=limit)

    return [serialize_doc(doc) for doc in documents]


@router.delete("/scan-history/{id}")
async def delete_scan_history_item(
    id: str,
    current_user: dict = Depends(require_current_user),
):
    """Delete only a history record owned by the authenticated user."""
    user_id = get_user_id(current_user)

    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )

    query = {"owner_id": user_id}

    if ObjectId.is_valid(id):
        query["_id"] = ObjectId(id)
    else:
        query["scan_id"] = id

    result = await db.scan_history.delete_one(query)

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Scan history record not found.",
        )

    return {
        "status": "success",
        "message": "Scan history record deleted.",
    }
