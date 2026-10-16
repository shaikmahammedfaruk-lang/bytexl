import logging
import re
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    is_brand_child_visible,
    readable_brand_filter,
    readable_brand_children_filter,
)
from app.models.schemas import AppScanRequest, ThreatResponse, ThreatUpdate
from app.services.auth_service import require_current_user
from app.services.detection_engine import run_multi_signal_detection
from app.services.correlation_engine import correlate_threats_into_campaigns

logger = logging.getLogger("brandshield.routes.apps")

router = APIRouter(prefix="/apps", tags=["App Monitoring"])


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc

    result = dict(doc)
    result["id"] = str(result.pop("_id"))
    return result


def get_user_id(user: dict) -> str:
    user_id = user.get("id") or user.get("_id")
    return str(user_id) if user_id else ""


async def get_readable_brand(db, brand_id: str, user_id: str):
    """Allow access only to owned brands or explicitly shared demo brands."""
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
    })

    if not brand:
        raise HTTPException(status_code=404, detail="Target brand not found")

    return brand


async def get_writable_brand(db, brand_id: str, user_id: str):
    """Only a brand's owner can scan or change its threat records."""
    brand = await get_readable_brand(db, brand_id, user_id)

    if str(brand.get("owner_id", "")) != user_id:
        raise HTTPException(
            status_code=403,
            detail="Shared demo brands are read-only.",
        )

    return brand


async def get_authorized_app_threat(
    db,
    threat_id: str,
    user_id: str,
    writable: bool = False,
):
    if not ObjectId.is_valid(threat_id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")

    brands = await db.brands.find(
        readable_brand_filter(user_id),
        {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
    ).to_list(length=5000)
    if writable:
        brands = [
            brand for brand in brands
            if str(brand.get("owner_id", "")) == user_id
        ]

    threat_scope = readable_brand_children_filter(brands, user_id)
    threat = await db.threats.find_one({
        "$and": [
            {
                "_id": ObjectId(threat_id),
                "asset_type": "app",
            },
            threat_scope,
        ]
    })

    if not threat:
        raise HTTPException(
            status_code=404,
            detail="Mobile application threat record not found",
        )

    brand_id = threat.get("brand_id")

    if not brand_id:
        raise HTTPException(
            status_code=404,
            detail="Associated brand not found",
        )

    if writable:
        brand = await get_writable_brand(db, brand_id, user_id)
        if not is_brand_child_visible(brand, user_id, threat):
            raise HTTPException(
                status_code=404,
                detail="Mobile application threat not found",
            )
    else:
        brand = await get_readable_brand(db, brand_id, user_id)

        if not is_brand_child_visible(brand, user_id, threat):
            raise HTTPException(
                status_code=404,
                detail="Mobile application threat not found",
            )

    return threat


def detect_app_store(url: str) -> str:
    url_l = url.lower()

    if "apple.com" in url_l or "apps.apple.com" in url_l:
        return "Apple App Store"

    return "Google Play"


def extract_package_id(url: str) -> str:
    if "id=" in url:
        return url.split("id=")[-1].split("&")[0]

    if "app/id" in url:
        return f"id{url.split('app/id')[-1].split('?')[0]}"

    return "com.unknown.impersonator"


@router.post("/scan")
async def scan_mobile_app(
    scan_req: AppScanRequest,
    current_user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(current_user)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user session")

    # Scanning creates and updates records, so shared demo brands
    # and brands owned by other users cannot be scanned here.
    brand = await get_writable_brand(
        db,
        scan_req.brand_id,
        user_id,
    )

    brand_id = str(brand["_id"])

    official_assets = await db.official_assets.find(
        brand_child_filter(brand, user_id)
    ).to_list(length=100)

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
        "description": scan_req.description or (
            f"Official mobile portal for {brand.get('name')} customers. "
            "Fast account access, enter PIN or OTP to claim cashback rewards."
        ),
        "app_icon_url": (
            scan_req.app_icon_url
            or "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=180"
        ),
        "rating": scan_req.rating or 2.3,
        "downloads": scan_req.downloads or "10,000+",
        "detected_time": datetime.utcnow(),
    }

    detection = await run_multi_signal_detection(
        brand=brand,
        official_assets=official_assets,
        candidate_data=candidate_dict,
        asset_type="app",
    )

    if detection["is_official_safe"]:
        return {
            "status": "safe",
            "message": (
                "Application matches official verified registry. "
                "No threat created."
            ),
            "detection": detection,
            "threat": None,
        }

    existing = await db.threats.find_one({
        "$and": [
            brand_child_filter(brand, user_id),
            {
                "asset_type": "app",
                "$or": [
                    {"username_or_package": package_id},
                    {"url": scan_req.url},
                ],
            },
        ]
    })

    now = datetime.utcnow()

    if existing:
        await db.threats.update_one(
            {
                "_id": existing["_id"],
                **brand_child_filter(brand, user_id),
            },
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
                    "updated_at": now,
                }
            },
        )

        updated_existing = await db.threats.find_one({
            "_id": existing["_id"],
            **brand_child_filter(brand, user_id),
        })

        return {
            "status": "record_updated",
            "message": (
                f"Application '{package_id}' already monitored. "
                "Refreshed detection signals."
            ),
            "threat": serialize_doc(updated_existing),
        }

    threat_doc = {
        "brand_id": brand_id,
        "owner_id": user_id,
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
                "text": (
                    f"Scanned via Mobile App Monitor. Developer "
                    f"'{developer}' differs from verified brand entity."
                ),
                "created_at": now.isoformat(),
            }
        ],
    }

    result = await db.threats.insert_one(threat_doc)
    threat_doc["_id"] = result.inserted_id

    await db.alerts.insert_one({
        "brand_id": brand_id,
        "owner_id": user_id,
        "threat_id": str(result.inserted_id),
        "title": f"Unauthorized App Detected on {store}",
        "message": (
            f"App '{app_name}' by '{developer}' detected "
            f"impersonating {brand.get('name')}."
        ),
        "severity": (
            "CRITICAL" if detection["risk_score"] >= 71.0 else "HIGH"
        ),
        "category": "APP_SPOOFING",
        "is_read": False,
        "created_at": now,
    })

    await correlate_threats_into_campaigns(db, brand_id, user_id)

    return {
        "status": "threat_created",
        "message": (
            f"Suspicious application detected "
            f"({detection['risk_level']}: {detection['risk_score']}/100)"
        ),
        "threat": serialize_doc(threat_doc),
    }


@router.get("/threats", response_model=List[ThreatResponse])
async def list_app_threats(
    brand_id: Optional[str] = None,
    store: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(current_user)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user session")

    readable_brands = await db.brands.find(
        readable_brand_filter(user_id),
        {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
    ).to_list(length=5000)

    query = {
        **readable_brand_children_filter(readable_brands, user_id),
        "asset_type": "app",
        "is_official_safe": {"$ne": True},
    }

    if brand_id:
        if not ObjectId.is_valid(brand_id):
            raise HTTPException(status_code=400, detail="Invalid brand ID")

        if not any(str(item["_id"]) == brand_id for item in readable_brands):
            raise HTTPException(status_code=404, detail="Brand not found")

        query["brand_id"] = brand_id

    if store and store != "ALL":
        query["platform"] = store

    if risk_level and risk_level != "ALL":
        query["risk_level"] = risk_level

    if status and status != "ALL":
        query["status"] = status

    if search:
        safe_search = re.escape(search)
        query["$and"] = [{
            "$or": [
                {"account_or_app_name": {"$regex": safe_search, "$options": "i"}},
                {"username_or_package": {"$regex": safe_search, "$options": "i"}},
                {"developer_name": {"$regex": safe_search, "$options": "i"}},
                {"why_flagged": {"$regex": safe_search, "$options": "i"}},
            ]
        }]

    items = await db.threats.find(query).sort(
        "detected_time", -1
    ).to_list(length=100)

    return [serialize_doc(item) for item in items]


@router.put("/threats/{id}", response_model=ThreatResponse)
async def update_app_threat(
    id: str,
    update_in: ThreatUpdate,
    current_user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(current_user)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user session")

    threat = await get_authorized_app_threat(
        db,
        id,
        user_id,
        writable=True,
    )
    brand = await get_writable_brand(
        db,
        str(threat["brand_id"]),
        user_id,
    )
    child_filter = brand_child_filter(brand, user_id)

    update_fields = {"updated_at": datetime.utcnow()}

    allowed_fields = [
        "account_or_app_name",
        "developer_name",
        "username_or_package",
        "bio_or_description",
        "platform",
        "url",
        "status",
        "analyst_assigned",
        "risk_score",
        "risk_level",
        "customer_impact_score",
        "why_flagged",
        "recommended_action",
    ]

    for field in allowed_fields:
        value = getattr(update_in, field, None)
        if value is not None:
            update_fields[field] = value

    update_op = {"$set": update_fields}

    if update_in.note:
        update_op["$push"] = {
            "notes": {
                "author": update_in.analyst_assigned or "Analyst",
                "text": update_in.note,
                "created_at": datetime.utcnow().isoformat(),
            }
        }

    updated = await db.threats.find_one_and_update(
        {
            "_id": ObjectId(id),
            "asset_type": "app",
            **child_filter,
        },
        update_op,
        return_document=ReturnDocument.AFTER,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Mobile application threat record not found",
        )

    return serialize_doc(updated)


@router.delete("/threats/{id}")
async def delete_app_threat(
    id: str,
    current_user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(current_user)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user session")

    threat = await get_authorized_app_threat(
        db,
        id,
        user_id,
        writable=True,
    )
    brand = await get_writable_brand(
        db,
        str(threat["brand_id"]),
        user_id,
    )
    child_filter = brand_child_filter(brand, user_id)

    result = await db.threats.delete_one({
        "_id": ObjectId(id),
        "asset_type": "app",
        **child_filter,
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Mobile application threat record not found",
        )

    await db.alerts.delete_many({
        "threat_id": id,
        **child_filter,
    })

    return {
        "status": "success",
        "message": "Mobile application threat record deleted successfully",
        "id": id,
    }