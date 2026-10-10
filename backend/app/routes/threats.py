import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import ThreatResponse, ThreatUpdate

logger = logging.getLogger("brandshield.routes.threats")
router = APIRouter(prefix="/threats", tags=["Threat Center"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("", response_model=List[ThreatResponse])
async def list_all_threats(
    brand_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    db = get_db()
    query = {"is_official_safe": {"$ne": True}}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id
    if asset_type and asset_type != "ALL":
        query["asset_type"] = asset_type
    if risk_level and risk_level != "ALL":
        query["risk_level"] = risk_level
    if status and status != "ALL":
        query["status"] = status
    if search:
        query["$or"] = [
            {"account_or_app_name": {"$regex": search, "$options": "i"}},
            {"username_or_package": {"$regex": search, "$options": "i"}},
            {"url": {"$regex": search, "$options": "i"}},
            {"platform": {"$regex": search, "$options": "i"}},
            {"threat_type": {"$regex": search, "$options": "i"}}
        ]

    cursor = db.threats.find(query).sort("detected_time", -1)
    threats = await cursor.to_list(length=200)
    return [serialize_doc(t) for t in threats]

@router.get("/{id}", response_model=ThreatResponse)
async def get_threat_by_id(id: str):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")

    threat = await db.threats.find_one({"_id": ObjectId(id)})
    if not threat:
        raise HTTPException(status_code=404, detail="Threat record not found")
    return serialize_doc(threat)

@router.put("/{id}", response_model=ThreatResponse)
async def update_threat(id: str, update_in: ThreatUpdate):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")

    threat = await db.threats.find_one({"_id": ObjectId(id)})
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    update_fields = {"updated_at": datetime.utcnow()}
    for field in [
        "status", "analyst_assigned", "account_or_app_name",
        "username_or_package", "developer_name", "bio_or_description",
        "url", "platform", "risk_score", "risk_level", "customer_impact_score",
        "why_flagged", "recommended_action"
    ]:
        val = getattr(update_in, field, None)
        if val is not None:
            update_fields[field] = val

    # If note provided, push to notes array
    push_fields = {}
    if update_in.note:
        note_entry = {
            "author": update_in.analyst_assigned or "Analyst",
            "text": update_in.note,
            "created_at": datetime.utcnow().isoformat()
        }
        push_fields["notes"] = note_entry

    update_op = {"$set": update_fields}
    if push_fields:
        update_op["$push"] = push_fields

    updated = await db.threats.find_one_and_update(
        {"_id": ObjectId(id)},
        update_op,
        return_document=True
    )

    # If analyst marks as false positive / legitimate, we can also record feedback
    if update_in.status == "LEGITIMATE_FALSE_POSITIVE":
        feedback_doc = {
            "threat_id": id,
            "brand_id": threat.get("brand_id"),
            "feedback": "MARKED_LEGITIMATE",
            "marked_at": datetime.utcnow(),
            "notes": update_in.note or "Marked legitimate by analyst to tune false positive protection."
        }
        await db.analyst_feedback.insert_one(feedback_doc)

    return serialize_doc(updated)

@router.post("/bulk-delete")
async def bulk_delete_threats(payload: dict):
    db = get_db()
    ids = payload.get("ids", [])
    valid_obj_ids = []
    valid_id_strs = []
    for item_id in ids:
        if ObjectId.is_valid(item_id):
            valid_obj_ids.append(ObjectId(item_id))
            valid_id_strs.append(item_id)
            
    if not valid_obj_ids:
        return {"success": True, "deleted_count": 0, "deleted_ids": []}
        
    res = await db.threats.delete_many({"_id": {"$in": valid_obj_ids}})
    # Also delete matching alerts
    await db.alerts.delete_many({"threat_id": {"$in": valid_id_strs}})
    
    return {
        "success": True,
        "deleted_count": res.deleted_count,
        "deleted_ids": valid_id_strs,
        "message": f"Successfully deleted {res.deleted_count} threat records."
    }

@router.delete("/{id}")
async def delete_threat(id: str):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")
        
    res = await db.threats.delete_one({"_id": ObjectId(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Threat not found")
        
    # Clean up associated alerts
    await db.alerts.delete_many({"threat_id": id})
    return {"status": "success", "message": "Threat record deleted successfully", "id": id}

@router.post("/{id}/mark-reviewed")
async def mark_threat_reviewed(id: str):
    return await update_threat(id, ThreatUpdate(status="REVIEWED", note="Threat verified and marked as reviewed by analyst."))

@router.post("/{id}/resolve")
async def resolve_threat(id: str):
    return await update_threat(id, ThreatUpdate(status="RESOLVED", note="Threat resolved and mitigated."))

@router.post("/{id}/mark-legitimate")
async def mark_threat_legitimate(id: str):
    return await update_threat(id, ThreatUpdate(status="LEGITIMATE_FALSE_POSITIVE", note="Marked legitimate by analyst."))
