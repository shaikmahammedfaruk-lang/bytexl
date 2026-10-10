import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import (
    DuplicateDetectionRequest,
    DuplicateDetectionResponse
)
from app.services.duplicate_detection_service import detect_duplicate_accounts

logger = logging.getLogger("brandshield.routes.duplicate_detection")
router = APIRouter(prefix="/duplicate-detection", tags=["Duplicate & Impersonation Detection"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.post("/scan", response_model=DuplicateDetectionResponse)
async def scan_duplicates(req: DuplicateDetectionRequest):
    """
    Scans for duplicate or impersonating accounts matching a reference account or protected brand.
    Combines existing active threat feeds with multi-signal lookalike discovery across platforms.
    """
    db = get_db()
    brand = None
    existing_threats = []

    if db is not None:
        try:
            if req.brand_id and ObjectId.is_valid(req.brand_id):
                brand = await db.brands.find_one({"_id": ObjectId(req.brand_id)})
                cursor = db.threats.find({"brand_id": req.brand_id, "is_official_safe": {"$ne": True}})
                existing_threats = await cursor.to_list(length=100)
            
            if not brand:
                all_brands = await db.brands.find({"is_archived": {"$ne": True}}).to_list(1)
                if all_brands:
                    brand = all_brands[0]
                    cursor = db.threats.find({"brand_id": str(brand["_id"]), "is_official_safe": {"$ne": True}})
                    existing_threats = await cursor.to_list(length=100)
        except Exception as e:
            logger.warning(f"Error accessing brand threats for duplicate scan: {e}")

    brand_name = (brand.get("name") if brand else "") or req.target_keyword or "Protected Brand"

    result = detect_duplicate_accounts(
        brand_name=brand_name,
        platform=req.platform or "ALL",
        reference_account_url=req.reference_account_url,
        threshold=req.threshold or 40.0,
        existing_threats=existing_threats
    )

    now = datetime.utcnow()
    result["timestamp"] = now

    # Store detection run in MongoDB for audit history
    if db is not None:
        try:
            doc_to_save = dict(result)
            doc_to_save["brand_id"] = str(brand["_id"]) if brand and "_id" in brand else req.brand_id
            doc_to_save["created_at"] = now
            await db.duplicate_scans.insert_one(doc_to_save)
        except Exception as e:
            logger.warning(f"Error storing duplicate scan: {e}")

    return result

@router.get("/history")
async def get_duplicate_history(brand_id: Optional[str] = None, limit: int = 10):
    db = get_db()
    if db is None:
        return []
    query = {}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id
    cursor = db.duplicate_scans.find(query).sort("created_at", -1).limit(limit)
    items = await cursor.to_list(length=limit)
    return [serialize_doc(it) for it in items]
