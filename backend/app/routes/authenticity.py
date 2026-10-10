import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import (
    BrandProfileVerificationRequest,
    WebsiteAuthenticityRequest,
    ImageAuthenticityRequest,
    AuthenticityVerdictOverrideRequest,
    AuthenticityInvestigationRequest
)
from app.services.authenticity_engine import brand_authenticity_engine, KNOWN_OFFICIAL_RECORDS
from app.utils.image_sim import compare_logos

logger = logging.getLogger("brandshield.routes.authenticity")
router = APIRouter(prefix="/authenticity", tags=["Brand Profile & Website Authenticity"])

# Memory storage for overrides & standalone alerts when running without MongoDB or in sandbox
_analyst_overrides: Dict[str, Dict[str, Any]] = {}
_cached_alerts: List[Dict[str, Any]] = [
    {
        "id": "alt-sec-901",
        "title": "Critical Impersonation Alert: nike-support-login.com",
        "domain": "nike-support-login.com",
        "brand_name": "Nike",
        "severity": "CRITICAL",
        "risk_score": 93,
        "primary_threat": "Brand Impersonation / Credential Phishing",
        "details": "High-fidelity login clone with cross-domain relay and fake 24/7 dispute desk.",
        "created_at": datetime.utcnow().isoformat(),
        "is_read": False,
        "analyst_verdict": "Likely Impersonation"
    },
    {
        "id": "alt-sec-902",
        "title": "Lookalike Domain Detected: abcbank-help-portal.online",
        "domain": "abcbank-help-portal.online",
        "brand_name": "ABC Bank",
        "severity": "HIGH",
        "risk_score": 87,
        "primary_threat": "Financial Phishing / Credential Harvesting",
        "details": "Recent domain registration mimicking banking support portal with OTP request cues.",
        "created_at": datetime.utcnow().isoformat(),
        "is_read": False,
        "analyst_verdict": None
    },
    {
        "id": "alt-sec-903",
        "title": "Typosquatting Domain: nik3.com",
        "domain": "nik3.com",
        "brand_name": "Nike",
        "severity": "MEDIUM",
        "risk_score": 58,
        "primary_threat": "Character Substitution Typosquatting",
        "details": "Homoglyph/leetspeak replacement ('3' for 'e') targeting mobile typo traffic.",
        "created_at": datetime.utcnow().isoformat(),
        "is_read": True,
        "analyst_verdict": "Needs Review"
    }
]

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc

@router.post("/verify-brand")
async def verify_brand_profile(req: BrandProfileVerificationRequest):
    """
    Evaluates brand identity assets, registers ground truth baseline,
    and calculates Brand Digital Trust Score (0-100) with asset health matrix.
    """
    db = get_db()
    
    clean_ig_user = None
    ig_url = None
    if req.instagram:
        clean_ig_user = req.instagram.strip().replace("@", "").split("/")[-1].split("?")[0]
        ig_url = req.instagram if req.instagram.startswith("http") else f"https://instagram.com/{clean_ig_user}"

    website = req.official_website or (f"https://{req.official_domain}" if req.official_domain else None)
    
    brand_dict = {
        "name": req.brand_name.strip(),
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
            "youtube": req.youtube
        },
        "official_social_links": [u for u in [ig_url, req.facebook, req.twitter, req.linkedin, req.youtube] if u],
        "official_app_links": [u for u in [req.app_store_url, req.play_store_url] if u],
        "app_store_url": req.app_store_url,
        "play_store_url": req.play_store_url
    }

    saved_brand = None
    if db is not None:
        try:
            now = datetime.utcnow()
            existing = None
            if req.brand_id and ObjectId.is_valid(req.brand_id):
                existing = await db.brands.find_one({"_id": ObjectId(req.brand_id)})
            if not existing:
                existing = await db.brands.find_one({"name": {"$regex": f"^{req.brand_name.strip()}$", "$options": "i"}})

            if existing:
                b_id = str(existing["_id"])
                update_fields = {k: v for k, v in brand_dict.items() if v is not None}
                update_fields["updated_at"] = now
                update_fields["is_archived"] = False
                await db.brands.update_one({"_id": existing["_id"]}, {"$set": update_fields})
                saved_brand = await db.brands.find_one({"_id": existing["_id"]})
            else:
                new_doc = dict(brand_dict)
                new_doc["industry"] = "Commercial & Enterprise"
                new_doc["is_archived"] = False
                new_doc["created_at"] = now
                new_doc["updated_at"] = now
                new_doc["brand_keywords"] = [req.brand_name.lower()]
                new_doc["brand_aliases"] = [req.brand_name]
                res = await db.brands.insert_one(new_doc)
                b_id = str(res.inserted_id)
                saved_brand = await db.brands.find_one({"_id": res.inserted_id})

            # Also ensure official assets exist in db.official_assets for this brand
            if ig_url:
                await db.official_assets.update_one(
                    {"brand_id": b_id, "platform": "Instagram"},
                    {"$set": {
                        "brand_id": b_id,
                        "name": f"{req.brand_name} Official Instagram",
                        "asset_type": "social",
                        "platform": "Instagram",
                        "url": ig_url,
                        "identifier": f"@{clean_ig_user}",
                        "verification_status": "VERIFIED",
                        "updated_at": now
                    }},
                    upsert=True
                )
            if website:
                await db.official_assets.update_one(
                    {"brand_id": b_id, "asset_type": "domain"},
                    {"$set": {
                        "brand_id": b_id,
                        "name": f"{req.brand_name} Official Domain",
                        "asset_type": "domain",
                        "platform": "Domain",
                        "url": website,
                        "identifier": brand_authenticity_engine.clean_domain(website),
                        "verification_status": "VERIFIED",
                        "updated_at": now
                    }},
                    upsert=True
                )
        except Exception as e:
            logger.warning(f"Database brand registration skipped or errored: {e}")

    # Compute Digital Trust Score & Health Breakdown
    trust_report = brand_authenticity_engine.compute_brand_trust_score(saved_brand or brand_dict)

    serialized_brand = serialize_doc(saved_brand) if saved_brand else brand_dict

    return {
        "success": True,
        "message": f"Brand identity baseline for '{req.brand_name}' successfully verified & registered.",
        "brand_name": req.brand_name,
        "brand": serialized_brand,
        "trust_report": trust_report
    }

@router.post("/analyze-website")
async def analyze_website(req: WebsiteAuthenticityRequest):
    """
    Executes comprehensive 10-factor multi-signal verification of a candidate website URL.
    Returns explainable risk score (0-100), AI vision comparison, SSL analysis with identity disclaimer,
    redirect chain tracer, official website discovery, and Brand Trust Graph.
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Target website URL or domain is required.")

    db = get_db()
    brand_doc = None

    if db is not None:
        try:
            if req.brand_id and ObjectId.is_valid(req.brand_id):
                brand_doc = await db.brands.find_one({"_id": ObjectId(req.brand_id)})
            elif req.brand_name:
                brand_doc = await db.brands.find_one({"name": {"$regex": f"^{req.brand_name}$", "$options": "i"}})
            
            if not brand_doc:
                # Attempt to match from URL domain
                cand_clean = brand_authenticity_engine.clean_domain(url)
                all_brands = await db.brands.find({"is_archived": {"$ne": True}}).to_list(100)
                for b in all_brands:
                    b_root = (b.get("name") or "").lower().replace(" ", "")
                    if b_root and b_root in cand_clean:
                        brand_doc = b
                        break
        except Exception as e:
            logger.warning(f"Error resolving brand from DB: {e}")

    # Run 10-Factor AI Engine with live telemetry
    result = await brand_authenticity_engine.verify_website_async(url, brand_doc)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unable to analyze website URL."))

    # Check for analyst override
    cand_domain = result["candidate_domain"]
    if cand_domain in _analyst_overrides:
        override = _analyst_overrides[cand_domain]
        result["analyst_override"] = override

    # If critical risk, register immediate security alert
    if result["risk"]["score"] >= 80:
        alert_item = {
            "id": f"alt-auto-{int(datetime.utcnow().timestamp())}",
            "title": f"🚨 Critical Impersonation Alert: {cand_domain}",
            "domain": cand_domain,
            "brand_name": result["brand_name"],
            "severity": "CRITICAL",
            "risk_score": result["risk"]["score"],
            "primary_threat": result["primary_threat"],
            "details": f"AI Vision ({result['visual_ai_analysis']['overall_similarity_pct']}%) & domain lookalike engine flagged high-risk impersonation of {result['brand_name']}.",
            "created_at": datetime.utcnow().isoformat(),
            "is_read": False,
            "analyst_verdict": None
        }
        # Add to in-memory alerts if not already present
        if not any(a.get("domain") == cand_domain for a in _cached_alerts):
            _cached_alerts.insert(0, alert_item)

        # Also store into MongoDB alerts if DB available
        if db is not None:
            try:
                await db.alerts.insert_one({
                    "brand_id": str(brand_doc["_id"]) if brand_doc and "_id" in brand_doc else "default",
                    "severity": "CRITICAL",
                    "title": alert_item["title"],
                    "description": alert_item["details"],
                    "source": "AI Authenticity Engine",
                    "risk_score": result["risk"]["score"],
                    "is_read": False,
                    "created_at": datetime.utcnow()
                })
            except Exception as e:
                logger.warning(f"Could not persist alert to db: {e}")

    return result

@router.post("/verify-image")
async def verify_image(req: ImageAuthenticityRequest):
    """
    Performs perceptual hash (dHash) and logo likeness verification between
    the actual candidate digital asset and the official brand trademark.
    Validates that both URLs return valid image content.
    Does not use mock or demo fallbacks.
    """
    cand_img = (req.candidate_image_url or req.candidate_logo_url or "").strip()
    off_img = (req.official_image_url or req.official_logo_url or "").strip()
    
    if not cand_img:
        raise HTTPException(status_code=400, detail="Candidate Suspicious Image / Logo URL is required.")
    if not off_img:
        raise HTTPException(status_code=400, detail="Official Brand Trademark Logo URL is required.")

    sim_result = await compare_logos(official_logo_url=off_img, candidate_logo_url=cand_img)
    if not sim_result.get("success"):
        raise HTTPException(status_code=400, detail=sim_result.get("error", "Image likeness verification failed."))

    return {
        "success": True,
        "candidate_image_url": sim_result["candidate_image_url"],
        "official_image_url": sim_result["official_image_url"],
        "similarity_pct": sim_result["similarity_pct"],
        "similarity_score": sim_result["similarity_score"],
        "match_status": sim_result["match_status"],
        "risk_severity": sim_result["risk_severity"],
        "hamming_distance": sim_result["hamming_distance"],
        "dhash_candidate": sim_result["dhash_candidate"],
        "dhash_official": sim_result["dhash_official"],
        "is_identical": sim_result["is_identical"],
        "is_direct_copy": sim_result.get("is_direct_copy", False),
        "is_cropped_or_recolored": sim_result.get("is_cropped_or_recolored", False),
        "tags": sim_result.get("tags", []),
        "thresholds": sim_result.get("thresholds", {}),
        "verdict": sim_result["match_status"],
        "explanation": sim_result["explanation"]
    }

@router.post("/override-verdict")
async def override_verdict(req: AuthenticityVerdictOverrideRequest):
    """
    Allows a SecOps risk analyst to record a verdict override on a scanned website or domain.
    """
    domain = brand_authenticity_engine.clean_domain(req.candidate_domain)
    override_data = {
        "verdict": req.override_verdict,
        "notes": req.notes or "Analyst manual review applied.",
        "analyst": req.analyst,
        "updated_at": datetime.utcnow().isoformat()
    }
    _analyst_overrides[domain] = override_data

    # Update any cached alert with the override
    for a in _cached_alerts:
        if a.get("domain") == domain:
            a["analyst_verdict"] = req.override_verdict

    return {
        "success": True,
        "message": f"Verdict for '{domain}' overridden to '{req.override_verdict}'.",
        "domain": domain,
        "override": override_data
    }

@router.get("/alerts")
async def get_authenticity_alerts(
    severity: Optional[str] = Query("ALL", description="Filter by severity: ALL, CRITICAL, HIGH, MEDIUM"),
    query: Optional[str] = Query(None, description="Search term for domain or brand")
):
    """
    Returns security alerts generated by the Authenticity Verification System.
    """
    results = list(_cached_alerts)

    if severity and severity != "ALL":
        results = [a for a in results if a.get("severity", "").upper() == severity.upper()]

    if query:
        q = query.lower()
        results = [
            a for a in results
            if q in a.get("domain", "").lower()
            or q in a.get("brand_name", "").lower()
            or q in a.get("title", "").lower()
        ]

    return {
        "success": True,
        "total": len(results),
        "alerts": results
    }

@router.post("/investigate")
async def investigate_threat(req: AuthenticityInvestigationRequest):
    """
    Directly escalates an authenticity threat candidate to a formal incident investigation case.
    """
    domain = brand_authenticity_engine.clean_domain(req.candidate_domain)
    now = datetime.utcnow()
    case_num = f"INV-{now.strftime('%Y')}-{str(int(now.timestamp()))[-4:]}"

    db = get_db()
    if db is not None:
        try:
            await db.investigations.insert_one({
                "case_number": case_num,
                "threat_id": domain,
                "status": "OPEN",
                "assigned_to": req.analyst,
                "created_at": now,
                "updated_at": now,
                "evidence_package": [
                    {"type": "Infringing Domain", "detail": domain},
                    {"type": "Risk Score", "detail": f"{req.risk_score}/100"},
                    {"type": "Brand Target", "detail": req.brand_name}
                ],
                "recommended_actions": [
                    f"Issue domain registrar takedown request for {domain}",
                    "Submit URL to Google Safe Browsing and Microsoft SmartScreen",
                    "Add domain to corporate perimeter DNS blocklists"
                ]
            })
        except Exception as e:
            logger.warning(f"Could not persist investigation to db: {e}")

    return {
        "success": True,
        "case_number": case_num,
        "status": "OPEN",
        "assigned_to": req.analyst,
        "domain": domain,
        "brand_name": req.brand_name,
        "message": f"Formal SOC investigation {case_num} opened for '{domain}'."
    }

@router.get("/trust-score")
async def get_trust_score(brand_name: Optional[str] = Query("Nike")):
    """
    Retrieves the current Brand Digital Trust Score and asset matrix.
    """
    rec = brand_authenticity_engine.extract_brand_record({"name": brand_name})
    report = brand_authenticity_engine.compute_brand_trust_score(rec)
    return report
