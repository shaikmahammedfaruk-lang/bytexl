
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from bson import ObjectId

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    is_brand_child_visible,
    readable_brand_children_filter,
    readable_brand_filter as access_readable_brand_filter,
)
from app.services.auth_service import require_current_user
from app.models.schemas import ThreatResponse, ThreatUpdate

logger = logging.getLogger("brandshield.routes.threats")
router = APIRouter(prefix="/threats", tags=["Threat Center"])


# ---------------------------------------------------------
# AUTHENTICATION AND OWNERSHIP
# ---------------------------------------------------------

def get_user_id(user: dict) -> str:
    user_id = user.get("id") or user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    return str(user_id)


def readable_brand_filter(user_id: str) -> dict:
    return access_readable_brand_filter(user_id)


async def get_readable_brands(db, user_id: str) -> list:
    cursor = db.brands.find(
        readable_brand_filter(user_id),
        {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
    )
    return await cursor.to_list(length=5000)


async def get_authorized_threat(
    db,
    threat_id: str,
    user_id: str,
    writable: bool = False,
) -> dict:
    if not ObjectId.is_valid(threat_id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")

    visible_brands = await get_readable_brands(db, user_id)
    if writable:
        visible_brands = [
            brand for brand in visible_brands
            if str(brand.get("owner_id", "")) == user_id
        ]

    threat_scope = readable_brand_children_filter(
        visible_brands,
        user_id,
    )
    threat = await db.threats.find_one({
        "$and": [
            {"_id": ObjectId(threat_id)},
            threat_scope,
        ]
    })
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    brand_id = str(threat.get("brand_id", ""))

    if not ObjectId.is_valid(brand_id):
        # Legacy threats without a valid associated brand are not exposed.
        raise HTTPException(status_code=404, detail="Threat not found")

    brand_query = {
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
    }
    brand = await db.brands.find_one(brand_query)

    if not brand:
        raise HTTPException(status_code=404, detail="Threat not found")

    if not is_brand_child_visible(brand, user_id, threat):
        raise HTTPException(status_code=404, detail="Threat not found")

    if writable:
        if str(brand.get("owner_id", "")) != user_id:
            raise HTTPException(
                status_code=403,
                detail="Shared demo threats are read-only",
            )

    return threat


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


# ---------------------------------------------------------
# LIST THREATS
# ---------------------------------------------------------

@router.get("", response_model=List[ThreatResponse])
async def list_all_threats(
    brand_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    visible_brands = await get_readable_brands(db, user_id)
    visible_brand_ids = [str(brand["_id"]) for brand in visible_brands]

    query = {
        **readable_brand_children_filter(visible_brands, user_id),
        "is_official_safe": {"$ne": True},
    }

    if brand_id:
        if not ObjectId.is_valid(brand_id):
            raise HTTPException(status_code=400, detail="Invalid brand ID")
        if brand_id not in visible_brand_ids:
            raise HTTPException(status_code=404, detail="Brand not found")
        query["brand_id"] = brand_id

    if asset_type and asset_type != "ALL":
        query["asset_type"] = asset_type

    if risk_level and risk_level != "ALL":
        query["risk_level"] = risk_level

    if status and status != "ALL":
        query["status"] = status

    if search:
        query["$and"] = [
            {
                "$or": [
                    {
                        "account_or_app_name": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "username_or_package": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {"url": {"$regex": search, "$options": "i"}},
                    {"platform": {"$regex": search, "$options": "i"}},
                    {"threat_type": {"$regex": search, "$options": "i"}},
                ]
            }
        ]

    cursor = db.threats.find(query).sort("detected_time", -1)
    threats = await cursor.to_list(length=200)
    return [serialize_doc(threat) for threat in threats]


# ---------------------------------------------------------
# GET ONE THREAT
# ---------------------------------------------------------

@router.get("/{id}", response_model=ThreatResponse)
async def get_threat_by_id(
    id: str,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    threat = await get_authorized_threat(db, id, get_user_id(user))
    return serialize_doc(threat)


# ---------------------------------------------------------
# UPDATE THREAT
# ---------------------------------------------------------

async def update_threat_for_user(
    id: str,
    update_in: ThreatUpdate,
    user_id: str,
):
    db = get_db()
    threat = await get_authorized_threat(
        db, id, user_id, writable=True
    )

    update_fields = {"updated_at": datetime.utcnow()}

    allowed_fields = [
        "status",
        "analyst_assigned",
        "account_or_app_name",
        "username_or_package",
        "developer_name",
        "bio_or_description",
        "url",
        "platform",
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
        note_entry = {
            "author": update_in.analyst_assigned or "Analyst",
            "text": update_in.note,
            "created_at": datetime.utcnow().isoformat(),
        }
        update_op["$push"] = {"notes": note_entry}

    updated = await db.threats.find_one_and_update(
        {
            "_id": ObjectId(id),
            "brand_id": threat.get("brand_id"),
            "$or": [
                {"owner_id": user_id},
                {"owner_id": {"$exists": False}},
            ],
        },
        update_op,
        return_document=True,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Threat not found")

    if update_in.status == "LEGITIMATE_FALSE_POSITIVE":
        await db.analyst_feedback.insert_one({
            "threat_id": id,
            "brand_id": threat.get("brand_id"),
            "owner_id": user_id,
            "feedback": "MARKED_LEGITIMATE",
            "marked_at": datetime.utcnow(),
            "notes": update_in.note
            or "Marked legitimate by analyst.",
        })

    return serialize_doc(updated)


@router.put("/{id}", response_model=ThreatResponse)
async def update_threat(
    id: str,
    update_in: ThreatUpdate,
    user: dict = Depends(require_current_user),
):
    return await update_threat_for_user(
        id,
        update_in,
        get_user_id(user),
    )


# ---------------------------------------------------------
# BULK DELETE
# ---------------------------------------------------------

@router.post("/bulk-delete")
async def bulk_delete_threats(
    payload: dict,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    ids = payload.get("ids", [])
    if not isinstance(ids, list):
        raise HTTPException(
            status_code=400,
            detail="ids must be a list",
        )

    # Validate ownership of every requested record before deleting.
    authorized_threats = []
    for item_id in ids:
        if not isinstance(item_id, str) or not ObjectId.is_valid(item_id):
            continue

        threat = await get_authorized_threat(
            db,
            item_id,
            user_id,
            writable=True,
        )
        authorized_threats.append(threat)

    if not authorized_threats:
        return {
            "success": True,
            "deleted_count": 0,
            "deleted_ids": [],
        }

    authorized_ids = [str(threat["_id"]) for threat in authorized_threats]
    delete_scopes = [
        {
            "_id": threat["_id"],
            "brand_id": threat.get("brand_id"),
            "$or": [
                {"owner_id": user_id},
                {"owner_id": {"$exists": False}},
            ],
        }
        for threat in authorized_threats
    ]

    result = await db.threats.delete_many({
        "$or": delete_scopes,
    })

    await db.alerts.delete_many({
        "threat_id": {"$in": authorized_ids},
        "brand_id": {
            "$in": list({
                str(threat.get("brand_id"))
                for threat in authorized_threats
                if threat.get("brand_id")
            })
        },
        "$or": [
            {"owner_id": user_id},
            {"owner_id": {"$exists": False}},
        ],
    })

    return {
        "success": True,
        "deleted_count": result.deleted_count,
        "deleted_ids": authorized_ids,
        "message": f"Deleted {result.deleted_count} threat records.",
    }


# ---------------------------------------------------------
# DELETE ONE THREAT
# ---------------------------------------------------------

@router.delete("/{id}")
async def delete_threat(
    id: str,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    threat = await get_authorized_threat(
        db, id, user_id, writable=True
    )

    result = await db.threats.delete_one({
        "_id": ObjectId(id),
        "brand_id": threat.get("brand_id"),
        "$or": [
            {"owner_id": user_id},
            {"owner_id": {"$exists": False}},
        ],
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Threat not found")

    await db.alerts.delete_many({
        "threat_id": id,
        "$or": [
            {"owner_id": user_id},
            {"owner_id": {"$exists": False}},
        ],
    })

    return {
        "status": "success",
        "message": "Threat record deleted successfully",
        "id": id,
    }


# ---------------------------------------------------------
# THREAT ACTIONS
# ---------------------------------------------------------

@router.post("/{id}/mark-reviewed")
async def mark_threat_reviewed(
    id: str,
    user: dict = Depends(require_current_user),
):
    update = ThreatUpdate(
        status="REVIEWED",
        note="Threat verified and marked as reviewed by analyst.",
    )
    return await update_threat_for_user(
        id, update, get_user_id(user)
    )


@router.post("/{id}/resolve")
async def resolve_threat(
    id: str,
    user: dict = Depends(require_current_user),
):
    update = ThreatUpdate(
        status="RESOLVED",
        note="Threat resolved and mitigated.",
    )
    return await update_threat_for_user(
        id, update, get_user_id(user)
    )


@router.post("/{id}/mark-legitimate")
async def mark_threat_legitimate(
    id: str,
    user: dict = Depends(require_current_user),
):
    update = ThreatUpdate(
        status="LEGITIMATE_FALSE_POSITIVE",
        note="Marked legitimate by analyst.",
    )
    return await update_threat_for_user(
        id, update, get_user_id(user)
    )