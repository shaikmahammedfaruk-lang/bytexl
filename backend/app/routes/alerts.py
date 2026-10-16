# import logging
# from typing import List, Optional
# from fastapi import APIRouter, HTTPException, Query
# from bson import ObjectId
# from app.database import get_db
# from app.models.schemas import AlertResponse

# logger = logging.getLogger("brandshield.routes.alerts")
# router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])

# def serialize_doc(doc: dict) -> dict:
#     if not doc:
#         return doc
#     doc["id"] = str(doc.pop("_id"))
#     if "message" not in doc or not doc["message"]:
#         doc["message"] = doc.get("details") or doc.get("title") or "Security alert notification."
#     if "category" not in doc or not doc["category"]:
#         doc["category"] = "BRAND_IMPERSONATION"
#     if "severity" not in doc or not doc["severity"]:
#         doc["severity"] = "HIGH"
#     if "brand_id" in doc and doc["brand_id"] is not None:
#         doc["brand_id"] = str(doc["brand_id"])
#     return doc

# @router.get("", response_model=List[AlertResponse])
# async def list_alerts(
#     brand_id: Optional[str] = None,
#     severity: Optional[str] = None,
#     unread_only: bool = False
# ):
#     db = get_db()
#     query = {}
#     if brand_id and ObjectId.is_valid(brand_id):
#         query["brand_id"] = brand_id
#     if severity and severity != "ALL":
#         query["severity"] = severity
#     if unread_only:
#         query["is_read"] = False

#     cursor = db.alerts.find(query).sort("created_at", -1)
#     alerts = await cursor.to_list(length=100)
#     return [serialize_doc(a) for a in alerts]

# @router.post("/{id}/read")
# async def mark_alert_read(id: str):
#     db = get_db()
#     if not ObjectId.is_valid(id):
#         raise HTTPException(status_code=400, detail="Invalid alert ID")

#     res = await db.alerts.update_one({"_id": ObjectId(id)}, {"$set": {"is_read": True}})
#     if res.matched_count == 0:
#         raise HTTPException(status_code=404, detail="Alert not found")
#     return {"status": "success", "message": "Alert marked as read"}

# @router.post("/mark-all-read")
# async def mark_all_alerts_read(brand_id: Optional[str] = None):
#     db = get_db()
#     query = {}
#     if brand_id and ObjectId.is_valid(brand_id):
#         query["brand_id"] = brand_id

#     res = await db.alerts.update_many(query, {"$set": {"is_read": True}})
#     return {"status": "success", "updated_count": res.modified_count}



import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    is_brand_child_visible,
    readable_brand_children_filter,
    readable_brand_filter as access_readable_brand_filter,
)
from app.services.auth_service import require_current_user
from app.models.schemas import AlertResponse

logger = logging.getLogger("brandshield.routes.alerts")
router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])


# ---------------------------------------------------------
# AUTHENTICATION AND BRAND ACCESS
# ---------------------------------------------------------

def get_user_id(user: dict) -> str:
    user_id = user.get("id") or user.get("_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    return str(user_id)


def readable_brand_filter(user_id: str) -> dict:
    return access_readable_brand_filter(user_id)


async def get_visible_brands(db, user_id: str) -> list:
    cursor = db.brands.find(
        readable_brand_filter(user_id),
        {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
    )
    return await cursor.to_list(length=5000)


async def get_alert_brand(db, brand_id: str, user_id: str) -> dict:
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=404, detail="Alert not found")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
    })

    if not brand:
        raise HTTPException(status_code=404, detail="Alert not found")

    return brand


async def get_writable_alert(db, alert_id: str, user_id: str) -> dict:
    if not ObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="Invalid alert ID")

    alert = await db.alerts.find_one({"_id": ObjectId(alert_id)})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    brand_id = str(alert.get("brand_id", ""))
    brand = await get_alert_brand(db, brand_id, user_id)

    if not is_brand_child_visible(brand, user_id, alert):
        raise HTTPException(status_code=404, detail="Alert not found")

    if str(brand.get("owner_id", "")) != user_id:
        raise HTTPException(
            status_code=403,
            detail="Shared demo alerts are read-only",
        )

    return alert


# ---------------------------------------------------------
# RESPONSE SERIALIZATION
# ---------------------------------------------------------

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc

    doc["id"] = str(doc.pop("_id"))

    if not doc.get("message"):
        doc["message"] = (
            doc.get("details")
            or doc.get("title")
            or "Security alert notification."
        )

    if not doc.get("category"):
        doc["category"] = "BRAND_IMPERSONATION"

    if not doc.get("severity"):
        doc["severity"] = "HIGH"

    if doc.get("brand_id") is not None:
        doc["brand_id"] = str(doc["brand_id"])

    return doc


# ---------------------------------------------------------
# LIST ALERTS
# ---------------------------------------------------------

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    brand_id: Optional[str] = None,
    severity: Optional[str] = None,
    unread_only: bool = False,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)
    visible_brands = await get_visible_brands(db, user_id)

    if brand_id:
        if not ObjectId.is_valid(brand_id):
            raise HTTPException(status_code=400, detail="Invalid brand ID")

        brand = await get_alert_brand(db, brand_id, user_id)
        query = brand_child_filter(brand, user_id)
    else:
        query = readable_brand_children_filter(visible_brands, user_id)

    if severity and severity != "ALL":
        query["severity"] = severity

    if unread_only:
        query["is_read"] = False

    cursor = db.alerts.find(query).sort("created_at", -1)
    alerts = await cursor.to_list(length=500)

    return [serialize_doc(alert) for alert in alerts]


# ---------------------------------------------------------
# MARK ONE ALERT AS READ
# ---------------------------------------------------------

@router.post("/{id}/read")
async def mark_alert_read(
    id: str,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    alert = await get_writable_alert(db, id, user_id)
    brand = await get_alert_brand(
        db,
        str(alert.get("brand_id", "")),
        user_id,
    )

    result = await db.alerts.update_one(
        {
            "_id": ObjectId(id),
            **brand_child_filter(brand, user_id),
        },
        {"$set": {"is_read": True}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "status": "success",
        "message": "Alert marked as read",
    }


# ---------------------------------------------------------
# MARK ALL ALERTS AS READ
# ---------------------------------------------------------

@router.post("/mark-all-read")
async def mark_all_alerts_read(
    brand_id: Optional[str] = None,
    user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(user)

    if brand_id:
        if not ObjectId.is_valid(brand_id):
            raise HTTPException(status_code=400, detail="Invalid brand ID")

        brand = await get_alert_brand(db, brand_id, user_id)

        if str(brand.get("owner_id", "")) != user_id:
            raise HTTPException(
                status_code=403,
                detail="Shared demo alerts are read-only",
            )

        writable_brands = [brand]
    else:
        cursor = db.brands.find(
            {"owner_id": user_id},
            {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
        )
        writable_brands = await cursor.to_list(length=5000)

    if not writable_brands:
        return {"status": "success", "updated_count": 0}

    result = await db.alerts.update_many(
        readable_brand_children_filter(writable_brands, user_id),
        {"$set": {"is_read": True}},
    )

    return {
        "status": "success",
        "updated_count": result.modified_count,
    }