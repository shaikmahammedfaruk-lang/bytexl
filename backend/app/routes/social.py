import re
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import SocialScanRequest, ThreatResponse, ThreatUpdate
from app.services.detection_engine import run_multi_signal_detection, clean_handle
from app.services.correlation_engine import correlate_threats_into_campaigns

logger = logging.getLogger("brandshield.routes.social")
router = APIRouter(prefix="/social", tags=["Social Monitoring"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

def detect_social_platform(url: str) -> str:
    url_l = url.lower()
    if "instagram.com" in url_l:
        return "Instagram"
    elif "facebook.com" in url_l or "fb.com" in url_l:
        return "Facebook"
    elif "twitter.com" in url_l or "x.com" in url_l:
        return "X"
    elif "linkedin.com" in url_l:
        return "LinkedIn"
    elif "youtube.com" in url_l or "youtu.be" in url_l:
        return "YouTube"
    elif "tiktok.com" in url_l:
        return "TikTok"
    return "Social Web"

@router.post("/scan")
async def scan_social_profile(scan_req: SocialScanRequest):
    db = get_db()
    brand_id = scan_req.brand_id
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = await db.brands.find_one({"_id": ObjectId(brand_id)})
    if not brand:
        raise HTTPException(status_code=404, detail="Target brand not found")

    # Fetch official assets for this brand
    off_cursor = db.official_assets.find({"brand_id": brand_id})
    official_assets = await off_cursor.to_list(length=100)

    # Derive missing fields from URL if not explicitly supplied
    platform = scan_req.platform or detect_social_platform(scan_req.url)
    username = scan_req.username or f"@{clean_handle(scan_req.url)}"
    display_name = scan_req.display_name or username.lstrip('@').replace('_', ' ').replace('-', ' ').title()
    
    candidate_dict = {
        "url": scan_req.url,
        "platform": platform,
        "username": username,
        "display_name": display_name,
        "bio": scan_req.bio or f"Official customer support and helpdesk channel for {brand.get('name')}. Send OTP or DM for fast resolution.",
        "profile_image_url": scan_req.profile_image_url or "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=180",
        "followers": scan_req.followers or 1420,
        "following": scan_req.following or 45,
        "detected_time": datetime.utcnow()
    }

    # Run detection engine
    detection = await run_multi_signal_detection(
        brand=brand,
        official_assets=official_assets,
        candidate_data=candidate_dict,
        asset_type="social"
    )

    # If officially safe, we return result without saving as malicious threat
    if detection["is_official_safe"]:
        return {
            "status": "safe",
            "message": "Asset matches official verified asset registry. No threat created.",
            "detection": detection,
            "threat": None
        }

    # Otherwise, persist to threats collection
    now = datetime.utcnow()
    threat_doc = {
        "brand_id": brand_id,
        "title": f"Social Impersonation: {display_name} ({platform})",
        "threat_type": detection["threat_type"],
        "asset_type": "social",
        "platform": platform,
        "url": scan_req.url,
        "account_or_app_name": display_name,
        "username_or_package": username,
        "developer_name": None,
        "profile_or_icon_url": candidate_dict["profile_image_url"],
        "bio_or_description": candidate_dict["bio"],
        "risk_score": detection["risk_score"],
        "risk_level": detection["risk_level"],
        "customer_impact_score": detection["customer_impact_score"],
        "confidence": detection["confidence"],
        "status": "NEW",
        "why_flagged": detection["why_flagged"],
        "recommended_action": detection["recommended_action"],
        "detection_factors": detection["detection_factors"],
        "official_comparison": detection["official_comparison"],
        "is_official_safe": False,
        "detected_time": now,
        "analyst_assigned": "SecOps Triage",
        "notes": [
            {
                "author": "Detection Engine",
                "text": f"Scanned via Social Media Monitor. Identified {detection['threat_type']} with risk score {detection['risk_score']}/100.",
                "created_at": now.isoformat()
            }
        ]
    }

    res = await db.threats.insert_one(threat_doc)
    threat_doc["id"] = str(res.inserted_id)

    # Create alert if risk is elevated
    if detection["risk_score"] >= 40.0:
        alert_doc = {
            "brand_id": brand_id,
            "threat_id": threat_doc["id"],
            "title": f"High Risk Social Impersonation ({platform})",
            "message": f"Suspicious account {username} detected mimicking {brand.get('name')}.",
            "severity": "CRITICAL" if detection["risk_score"] >= 71.0 else "HIGH",
            "category": "SOCIAL_IMPERSONATION",
            "is_read": False,
            "created_at": now
        }
        await db.alerts.insert_one(alert_doc)

    # Re-correlate into threat campaigns in background
    await correlate_threats_into_campaigns(db, brand_id)

    return {
        "status": "threat_created",
        "message": f"High-confidence threat flagged ({detection['risk_level']}: {detection['risk_score']}/100)",
        "threat": serialize_doc(threat_doc)
    }

@router.get("/threats", response_model=List[ThreatResponse])
async def list_social_threats(
    brand_id: Optional[str] = None,
    platform: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    db = get_db()
    query = {"asset_type": "social", "is_official_safe": {"$ne": True}}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id
    if platform and platform != "ALL":
        query["platform"] = platform
    if risk_level and risk_level != "ALL":
        query["risk_level"] = risk_level
    if status and status != "ALL":
        query["status"] = status
    if search:
        query["$or"] = [
            {"account_or_app_name": {"$regex": search, "$options": "i"}},
            {"username_or_package": {"$regex": search, "$options": "i"}},
            {"url": {"$regex": search, "$options": "i"}},
            {"why_flagged": {"$regex": search, "$options": "i"}}
        ]

    cursor = db.threats.find(query).sort("detected_time", -1)
    items = await cursor.to_list(length=100)
    return [serialize_doc(i) for i in items]

@router.put("/threats/{id}", response_model=ThreatResponse)
async def update_social_threat(id: str, update_in: ThreatUpdate):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")
        
    update_fields = {"updated_at": datetime.utcnow()}
    for field in [
        "account_or_app_name", "username_or_package", "bio_or_description",
        "platform", "url", "status", "analyst_assigned", "risk_score",
        "risk_level", "customer_impact_score", "why_flagged", "recommended_action"
    ]:
        val = getattr(update_in, field, None)
        if val is not None:
            update_fields[field] = val
            
    push_fields = {}
    if update_in.note:
        push_fields["notes"] = {
            "author": update_in.analyst_assigned or "Analyst",
            "text": update_in.note,
            "created_at": datetime.utcnow().isoformat()
        }
        
    update_op = {"$set": update_fields}
    if push_fields:
        update_op["$push"] = push_fields
        
    res = await db.threats.find_one_and_update(
        {"_id": ObjectId(id), "asset_type": "social"},
        update_op,
        return_document=True
    )
    if not res:
        raise HTTPException(status_code=404, detail="Social threat not found")
    return serialize_doc(res)

@router.delete("/threats/{id}")
async def delete_social_threat(id: str):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")
        
    res = await db.threats.delete_one({"_id": ObjectId(id), "asset_type": "social"})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Social threat not found")
        
    await db.alerts.delete_many({"threat_id": id})
    return {"status": "success", "message": "Social threat record deleted successfully", "id": id}
