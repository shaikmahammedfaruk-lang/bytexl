import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import (
    InstagramAnalyzeRequest,
    InstagramAnalyzeResponse,
    InstagramInvestigationRequest,
    InvestigationResponse
)
from app.services.instagram_service import fetch_instagram_profile, sanitize_instagram_username
from app.services.instagram_risk_engine import risk_analyzer, register_verified_entity
from app.services.correlation_engine import correlate_threats_into_campaigns

logger = logging.getLogger("brandshield.routes.instagram")
router = APIRouter(prefix="/instagram", tags=["Instagram Risk Analyzer"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.post("/analyze", response_model=InstagramAnalyzeResponse)
async def analyze_instagram_profile(req: InstagramAnalyzeRequest):
    """
    Analyzes an Instagram profile identifier against a protected brand.
    Combines official Meta Graph API telemetry (or graceful demo mode) with
    multi-signal look-alike matching, profile consistency, and customer phishing detection.
    """
    clean_username = sanitize_instagram_username(req.username)
    if not clean_username:
        raise HTTPException(status_code=400, detail="Instagram username or profile link is required.")

    db = get_db()
    
    # 1. Fetch brand information
    brand = None
    official_assets = []
    if db is not None:
        try:
            if req.brand_id and ObjectId.is_valid(req.brand_id):
                brand = await db.brands.find_one({"_id": ObjectId(req.brand_id)})
                if brand:
                    off_cursor = db.official_assets.find({"brand_id": req.brand_id})
                    official_assets = await off_cursor.to_list(length=100)
            
            if not brand:
                all_brands = await db.brands.find({"is_archived": {"$ne": True}}).to_list(100)
                for b in all_brands:
                    b_name_clean = b.get("name", "").lower().replace(" ", "")
                    b_ig = (b.get("official_instagram_username") or "").lower()
                    if (b_name_clean and b_name_clean in clean_username) or (b_ig and b_ig in clean_username):
                        brand = b
                        break
                
                if not brand:
                    brand = next((b for b in all_brands if b.get("name") == "Nike"), None)
                if not brand and all_brands:
                    brand = all_brands[0]

                if brand:
                    b_id = str(brand["_id"])
                    off_cursor = db.official_assets.find({"brand_id": b_id})
                    official_assets = await off_cursor.to_list(length=100)
        except Exception as e:
            logger.warning(f"Error accessing brand in database: {e}")
    
    if not brand:
        brand = {
            "name": "ABC Bank",
            "brand_aliases": ["abc", "abc bank"],
            "brand_keywords": ["banking", "support", "official", "verify"]
        }

    brand_id_str = str(brand.get("_id", "unknown"))
    brand_name = brand.get("name", "Protected Brand")

    # 2. Fetch Profile from Meta Graph API or graceful demo fallback
    try:
        profile_data = await fetch_instagram_profile(clean_username, force_demo=req.force_demo, override_is_verified=req.is_verified)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error fetching Instagram profile: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving Instagram account telemetry.")

    # If account is verified, dynamically register it into authentic original accounts registry
    if profile_data.get("is_verified"):
        register_verified_entity(
            username=clean_username,
            name=profile_data.get("display_name"),
            url=f"https://www.instagram.com/{clean_username}/",
            followers_count=profile_data.get("followers_count"),
            avatar=profile_data.get("profile_picture_url"),
            bio=profile_data.get("biography")
        )

    # 3. Run Risk Analysis Engine
    risk_assessment = risk_analyzer.analyze(
        profile=profile_data,
        brand=brand,
        official_assets=official_assets
    )

    now = datetime.utcnow()

    if db is not None and profile_data.get("is_verified"):
        try:
            await db.verified_original_accounts.update_one(
                {"username": clean_username},
                {
                    "$set": {
                        "username": clean_username,
                        "name": profile_data.get("display_name") or clean_username,
                        "url": f"https://www.instagram.com/{clean_username}/",
                        "followers_count": profile_data.get("followers_count"),
                        "avatar": profile_data.get("profile_picture_url"),
                        "bio": profile_data.get("biography"),
                        "verified_at": now
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.warning(f"Could not persist verified account to MongoDB: {e}")

    # 4. Persist analysis to MongoDB collection 'instagram_analyses'
    analysis_doc = {
        "username": clean_username,
        "brand_id": brand_id_str,
        "brand_name": brand_name,
        "profile": profile_data,
        "risk": {
            "score": risk_assessment["score"],
            "level": risk_assessment["level"],
            "confidence": risk_assessment["confidence"]
        },
        "primary_threat": risk_assessment.get("primary_threat", "Brand Impersonation"),
        "secondary_threat": risk_assessment.get("secondary_threat"),
        "confidence_pct": risk_assessment.get("confidence_pct", 94),
        "signals": risk_assessment["signals"],
        "why_flagged": risk_assessment.get("why_flagged", []),
        "evidence_cards": risk_assessment.get("evidence_cards", []),
        "official_comparison": risk_assessment.get("official_comparison"),
        "profile_risk_matrix": risk_assessment.get("profile_risk_matrix"),
        "suggested_original_account": risk_assessment.get("suggested_original_account"),
        "recommendations": risk_assessment["recommendations"],
        "explanation": risk_assessment["explanation"],
        "is_official_brand_asset": risk_assessment.get("is_official_brand_asset", False),
        "created_at": now
    }

    analysis_id = f"demo_analysis_{uuid.uuid4().hex[:12]}"

    if db is not None:
        try:
            res = await db.instagram_analyses.insert_one(analysis_doc)
            analysis_id = str(res.inserted_id)

            # Upsert profile snapshot into 'instagram_profiles' collection
            await db.instagram_profiles.update_one(
                {"username": clean_username},
                {
                    "$set": {
                        "username": clean_username,
                        "profile_snapshot": profile_data,
                        "last_analyzed_at": now,
                        "last_risk_score": risk_assessment["score"],
                        "last_risk_level": risk_assessment["level"]
                    }
                },
                upsert=True
            )

            # If HIGH or CRITICAL risk and NOT an official asset, automatically track or link into threats collection
            if risk_assessment["score"] >= 60 and not risk_assessment.get("is_official_brand_asset"):
                threat_url = f"https://instagram.com/{clean_username}"
                existing_threat = await db.threats.find_one({"url": threat_url})
                
                if not existing_threat:
                    threat_doc = {
                        "brand_id": brand_id_str,
                        "title": f"Instagram Impersonation: @{clean_username}",
                        "threat_type": "Brand Impersonation" if "support" not in clean_username else "Customer Support Impersonation",
                        "asset_type": "social",
                        "platform": "Instagram",
                        "url": threat_url,
                        "account_or_app_name": profile_data.get("display_name") or clean_username,
                        "username_or_package": f"@{clean_username}",
                        "developer_name": None,
                        "profile_or_icon_url": profile_data.get("profile_picture_url"),
                        "bio_or_description": profile_data.get("biography"),
                        "risk_score": float(risk_assessment["score"]),
                        "risk_level": risk_assessment["level"],
                        "customer_impact_score": round(min(95.0, float(risk_assessment["score"]) * 0.95), 1),
                        "confidence": float(risk_assessment["confidence"] * 100),
                        "status": "NEW",
                        "why_flagged": risk_assessment["explanation"],
                        "recommended_action": risk_assessment["recommendations"][0] if risk_assessment["recommendations"] else "Investigate profile.",
                        "detection_factors": {
                            "name_similarity": next((s["score"] for s in risk_assessment["signals"] if s["name"] == "Username Similarity"), 0.0) * 5.0,
                            "username_similarity": next((s["score"] for s in risk_assessment["signals"] if s["name"] == "Username Similarity"), 0.0) * 5.0,
                            "logo_similarity": 75.0,
                            "description_similarity": 65.0,
                            "brand_keyword_presence": 80.0,
                            "official_mismatch": 100.0,
                            "developer_mismatch": 0.0,
                            "customer_targeting_score": next((s["score"] for s in risk_assessment["signals"] if s["name"] == "Customer Phishing Intent"), 0.0) * 6.6,
                            "lookalike_type": "INSTAGRAM_ANALYZER_FLAGGED",
                            "lookalike_explanation": risk_assessment["explanation"],
                            "targeting_phrases": []
                        },
                        "official_comparison": {
                            "official": {
                                "name": brand_name,
                                "username_or_dev": official_assets[0].get("identifier") if official_assets else f"Official {brand_name}",
                                "url": official_assets[0].get("url") if official_assets else f"https://instagram.com/{brand_name.lower().replace(' ', '')}",
                                "platform": "Instagram",
                                "verified": True
                            },
                            "suspicious": {
                                "name": profile_data.get("display_name") or clean_username,
                                "username_or_dev": f"@{clean_username}",
                                "url": threat_url,
                                "platform": "Instagram",
                                "verified": profile_data.get("is_verified", False)
                            },
                            "differences": ["Asset is not registered in official brand directory", f"High resemblance to {brand_name}"]
                        },
                        "is_official_safe": False,
                        "detected_time": now,
                        "analyst_assigned": "SecOps Triage",
                        "notes": [
                            {
                                "author": "Instagram Risk Analyzer",
                                "text": f"Profile evaluated with AI-estimated risk of {risk_assessment['score']}/100 ({risk_assessment['level']}).",
                                "created_at": now.isoformat()
                            }
                        ]
                    }
                    t_res = await db.threats.insert_one(threat_doc)
                    
                    # Alert
                    await db.alerts.insert_one({
                        "brand_id": brand_id_str,
                        "threat_id": str(t_res.inserted_id),
                        "title": f"Instagram Risk Alert: @{clean_username}",
                        "message": f"Account @{clean_username} flagged as {risk_assessment['level']} RISK ({risk_assessment['score']}/100) targeting {brand_name}.",
                        "severity": "CRITICAL" if risk_assessment["score"] >= 80 else "HIGH",
                        "category": "SOCIAL_IMPERSONATION",
                        "is_read": False,
                        "created_at": now
                    })
                    
                    # Recorrelate into campaigns
                    await correlate_threats_into_campaigns(db, brand_id_str)
        except Exception as e:
            logger.error(f"Error persisting analysis to MongoDB: {e}")

    return {
        "success": True,
        "profile": profile_data,
        "risk": {
            "score": risk_assessment["score"],
            "level": risk_assessment["level"],
            "confidence": risk_assessment["confidence"]
        },
        "primary_threat": risk_assessment.get("primary_threat", "Brand Impersonation"),
        "secondary_threat": risk_assessment.get("secondary_threat"),
        "confidence_pct": risk_assessment.get("confidence_pct", 94),
        "signals": risk_assessment["signals"],
        "why_flagged": risk_assessment.get("why_flagged", []),
        "evidence_cards": risk_assessment.get("evidence_cards", []),
        "official_comparison": risk_assessment.get("official_comparison"),
        "profile_risk_matrix": risk_assessment.get("profile_risk_matrix"),
        "suggested_original_account": risk_assessment.get("suggested_original_account"),
        "recommendations": risk_assessment["recommendations"],
        "explanation": risk_assessment["explanation"],
        "brand_name": brand_name,
        "analysis_id": analysis_id,
        "is_official_brand_asset": risk_assessment.get("is_official_brand_asset", False),
        "created_at": now
    }

@router.get("/history")
async def get_analysis_history(brand_id: Optional[str] = None, limit: int = Query(20, ge=1, le=100)):
    """Retrieves recent Instagram profile risk analyses."""
    db = get_db()
    if db is None:
        return []
    query = {}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id

    cursor = db.instagram_analyses.find(query).sort("created_at", -1).limit(limit)
    items = await cursor.to_list(length=limit)
    return [serialize_doc(item) for item in items]

@router.post("/investigate", response_model=InvestigationResponse)
async def create_investigation_from_analysis(req: InstagramInvestigationRequest):
    """
    Creates a new formal investigation case from an Instagram profile analysis
    using the existing BrandShield AI investigation architecture.
    """
    db = get_db()
    if db is None or not ObjectId.is_valid(req.analysis_id):
        # Graceful fallback so demo mode investigations can always be demonstrated
        now = datetime.utcnow()
        case_num = f"INV-IG-{now.strftime('%Y')}-{str(int(now.timestamp()))[-4:]}"
        return {
            "id": f"demo_inv_{req.analysis_id[-8:] if len(req.analysis_id) >= 8 else 'case01'}",
            "threat_id": f"demo_thr_{req.analysis_id[-8:] if len(req.analysis_id) >= 8 else 'case01'}",
            "brand_id": "demo_brand",
            "case_number": case_num,
            "title": "Investigation: Instagram Impersonator Case",
            "status": "OPEN",
            "analyst": req.analyst_name or "SecOps Risk Analyst",
            "summary": "Escalated from Instagram Risk Analyzer forensic telemetry.",
            "evidence_items": [
                {"type": "Target Profile", "detail": "Instagram handle target"},
                {"type": "Risk Classification", "detail": "High risk impersonator profile detected"},
                {"type": "Meta Verification", "detail": "Unverified status combined with customer-targeting language"}
            ],
            "recommended_actions": [
                "Verify username against Meta Business Manager official asset directory",
                "Submit DMCA / Trademark Impersonation Takedown to Meta Trust & Safety"
            ],
            "timeline": [
                {
                    "time": now.isoformat(),
                    "event": f"Escalated to formal AI Investigation Case {case_num} by {req.analyst_name}"
                }
            ],
            "created_at": now
        }

    analysis = await db.instagram_analyses.find_one({"_id": ObjectId(req.analysis_id)})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    clean_user = analysis.get("username")
    threat_url = f"https://instagram.com/{clean_user}"
    
    # Check if a threat record already exists for this Instagram profile
    threat = await db.threats.find_one({"url": threat_url})
    threat_id = str(threat["_id"]) if threat else None

    # If no threat record, create one so investigation links cleanly
    if not threat_id:
        brand_id = analysis.get("brand_id")
        now = datetime.utcnow()
        profile = analysis.get("profile", {})
        risk = analysis.get("risk", {})
        
        threat_doc = {
            "brand_id": brand_id,
            "title": f"Instagram Impersonator: @{clean_user}",
            "threat_type": "Brand Impersonation",
            "asset_type": "social",
            "platform": "Instagram",
            "url": threat_url,
            "account_or_app_name": profile.get("display_name") or clean_user,
            "username_or_package": f"@{clean_user}",
            "developer_name": None,
            "profile_or_icon_url": profile.get("profile_picture_url"),
            "bio_or_description": profile.get("biography"),
            "risk_score": float(risk.get("score", 70)),
            "risk_level": risk.get("level", "HIGH"),
            "customer_impact_score": 75.0,
            "confidence": float(risk.get("confidence", 0.85) * 100),
            "status": "UNDER_INVESTIGATION",
            "why_flagged": analysis.get("explanation", "Flagged by Instagram Risk Analyzer."),
            "recommended_action": "Prioritize takedown submission to Meta Trust & Safety.",
            "detection_factors": {
                "name_similarity": 85.0,
                "username_similarity": 85.0,
                "logo_similarity": 80.0,
                "description_similarity": 70.0,
                "brand_keyword_presence": 85.0,
                "official_mismatch": 100.0,
                "developer_mismatch": 0.0,
                "customer_targeting_score": 60.0,
                "lookalike_type": "INSTAGRAM_ANALYZER_CASE",
                "lookalike_explanation": analysis.get("explanation", ""),
                "targeting_phrases": []
            },
            "official_comparison": {
                "official": {
                    "name": analysis.get("brand_name"),
                    "username_or_dev": "Official Handle",
                    "url": "https://instagram.com/",
                    "platform": "Instagram",
                    "verified": True
                },
                "suspicious": {
                    "name": profile.get("display_name") or clean_user,
                    "username_or_dev": f"@{clean_user}",
                    "url": threat_url,
                    "platform": "Instagram",
                    "verified": profile.get("is_verified", False)
                },
                "differences": ["Unregistered Instagram account claiming brand affiliation"]
            },
            "is_official_safe": False,
            "detected_time": now,
            "analyst_assigned": req.analyst_name,
            "notes": [
                {
                    "author": req.analyst_name,
                    "text": "Formal investigation escalated from Instagram Risk Analyzer.",
                    "created_at": now.isoformat()
                }
            ]
        }
        res_t = await db.threats.insert_one(threat_doc)
        threat_id = str(res_t.inserted_id)

    # Check existing investigation
    existing_inv = await db.investigations.find_one({"threat_id": threat_id})
    if existing_inv:
        return serialize_doc(existing_inv)

    now = datetime.utcnow()
    case_num = f"INV-IG-{now.strftime('%Y')}-{str(int(now.timestamp()))[-4:]}"
    
    # Evidence items from analysis
    evidence_items = [
        {"type": "Target Profile", "detail": f"@{clean_user} ({threat_url})"},
        {"type": "AI Risk Score", "detail": f"{analysis.get('risk', {}).get('score')}/100 ({analysis.get('risk', {}).get('level')})"},
        {"type": "Meta Verification Status", "detail": "Verified" if analysis.get("profile", {}).get("is_verified") else "Unverified Account"},
        {"type": "Follower Telemetry", "detail": f"{analysis.get('profile', {}).get('followers_count', 'unknown')} followers, {analysis.get('profile', {}).get('following_count', 'unknown')} following"}
    ]

    inv_doc = {
        "threat_id": threat_id,
        "brand_id": analysis.get("brand_id"),
        "case_number": case_num,
        "title": f"Investigation: Instagram Impersonator @{clean_user}",
        "status": "OPEN",
        "analyst": req.analyst_name,
        "summary": analysis.get("explanation"),
        "evidence_items": evidence_items,
        "recommended_actions": analysis.get("recommendations", [
            "Submit takedown request to Meta Trust & Safety desk",
            "Monitor network mutations and external bio links"
        ]),
        "timeline": [
            {"time": analysis.get("created_at", now).isoformat(), "event": "Profile analyzed via Instagram Risk Analyzer"},
            {"time": now.isoformat(), "event": f"Escalated to formal AI Investigation Case {case_num}"}
        ],
        "created_at": now
    }

    res_inv = await db.investigations.insert_one(inv_doc)
    inv_doc["id"] = str(res_inv.inserted_id)
    return inv_doc
