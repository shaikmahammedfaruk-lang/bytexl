import logging
import re
import uuid
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
    BrandProfileVerificationRequest,
    WebsiteAuthenticityRequest,
    ImageAuthenticityRequest,
    AuthenticityVerdictOverrideRequest,
    AuthenticityInvestigationRequest,
)
from app.services.auth_service import require_current_user
from app.services.authenticity_engine import (
    brand_authenticity_engine,
    KNOWN_OFFICIAL_RECORDS,
)
from app.utils.image_sim import compare_logos


logger = logging.getLogger("brandshield.routes.authenticity")
router = APIRouter(
    prefix="/authenticity",
    tags=["Brand Profile & Website Authenticity"],
)

# These are read-only demonstration alerts shared across accounts.
_demo_alerts = [
    {
        "id": "alt-sec-901",
        "title": "Critical Impersonation Alert: nike-support-login.com",
        "domain": "nike-support-login.com",
        "brand_name": "Nike",
        "severity": "CRITICAL",
        "risk_score": 93,
        "primary_threat": "Brand Impersonation / Credential Phishing",
        "details": (
            "High-fidelity login clone with cross-domain relay "
            "and fake 24/7 dispute desk."
        ),
        "created_at": datetime.utcnow().isoformat(),
        "is_read": False,
        "analyst_verdict": "Likely Impersonation",
        "is_demo": True,
    },
    {
        "id": "alt-sec-902",
        "title": "Lookalike Domain Detected: abcbank-help-portal.online",
        "domain": "abcbank-help-portal.online",
        "brand_name": "ABC Bank",
        "severity": "HIGH",
        "risk_score": 87,
        "primary_threat": "Financial Phishing / Credential Harvesting",
        "details": (
            "Lookalike banking support portal with OTP request cues."
        ),
        "created_at": datetime.utcnow().isoformat(),
        "is_read": False,
        "analyst_verdict": None,
        "is_demo": True,
    },
    {
        "id": "alt-sec-903",
        "title": "Typosquatting Domain: nik3.com",
        "domain": "nik3.com",
        "brand_name": "Nike",
        "severity": "MEDIUM",
        "risk_score": 58,
        "primary_threat": "Character Substitution Typosquatting",
        "details": (
            "Homoglyph/leetspeak replacement targeting mobile typo traffic."
        ),
        "created_at": datetime.utcnow().isoformat(),
        "is_read": True,
        "analyst_verdict": "Needs Review",
        "is_demo": True,
    },
]

# Overrides and alerts are scoped to the authenticated account.
# These are process-local caches, not durable database storage.
_user_overrides = {}
_user_alerts = {}


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc

    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))

    return result


def get_user_id(current_user: dict) -> str:
    user_id = current_user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Unable to identify the authenticated user.",
        )

    return str(user_id)


async def get_readable_brand(db, brand_id: str, user_id: str):
    """Allow access only to the user's brand or explicit shared demo brands."""
    if not brand_id or not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID.")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
    })

    if not brand or brand.get("is_archived") is True:
        raise HTTPException(status_code=404, detail="Brand not found.")

    is_owner = str(brand.get("owner_id", "")) == user_id
    is_demo = is_shared_demo_brand(brand)

    if not is_owner and not is_demo:
        raise HTTPException(
            status_code=404,
            detail="Brand not found or access denied.",
        )

    return brand


async def find_brand_for_analysis(
    db,
    user_id: str,
    brand_id: Optional[str] = None,
    brand_name: Optional[str] = None,
    candidate_url: Optional[str] = None,
):
    """Resolve only a brand the caller is allowed to read."""
    if brand_id:
        return await get_readable_brand(db, brand_id, user_id)

    if brand_name:
        brand = await db.brands.find_one(
            {
                "name": {
                    "$regex": f"^{re.escape(brand_name.strip())}$",
                    "$options": "i",
                },
                "owner_id": user_id,
                "is_archived": {"$ne": True},
            }
        )

        if brand:
            return brand

        # Shared demo brands can be used for analysis, but not modified.
        return await db.brands.find_one(
            {
                "name": {
                    "$regex": f"^{re.escape(brand_name.strip())}$",
                    "$options": "i",
                },
                **shared_demo_brand_filter(),
                "is_archived": {"$ne": True},
            }
        )

    if candidate_url:
        candidate_domain = brand_authenticity_engine.clean_domain(
            candidate_url
        )

        owned_brands = await db.brands.find(
            {
                "owner_id": user_id,
                "is_archived": {"$ne": True},
            }
        ).to_list(length=200)

        demo_brands = await db.brands.find(
            {
                **shared_demo_brand_filter(),
                "is_archived": {"$ne": True},
            }
        ).to_list(length=200)

        for brand in owned_brands + demo_brands:
            name_root = (
                (brand.get("name") or "")
                .lower()
                .replace(" ", "")
            )

            if name_root and name_root in candidate_domain.lower():
                return brand

    # Do not silently choose an unrelated user's brand.
    return None


@router.post("/verify-brand")
async def verify_brand_profile(
    req: BrandProfileVerificationRequest,
    current_user: dict = Depends(require_current_user),
):
    """Register or update the authenticated user's brand baseline."""
    user_id = get_user_id(current_user)
    db = get_db()

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )

    brand_name = (req.brand_name or "").strip()
    if not brand_name:
        raise HTTPException(
            status_code=400,
            detail="Brand name is required.",
        )

    clean_ig_user = None
    ig_url = None

    if req.instagram:
        clean_ig_user = (
            req.instagram.strip()
            .replace("@", "")
            .split("/")[-1]
            .split("?")[0]
        )

        if clean_ig_user:
            ig_url = (
                req.instagram
                if req.instagram.startswith("http")
                else f"https://instagram.com/{clean_ig_user}"
            )

    website = req.official_website or (
        f"https://{req.official_domain}"
        if req.official_domain
        else None
    )

    brand_dict = {
        "name": brand_name,
        "website": website,
        "logo_url": req.official_logo,
        "description": req.brand_description,
        "official_instagram_username": clean_ig_user,
        "official_instagram_url": ig_url,
        "official_bio": req.brand_description,
        "official_instagram_logo": req.official_logo,
        "official_email": req.official_contact_email,
        "social_profiles": {
            "instagram": req.instagram,
            "facebook": req.facebook,
            "twitter": req.twitter,
            "linkedin": req.linkedin,
            "youtube": req.youtube,
        },
        "official_social_links": [
            url
            for url in [
                ig_url,
                req.facebook,
                req.twitter,
                req.linkedin,
                req.youtube,
            ]
            if url
        ],
        "official_app_links": [
            url
            for url in [req.app_store_url, req.play_store_url]
            if url
        ],
        "app_store_url": req.app_store_url,
        "play_store_url": req.play_store_url,
    }

    now = datetime.utcnow()
    existing = None

    if req.brand_id:
        if not ObjectId.is_valid(req.brand_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid brand ID.",
            )

        existing = await db.brands.find_one(
            {
                "_id": ObjectId(req.brand_id),
                "owner_id": user_id,
            }
        )

        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Brand not found or access denied.",
            )

    if not existing:
        # Search only this user's brands. Never update another account's
        # brand merely because its name matches.
        existing = await db.brands.find_one(
            {
                "owner_id": user_id,
                "name": {
                    "$regex": f"^{re.escape(brand_name)}$",
                    "$options": "i",
                },
                "is_archived": {"$ne": True},
            }
        )

    if existing:
        brand_id_str = str(existing["_id"])

        update_fields = {
            key: value
            for key, value in brand_dict.items()
            if value is not None
        }
        update_fields["updated_at"] = now
        update_fields["is_archived"] = False

        await db.brands.update_one(
            {
                "_id": existing["_id"],
                "owner_id": user_id,
            },
            {"$set": update_fields},
        )

        saved_brand = await db.brands.find_one(
            {
                "_id": existing["_id"],
                "owner_id": user_id,
            }
        )

    else:
        new_doc = dict(brand_dict)
        new_doc.update(
            {
                "owner_id": user_id,
                "is_demo": False,
                "is_shared": False,
                "industry": "Commercial & Enterprise",
                "is_archived": False,
                "created_at": now,
                "updated_at": now,
                "brand_keywords": [brand_name.lower()],
                "brand_aliases": [brand_name],
            }
        )

        result = await db.brands.insert_one(new_doc)
        brand_id_str = str(result.inserted_id)
        saved_brand = await db.brands.find_one(
            {"_id": result.inserted_id, "owner_id": user_id}
        )

    if saved_brand is None:
        raise HTTPException(
            status_code=500,
            detail="Unable to save brand identity.",
        )

    # Only create official assets for the authenticated user's own brand.
    if ig_url:
        await db.official_assets.update_one(
            {"$and": [
                brand_child_filter(saved_brand, user_id),
                {"platform": "Instagram"},
            ]},
            {
                "$set": {
                    "brand_id": brand_id_str,
                    "owner_id": user_id,
                    "name": f"{brand_name} Official Instagram",
                    "asset_type": "social",
                    "platform": "Instagram",
                    "url": ig_url,
                    "identifier": f"@{clean_ig_user}",
                    "verification_status": "VERIFIED",
                    "updated_at": now,
                }
            },
            upsert=True,
        )

    if website:
        await db.official_assets.update_one(
            {"$and": [
                brand_child_filter(saved_brand, user_id),
                {"asset_type": "domain"},
            ]},
            {
                "$set": {
                    "brand_id": brand_id_str,
                    "owner_id": user_id,
                    "name": f"{brand_name} Official Domain",
                    "asset_type": "domain",
                    "platform": "Domain",
                    "url": website,
                    "identifier": (
                        brand_authenticity_engine.clean_domain(website)
                    ),
                    "verification_status": "VERIFIED",
                    "updated_at": now,
                }
            },
            upsert=True,
        )

    trust_report = brand_authenticity_engine.compute_brand_trust_score(
        saved_brand
    )

    return {
        "success": True,
        "message": (
            f"Brand identity baseline for '{brand_name}' "
            "successfully verified and registered."
        ),
        "brand_name": brand_name,
        "brand": serialize_doc(saved_brand),
        "trust_report": trust_report,
    }


@router.post("/analyze-website")
async def analyze_website(
    req: WebsiteAuthenticityRequest,
    current_user: dict = Depends(require_current_user),
):
    """Analyze a website without exposing another user's private brand data."""
    user_id = get_user_id(current_user)

    url = (req.url or "").strip()
    if not url:
        raise HTTPException(
            status_code=400,
            detail="Target website URL or domain is required.",
        )

    db = get_db()
    brand_doc = None

    if db is not None:
        try:
            brand_doc = await find_brand_for_analysis(
                db=db,
                user_id=user_id,
                brand_id=req.brand_id,
                brand_name=req.brand_name,
                candidate_url=url if not req.brand_id and not req.brand_name else None,
            )
        except HTTPException:
            raise
        except Exception:
            logger.exception("Error resolving brand for website analysis.")
            raise HTTPException(
                status_code=500,
                detail="Unable to resolve the selected brand.",
            )

    result = await brand_authenticity_engine.verify_website_async(
        url,
        brand_doc,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "error",
                "Unable to analyze website URL.",
            ),
        )

    candidate_domain = result.get("candidate_domain", "")
    override_key = (user_id, candidate_domain)

    if override_key in _user_overrides:
        result["analyst_override"] = _user_overrides[override_key]

    # Dynamically generated alerts are private to the current account.
    if result.get("risk", {}).get("score", 0) >= 80:
        alert_item = {
            "id": f"alt-auto-{uuid.uuid4().hex[:12]}",
            "owner_id": user_id,
            "title": f"Critical Impersonation Alert: {candidate_domain}",
            "domain": candidate_domain,
            "brand_name": result.get("brand_name", "Unknown Brand"),
            "severity": "CRITICAL",
            "risk_score": result["risk"]["score"],
            "primary_threat": result.get("primary_threat"),
            "details": (
                "High-risk website flagged by the authenticity engine."
            ),
            "created_at": datetime.utcnow().isoformat(),
            "is_read": False,
            "analyst_verdict": None,
            "is_demo": False,
        }

        user_alerts = _user_alerts.setdefault(user_id, [])
        if not any(
            item.get("domain") == candidate_domain
            for item in user_alerts
        ):
            user_alerts.insert(0, alert_item)

    return result


@router.post("/verify-image")
async def verify_image(
    req: ImageAuthenticityRequest,
    current_user: dict = Depends(require_current_user),
):
    """Compare a candidate image with an official logo."""
    cand_img = (
        req.candidate_image_url or req.candidate_logo_url or ""
    ).strip()

    off_img = (
        req.official_image_url or req.official_logo_url or ""
    ).strip()

    if not cand_img:
        raise HTTPException(
            status_code=400,
            detail="Candidate suspicious image/logo URL is required.",
        )

    if not off_img:
        raise HTTPException(
            status_code=400,
            detail="Official brand trademark logo URL is required.",
        )

    result = await compare_logos(
        official_logo_url=off_img,
        candidate_logo_url=cand_img,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "error",
                "Image likeness verification failed.",
            ),
        )

    return {
        "success": True,
        "candidate_image_url": result["candidate_image_url"],
        "official_image_url": result["official_image_url"],
        "similarity_pct": result["similarity_pct"],
        "similarity_score": result["similarity_score"],
        "match_status": result["match_status"],
        "risk_severity": result["risk_severity"],
        "hamming_distance": result["hamming_distance"],
        "dhash_candidate": result["dhash_candidate"],
        "dhash_official": result["dhash_official"],
        "is_identical": result["is_identical"],
        "is_direct_copy": result.get("is_direct_copy", False),
        "is_cropped_or_recolored": result.get(
            "is_cropped_or_recolored",
            False,
        ),
        "tags": result.get("tags", []),
        "thresholds": result.get("thresholds", {}),
        "verdict": result["match_status"],
        "explanation": result["explanation"],
    }


@router.post("/override-verdict")
async def override_verdict(
    req: AuthenticityVerdictOverrideRequest,
    current_user: dict = Depends(require_current_user),
):
    """Save a verdict override privately for the authenticated user."""
    user_id = get_user_id(current_user)
    domain = brand_authenticity_engine.clean_domain(
        req.candidate_domain
    )

    if not domain:
        raise HTTPException(
            status_code=400,
            detail="Candidate domain is required.",
        )

    override_data = {
        "verdict": req.override_verdict,
        "notes": req.notes or "Analyst manual review applied.",
        "analyst": req.analyst,
        "updated_at": datetime.utcnow().isoformat(),
    }

    _user_overrides[(user_id, domain)] = override_data

    for alert in _user_alerts.get(user_id, []):
        if alert.get("domain") == domain:
            alert["analyst_verdict"] = req.override_verdict

    return {
        "success": True,
        "message": (
            f"Verdict for '{domain}' overridden to "
            f"'{req.override_verdict}'."
        ),
        "domain": domain,
        "override": override_data,
    }


@router.get("/alerts")
async def get_authenticity_alerts(
    severity: Optional[str] = Query(
        "ALL",
        description="Filter by severity: ALL, CRITICAL, HIGH, MEDIUM",
    ),
    query: Optional[str] = Query(
        None,
        description="Search term for domain or brand",
    ),
    current_user: dict = Depends(require_current_user),
):
    """Return shared read-only demo alerts and this user's own alerts."""
    user_id = get_user_id(current_user)

    results = [
        dict(alert)
        for alert in _demo_alerts
    ]

    results.extend(
        dict(alert)
        for alert in _user_alerts.get(user_id, [])
    )

    if severity and severity.upper() != "ALL":
        results = [
            alert
            for alert in results
            if alert.get("severity", "").upper() == severity.upper()
        ]

    if query:
        search_text = query.lower()
        results = [
            alert
            for alert in results
            if search_text in alert.get("domain", "").lower()
            or search_text in alert.get("brand_name", "").lower()
            or search_text in alert.get("title", "").lower()
        ]