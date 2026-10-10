import re
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import AppScanRequest, ThreatResponse, ThreatUpdate
from app.services.detection_engine import run_multi_signal_detection
from app.services.correlation_engine import correlate_threats_into_campaigns

logger = logging.getLogger("brandshield.routes.apps")
router = APIRouter(prefix="/apps", tags=["App Monitoring"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

def detect_app_store(url: str) -> str:
    url_l = url.lower()
    if "apple.com" in url_l or "apps.apple.com" in url_l:
        return "Apple App Store"
    return "Google Play"

def extract_package_id(url: str) -> str:
    if "id=" in url:
        return url.split("id=")[-1].split("&")[0]
    elif "app/id" in url:
        return f"id{url.split('app/id')[-1].split('?')[0]}"
    return "com.unknown.impersonator"

@router.post("/scan")
async def scan_mobile_app(scan_req: AppScanRequest):
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

    store = scan_req.store or detect_app_store(scan_req.url)
    package_id = scan_req.package_id or extract_package_id(scan_req.url)
    app_name = scan_req.app_name or f"{brand.get('name')} Mobile Quick Support"
    developer = scan_req.developer or "Unknown Apps Ltd"
    publisher = scan_req.publisher or developer

    candidate_dict = {
        "url": scan_req.url,
        "store": store,
        "platform": store,
        "app_name": app_name,
        "developer": developer,
        "publisher": publisher,
        "package_id": package_id,
        "description": scan_req.description or f"Official mobile portal for {brand.get('name')} customers. Fast account access, enter PIN or OTP to claim cashback rewards.",
        "app_icon_url": scan_req.app_icon_url or "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=180",
        "rating": scan_req.rating or 2.3,
        "downloads": scan_req.downloads or "10,000+",
        "detected_time": datetime.utcnow()
    }

    # Run detection engine
    detection = await run_multi_signal_detection(
        brand=brand,
        official_assets=official_assets,
        candidate_data=candidate_dict,
        asset_type="app"
    )

    # If officially safe, return without creating malicious threat
    if detection["is_official_safe"]:
        return {
            "status": "safe",
            "message": "Application matches official verified registry. No threat created.",
            "detection": detection,
            "threat": None
        }

    # Check for existing duplicate record using unique package_id or canonical URL
    existing = await db.threats.find_one({
        "brand_id": brand_id,
        "asset_type": "app",
        "$or": [
            {"username_or_package": package_id},
            {"url": scan_req.url}
        ]
    })
    if existing:
        now = datetime.utcnow()
        await db.threats.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "account_or_app_name": app_name,
                    "developer_name": developer,
                    "risk_score": detection["risk_score"],
                    "risk_level": detection["risk_level"],
                    "customer_impact_score": detection["customer_impact_score"],
                    "confidence": detection["confidence"],
                    "why_flagged": detection["why_flagged"],
                    "recommended_action": detection["recommended_action"],
                    "detection_factors": detection["detection_factors"],
                    "updated_at": now
                }
            }
        )
        updated_existing = await db.threats.find_one({"_id": existing["_id"]})
        return {
            "status": "record_updated",
            "message": f"Application '{package_id}' already monitored. Refreshed detection signals.",
            "threat": serialize_doc(updated_existing)
        }

    now = datetime.utcnow()
    threat_doc = {
        "brand_id": brand_id,
        "title": f"Fake Application: {app_name} ({store})",
        "threat_type": detection["threat_type"],
        "asset_type": "app",
        "platform": store,
        "url": scan_req.url,
        "account_or_app_name": app_name,
        "username_or_package": package_id,
        "developer_name": developer,
        "profile_or_icon_url": candidate_dict["app_icon_url"],
        "bio_or_description": candidate_dict["description"],
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
        "analyst_assigned": "SecOps App Reviewer",
        "notes": [
            {
                "author": "App Store Crawler",
                "text": f"Scanned via Mobile App Monitor. Developer '{developer}' differs from verified brand entity.",
                "created_at": now.isoformat()
            }
        ]
    }

    res = await db.threats.insert_one(threat_doc)
    threat_doc["id"] = str(res.inserted_id)

    # Generate alert
    alert_doc = {
        "brand_id": brand_id,
        "threat_id": threat_doc["id"],
        "title": f"Unauthorized App Detected on {store}",
        "message": f"App '{app_name}' by '{developer}' detected impersonating {brand.get('name')}.",
        "severity": "CRITICAL" if detection["risk_score"] >= 71.0 else "HIGH",
        "category": "APP_SPOOFING",
        "is_read": False,
        "created_at": now
    }
    await db.alerts.insert_one(alert_doc)

    # Update threat campaign correlation
    await correlate_threats_into_campaigns(db, brand_id)

    return {
        "status": "threat_created",
        "message": f"Suspicious application detected ({detection['risk_level']}: {detection['risk_score']}/100)",
        "threat": serialize_doc(threat_doc)
    }

@router.get("/threats", response_model=List[ThreatResponse])
async def list_app_threats(
    brand_id: Optional[str] = None,
    store: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    db = get_db()
    query = {"asset_type": "app", "is_official_safe": {"$ne": True}}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id
    if store and store != "ALL":
        query["platform"] = store
    if risk_level and risk_level != "ALL":
        query["risk_level"] = risk_level
    if status and status != "ALL":
        query["status"] = status
    if search:
        query["$or"] = [
            {"account_or_app_name": {"$regex": search, "$options": "i"}},
            {"username_or_package": {"$regex": search, "$options": "i"}},
            {"developer_name": {"$regex": search, "$options": "i"}},
            {"why_flagged": {"$regex": search, "$options": "i"}}
        ]

    cursor = db.threats.find(query).sort("detected_time", -1)
    items = await cursor.to_list(length=100)
    return [serialize_doc(i) for i in items]

@router.put("/threats/{id}", response_model=ThreatResponse)
async def update_app_threat(id: str, update_in: ThreatUpdate):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")
        
    update_fields = {"updated_at": datetime.utcnow()}
    for field in [
        "account_or_app_name", "developer_name", "username_or_package",
        "bio_or_description", "platform", "url", "status", "analyst_assigned",
        "risk_score", "risk_level", "customer_impact_score", "why_flagged",
        "recommended_action"
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
        {"_id": ObjectId(id), "asset_type": "app"},
        update_op,
        return_document=True
    )
    if not res:
        raise HTTPException(status_code=404, detail="Mobile application threat record not found")
    return serialize_doc(res)

@router.delete("/threats/{id}")
async def delete_app_threat(id: str):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")
        
    res = await db.threats.delete_one({"_id": ObjectId(id), "asset_type": "app"})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mobile application threat record not found")
        
    await db.alerts.delete_many({"threat_id": id})
    return {"status": "success", "message": "Mobile application threat record deleted successfully", "id": id}
