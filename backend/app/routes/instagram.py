
import uuid
import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    is_shared_demo_brand,
    readable_brand_filter,
    shared_demo_brand_filter,
)
from app.models.schemas import (
    InvestigationCreate,
    InstagramAnalyzeRequest,
    InstagramAnalyzeResponse,
    InstagramInvestigationRequest,
    InvestigationResponse,
)
from app.routes.investigations import create_investigation
from app.services.auth_service import require_current_user
from app.services.instagram_service import (
    fetch_instagram_profile,
    sanitize_instagram_username,
)
from app.services.instagram_risk_engine import (
    risk_analyzer,
    register_verified_entity,
)
from app.services.correlation_engine import correlate_threats_into_campaigns


logger = logging.getLogger("brandshield.routes.instagram")
router = APIRouter(prefix="/instagram", tags=["Instagram Risk Analyzer"])


def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB ObjectId to a JSON-compatible string."""
    if not doc:
        return doc

    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))

    return doc


def user_id_of(current_user: dict) -> str:
    """Get the authenticated user's stable ID."""
    user_id = current_user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Unable to identify the authenticated user.",
        )

    return str(user_id)


async def get_readable_brand(db, brand_id: str, user_id: str):
    """
    Return a brand only when it belongs to this user or is explicitly
    designated as shared, read-only demo data.
    """
    if not brand_id or not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID.")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
    })

    if not brand or brand.get("is_archived") is True:
        raise HTTPException(status_code=404, detail="Brand not found.")

    is_owner = str(brand.get("owner_id", "")) == user_id
    is_shared_demo = is_shared_demo_brand(brand)

    if not is_owner and not is_shared_demo:
        raise HTTPException(
            status_code=404,
            detail="Brand not found or access denied.",
        )

    return brand


def can_write_brand(brand: dict, user_id: str) -> bool:
    """Shared demo brands are readable but never writable."""
    return str(brand.get("owner_id", "")) == user_id


async def get_brand_for_analysis(db, requested_brand_id, user_id):
    """
    Select an accessible brand. Prefer the user's own brands.
    If none exist, allow analysis against an explicitly shared demo brand.
    """
    if requested_brand_id:
        return await get_readable_brand(
            db,
            str(requested_brand_id),
            user_id,
        )

    owned_brand = await db.brands.find_one(
        {
            "owner_id": user_id,
            "is_archived": {"$ne": True},
        },
        sort=[("created_at", -1)],
    )

    if owned_brand:
        return owned_brand

    demo_brand = await db.brands.find_one(
        {
            **shared_demo_brand_filter(),
            "is_archived": {"$ne": True},
        }
    )

    return demo_brand


@router.post("/analyze", response_model=InstagramAnalyzeResponse)
async def analyze_instagram_profile(
    req: InstagramAnalyzeRequest,
    current_user: dict = Depends(require_current_user),
):
    """Analyze an Instagram profile against an accessible protected brand."""
    user_id = user_id_of(current_user)

    clean_username = sanitize_instagram_username(req.username)
    if not clean_username:
        raise HTTPException(
            status_code=400,
            detail="Instagram username or profile link is required.",
        )

    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Please try again later.",
        )

    try:
        brand = await get_brand_for_analysis(
            db,
            req.brand_id,
            user_id,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Could not retrieve the selected brand.")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve the selected brand.",
        )

    if brand:
        brand_id_str = str(brand["_id"])
        brand_name = brand.get("name", "Protected Brand")
        official_assets = await db.official_assets.find(
            brand_child_filter(brand, user_id)
        ).to_list(length=100)
    else:
        # Preserve demo analysis when no brand has been configured.
        # This synthetic brand is not saved to the shared brands collection.
        brand = {
            "name": "ABC Bank",
            "brand_aliases": ["abc", "abc bank"],
            "brand_keywords": [
                "banking",
                "support",
                "official",
                "verify",
            ],
        }
        brand_id_str = "unknown"
        brand_name = brand["name"]
        official_assets = []

    try:
        profile_data = await fetch_instagram_profile(
            clean_username,
            force_demo=req.force_demo,
            override_is_verified=req.is_verified,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Error fetching Instagram profile.")
        raise HTTPException(
            status_code=502,
            detail="Error retrieving Instagram account telemetry.",
        )

    if profile_data.get("is_verified"):
        register_verified_entity(
            username=clean_username,
            name=profile_data.get("display_name"),
            url=f"https://www.instagram.com/{clean_username}/",
            followers_count=profile_data.get("followers_count"),
            avatar=profile_data.get("profile_picture_url"),
            bio=profile_data.get("biography"),
        )

        # This collection is a shared registry of public verified accounts,
        # not a store for private user analyses.
        try:
            await db.verified_original_accounts.update_one(
                {"username": clean_username},
                {
                    "$set": {
                        "username": clean_username,
                        "name": profile_data.get("display_name")
                        or clean_username,
                        "url": f"https://www.instagram.com/{clean_username}/",
                        "followers_count": profile_data.get(
                            "followers_count"
                        ),
                        "avatar": profile_data.get("profile_picture_url"),
                        "bio": profile_data.get("biography"),
                        "verified_at": datetime.utcnow(),
                    }
                },
                upsert=True,
            )
        except Exception:
            logger.warning(
                "Could not persist verified account to MongoDB.",
                exc_info=True,
            )

    risk_assessment = risk_analyzer.analyze(
        profile=profile_data,
        brand=brand,
        official_assets=official_assets,
    )

    now = datetime.utcnow()

    analysis_doc = {
        "owner_id": user_id,
        "is_demo": False,
        "username": clean_username,
        "brand_id": brand_id_str,
        "brand_name": brand_name,
        "profile": profile_data,
        "risk": {
            "score": risk_assessment["score"],
            "level": risk_assessment["level"],
            "confidence": risk_assessment["confidence"],
        },
        "primary_threat": risk_assessment.get(
            "primary_threat",
            "Brand Impersonation",
        ),
        "secondary_threat": risk_assessment.get("secondary_threat"),
        "confidence_pct": risk_assessment.get("confidence_pct", 94),
        "signals": risk_assessment["signals"],
        "why_flagged": risk_assessment.get("why_flagged", []),
        "evidence_cards": risk_assessment.get("evidence_cards", []),
        "official_comparison": risk_assessment.get("official_comparison"),
        "profile_risk_matrix": risk_assessment.get("profile_risk_matrix"),
        "suggested_original_account": risk_assessment.get(
            "suggested_original_account"
        ),
        "recommendations": risk_assessment["recommendations"],
        "explanation": risk_assessment["explanation"],
        "is_official_brand_asset": risk_assessment.get(
            "is_official_brand_asset",
            False,
        ),
        "created_at": now,
    }

    analysis_id = f"demo_analysis_{uuid.uuid4().hex[:12]}"

    try:
        result = await db.instagram_analyses.insert_one(analysis_doc)
        analysis_id = str(result.inserted_id)

        # Keep profile snapshots scoped to the logged-in user.
        await db.instagram_profiles.update_one(
            {
                "owner_id": user_id,
                "username": clean_username,
            },
            {
                "$set": {
                    "owner_id": user_id,
                    "username": clean_username,
                    "profile_snapshot": profile_data,
                    "last_analyzed_at": now,
                    "last_risk_score": risk_assessment["score"],
                    "last_risk_level": risk_assessment["level"],
                }
            },
            upsert=True,
        )

        # Only create or correlate threat records when the brand belongs
        # to this user. Shared demo brands remain read-only.
        writable_brand = bool(
            brand.get("_id") and can_write_brand(brand, user_id)
        )

        if (
            writable_brand
            and risk_assessment["score"] >= 60
            and not risk_assessment.get("is_official_brand_asset")
        ):
            threat_url = f"https://instagram.com/{clean_username}"

            existing_threat = await db.threats.find_one(
                {
                    "$and": [
                        brand_child_filter(brand, user_id),
                        {"url": threat_url},
                    ]
                }
            )

            if not existing_threat:
                username_signal = next(
                    (
                        signal.get("score", 0.0)
                        for signal in risk_assessment["signals"]
                        if signal.get("name") == "Username Similarity"
                    ),
                    0.0,
                )

                phishing_signal = next(
                    (
                        signal.get("score", 0.0)
                        for signal in risk_assessment["signals"]
                        if signal.get("name")
                        == "Customer Phishing Intent"
                    ),
                    0.0,
                )

                threat_doc = {
                    "owner_id": user_id,
                    "brand_id": brand_id_str,
                    "title": f"Instagram Impersonation: @{clean_username}",
                    "threat_type": (
                        "Customer Support Impersonation"
                        if "support" in clean_username
                        else "Brand Impersonation"
                    ),
                    "asset_type": "social",
                    "platform": "Instagram",
                    "url": threat_url,
                    "account_or_app_name": (
                        profile_data.get("display_name")
                        or clean_username
                    ),
                    "username_or_package": f"@{clean_username}",
                    "developer_name": None,
                    "profile_or_icon_url": profile_data.get(
                        "profile_picture_url"
                    ),
                    "bio_or_description": profile_data.get("biography"),
                    "risk_score": float(risk_assessment["score"]),
                    "risk_level": risk_assessment["level"],
                    "customer_impact_score": round(
                        min(
                            95.0,
                            float(risk_assessment["score"]) * 0.95,
                        ),
                        1,
                    ),
                    "confidence": float(
                        risk_assessment["confidence"] * 100
                    ),
                    "status": "NEW",
                    "why_flagged": risk_assessment["explanation"],
                    "recommended_action": (
                        risk_assessment["recommendations"][0]
                        if risk_assessment["recommendations"]
                        else "Investigate profile."
                    ),
                    "detection_factors": {
                        "name_similarity": username_signal * 5.0,
                        "username_similarity": username_signal * 5.0,
                        "logo_similarity": 75.0,
                        "description_similarity": 65.0,
                        "brand_keyword_presence": 80.0,
                        "official_mismatch": 100.0,
                        "developer_mismatch": 0.0,
                        "customer_targeting_score": phishing_signal * 6.6,
                        "lookalike_type": "INSTAGRAM_ANALYZER_FLAGGED",
                        "lookalike_explanation": risk_assessment[
                            "explanation"
                        ],
                        "targeting_phrases": [],
                    },
                    "official_comparison": {
                        "official": {
                            "name": brand_name,
                            "username_or_dev": (
                                official_assets[0].get("identifier")
                                if official_assets
                                else f"Official {brand_name}"
                            ),
                            "url": (
                                official_assets[0].get("url")
                                if official_assets
                                else (
                                    "https://instagram.com/"
                                    + brand_name.lower().replace(" ", "")
                                )
                            ),
                            "platform": "Instagram",
                            "verified": True,
                        },
                        "suspicious": {
                            "name": (
                                profile_data.get("display_name")
                                or clean_username
                            ),
                            "username_or_dev": f"@{clean_username}",
                            "url": threat_url,
                            "platform": "Instagram",
                            "verified": profile_data.get(
                                "is_verified",
                                False,
                            ),
                        },
                        "differences": [
                            "Asset is not registered in official brand directory",
                            f"High resemblance to {brand_name}",
                        ],
                    },
                    "is_official_safe": False,
                    "detected_time": now,
                    "analyst_assigned": "SecOps Triage",
                    "notes": [
                        {
                            "author": "Instagram Risk Analyzer",
                            "text": (
                                "Profile evaluated with AI-estimated risk "
                                f"of {risk_assessment['score']}/100 "
                                f"({risk_assessment['level']})."
                            ),
                            "created_at": now.isoformat(),
                        }
                    ],
                }

                threat_result = await db.threats.insert_one(threat_doc)
                threat_id = str(threat_result.inserted_id)

                await db.alerts.insert_one(
                    {
                        "owner_id": user_id,
                        "brand_id": brand_id_str,
                        "threat_id": threat_id,
                        "title": (
                            f"Instagram Risk Alert: @{clean_username}"
                        ),
                        "message": (
                            f"Account @{clean_username} flagged as "
                            f"{risk_assessment['level']} RISK "
                            f"({risk_assessment['score']}/100) "
                            f"targeting {brand_name}."
                        ),
                        "severity": (
                            "CRITICAL"
                            if risk_assessment["score"] >= 80
                            else "HIGH"
                        ),
                        "category": "SOCIAL_IMPERSONATION",
                        "is_read": False,
                        "created_at": now,
                    }
                )

                await correlate_threats_into_campaigns(
                    db,
                    brand_id_str,
                    user_id,
                )

    except Exception:
        # Preserve the analysis response even if a secondary write fails.
        # The analysis insert may already have succeeded, so log the issue.
        logger.exception("Error persisting Instagram analysis data.")

    return {
        "success": True,
        "profile": profile_data,
        "risk": {
            "score": risk_assessment["score"],
            "level": risk_assessment["level"],
            "confidence": risk_assessment["confidence"],
        },
        "primary_threat": risk_assessment.get(
            "primary_threat",
            "Brand Impersonation",
        ),
        "secondary_threat": risk_assessment.get("secondary_threat"),
        "confidence_pct": risk_assessment.get("confidence_pct", 94),
        "signals": risk_assessment["signals"],
        "why_flagged": risk_assessment.get("why_flagged", []),
        "evidence_cards": risk_assessment.get("evidence_cards", []),
        "official_comparison": risk_assessment.get("official_comparison"),
        "profile_risk_matrix": risk_assessment.get("profile_risk_matrix"),
        "suggested_original_account": risk_assessment.get(
            "suggested_original_account"
        ),
        "recommendations": risk_assessment["recommendations"],
        "explanation": risk_assessment["explanation"],
        "brand_name": brand_name,
        "analysis_id": analysis_id,
        "is_official_brand_asset": risk_assessment.get(
            "is_official_brand_asset",
            False,
        ),
        "created_at": now,
    }


@router.get("/history")
async def get_analysis_history(
    brand_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_current_user),
):
    """Return only analyses owned by the authenticated user."""
    user_id = user_id_of(current_user)
    db = get_db()

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )

    query = {"owner_id": user_id}

    if brand_id:
        if not ObjectId.is_valid(brand_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid brand ID.",
            )

        await get_readable_brand(db, brand_id, user_id)
        query["brand_id"] = brand_id

    cursor = (
        db.instagram_analyses.find(query)
        .sort("created_at", -1)
        .limit(limit)
    )

    items = await cursor.to_list(length=limit)
    return [serialize_doc(item) for item in items]


@router.post(
    "/investigate",
    response_model=InvestigationResponse,
)
async def create_investigation_from_analysis(
    req: InstagramInvestigationRequest,
    current_user: dict = Depends(require_current_user),
):
    """
    Create a new formal investigation case from an Instagram profile analysis
    using the existing BrandShield AI investigation architecture.
    """
    user_id = user_id_of(current_user)
    db = get_db()

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )

    if not ObjectId.is_valid(req.analysis_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid Instagram analysis ID.",
        )

    analysis = await db.instagram_analyses.find_one({
        "_id": ObjectId(req.analysis_id),
        "owner_id": user_id,
    })

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Instagram analysis not found.",
        )

    brand_id = str(analysis.get("brand_id") or "")
    brand = await get_readable_brand(db, brand_id, user_id)

    if not can_write_brand(brand, user_id):
        raise HTTPException(
            status_code=403,
            detail="Investigations require a brand you own.",
        )

    username = str(analysis.get("username") or "").strip()
    threat_url = f"https://instagram.com/{username}"
    threat = await db.threats.find_one({
        "$and": [
            brand_child_filter(brand, user_id),
            {
                "asset_type": "social",
                "platform": "Instagram",
                "url": threat_url,
            },
        ]
    })

    if not threat:
        raise HTTPException(
            status_code=409,
            detail=(
                "This analysis has no associated threat record to "
                "investigate. Re-analyze a high-risk account first."
            ),
        )

    return await create_investigation(
        InvestigationCreate(
            threat_id=str(threat["_id"]),
            analyst=req.analyst_name,
        ),
        current_user,
    )
   