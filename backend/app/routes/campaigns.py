import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import CampaignResponse
from app.services.correlation_engine import correlate_threats_into_campaigns

logger = logging.getLogger("brandshield.routes.campaigns")
router = APIRouter(prefix="/campaigns", tags=["Cross-Platform Threat Campaigns"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(brand_id: Optional[str] = None):
    db = get_db()
    query = {}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id

    cursor = db.campaigns.find(query).sort("campaign_risk", -1)
    items = await cursor.to_list(length=50)

    # If no campaigns yet, run correlation
    if not items and brand_id:
        items = await correlate_threats_into_campaigns(db, brand_id)

    return [serialize_doc(i) for i in items]

@router.get("/{id}", response_model=CampaignResponse)
async def get_campaign(id: str):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid campaign ID")

    campaign = await db.campaigns.find_one({"_id": ObjectId(id)})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return serialize_doc(campaign)

@router.post("/recorrelate/{brand_id}")
async def force_recorrelate(brand_id: str):
    db = get_db()
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    campaigns = await correlate_threats_into_campaigns(db, brand_id)
    return {"status": "success", "correlated_campaigns": len(campaigns)}
