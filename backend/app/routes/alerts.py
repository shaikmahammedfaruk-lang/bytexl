import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import AlertResponse

logger = logging.getLogger("brandshield.routes.alerts")
router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    if "message" not in doc or not doc["message"]:
        doc["message"] = doc.get("details") or doc.get("title") or "Security alert notification."
    if "category" not in doc or not doc["category"]:
        doc["category"] = "BRAND_IMPERSONATION"
    if "severity" not in doc or not doc["severity"]:
        doc["severity"] = "HIGH"
    if "brand_id" in doc and doc["brand_id"] is not None:
        doc["brand_id"] = str(doc["brand_id"])
    return doc

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    brand_id: Optional[str] = None,
    severity: Optional[str] = None,
    unread_only: bool = False
):
    db = get_db()
    query = {}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id
    if severity and severity != "ALL":
        query["severity"] = severity
    if unread_only:
        query["is_read"] = False

    cursor = db.alerts.find(query).sort("created_at", -1)
    alerts = await cursor.to_list(length=100)
    return [serialize_doc(a) for a in alerts]

@router.post("/{id}/read")
async def mark_alert_read(id: str):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid alert ID")

    res = await db.alerts.update_one({"_id": ObjectId(id)}, {"$set": {"is_read": True}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success", "message": "Alert marked as read"}

@router.post("/mark-all-read")
async def mark_all_alerts_read(brand_id: Optional[str] = None):
    db = get_db()
    query = {}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id

    res = await db.alerts.update_many(query, {"$set": {"is_read": True}})
    return {"status": "success", "updated_count": res.modified_count}
