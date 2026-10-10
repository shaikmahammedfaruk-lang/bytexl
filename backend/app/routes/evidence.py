import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Response
from bson import ObjectId
from app.database import get_db
from app.services.evidence_service import generate_evidence_package

logger = logging.getLogger("brandshield.routes.evidence")
router = APIRouter(prefix="/evidence", tags=["Evidence Center"])

@router.post("/{threat_id}/generate")
async def create_evidence_report(threat_id: str):
    db = get_db()
    if not ObjectId.is_valid(threat_id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")

    threat = await db.threats.find_one({"_id": ObjectId(threat_id)})
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    brand_id = threat.get("brand_id")
    brand = await db.brands.find_one({"_id": ObjectId(brand_id) if ObjectId.is_valid(brand_id) else brand_id})
    brand_dict = brand or {"name": "Target Brand"}

    evidence_doc = generate_evidence_package(threat, brand_dict)

    # Save to evidence collection
    await db.evidence.insert_one(dict(evidence_doc))

    return evidence_doc

@router.get("/{threat_id}")
async def get_latest_evidence(threat_id: str):
    db = get_db()
    if not ObjectId.is_valid(threat_id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")

    doc = await db.evidence.find_one({"threat_id": threat_id}, sort=[("_id", -1)])
    if not doc:
        # Generate on the fly
        return await create_evidence_report(threat_id)
    doc["id"] = str(doc.pop("_id"))
    return doc
