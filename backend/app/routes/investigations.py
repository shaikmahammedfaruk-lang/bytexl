import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import InvestigationCreate, InvestigationResponse

logger = logging.getLogger("brandshield.routes.investigations")
router = APIRouter(prefix="/investigations", tags=["AI Threat Investigator"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.post("", response_model=InvestigationResponse)
async def create_investigation(inv_in: InvestigationCreate):
    db = get_db()
    threat_id = inv_in.threat_id
    if not ObjectId.is_valid(threat_id):
        raise HTTPException(status_code=400, detail="Invalid threat ID")

    threat = await db.threats.find_one({"_id": ObjectId(threat_id)})
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    brand_id = threat.get("brand_id")
    brand = await db.brands.find_one({"_id": ObjectId(brand_id) if ObjectId.is_valid(brand_id) else brand_id})
    brand_name = brand.get("name") if brand else "Brand"

    # Check if existing investigation for this threat
    existing = await db.investigations.find_one({"threat_id": threat_id})
    if existing:
        return serialize_doc(existing)

    now = datetime.utcnow()
    case_num = f"INV-{now.strftime('%Y')}-{str(int(now.timestamp()))[-4:]}"
    
    # Mark threat as UNDER_INVESTIGATION
    await db.threats.update_one(
        {"_id": ObjectId(threat_id)},
        {"$set": {"status": "UNDER_INVESTIGATION", "updated_at": now}}
    )

    factors = threat.get("detection_factors", {})
    evidence_items = [
        {"type": "Infringing URL", "detail": threat.get("url")},
        {"type": "Name Resemblance", "detail": f"{factors.get('name_similarity', 0)}% similarity ({factors.get('lookalike_type')})"},
        {"type": "Logo Analysis", "detail": f"{factors.get('logo_similarity', 0)}% visual alignment with {brand_name} trademark"},
        {"type": "Targeting Triggers", "detail": ", ".join(factors.get("targeting_phrases", [])) or "Synthetic profile imitating support desk"}
    ]

    rec_actions = [
        f"Generate certified evidence package for {threat.get('platform')} takedown submission",
        f"Correlate threat indicators with cross-platform campaign syndicate",
        f"Assign SecOps analyst to monitor infrastructure mutations"
    ]

    timeline = [
        {"time": threat.get("detected_time", now).isoformat(), "event": "Threat discovered by BrandShield crawler"},
        {"time": now.isoformat(), "event": f"Automated AI Investigation initiated under Case {case_num}"}
    ]

    inv_doc = {
        "threat_id": threat_id,
        "brand_id": brand_id,
        "case_number": case_num,
        "title": inv_in.title or f"Investigation: {threat.get('threat_type')} on {threat.get('platform')}",
        "status": "OPEN",
        "analyst": inv_in.analyst or "Senior Threat Analyst",
        "summary": f"High-confidence {threat.get('threat_type')} identified posing immediate threat to {brand_name} customers. Risk score {threat.get('risk_score')}/100 with customer impact score of {threat.get('customer_impact_score')}/100.",
        "evidence_items": evidence_items,
        "recommended_actions": rec_actions,
        "timeline": timeline,
        "created_at": now
    }

    res = await db.investigations.insert_one(inv_doc)
    inv_doc["id"] = str(res.inserted_id)
    return inv_doc

@router.get("", response_model=List[InvestigationResponse])
async def list_investigations(brand_id: Optional[str] = None):
    db = get_db()
    query = {}
    if brand_id and ObjectId.is_valid(brand_id):
        query["brand_id"] = brand_id

    cursor = db.investigations.find(query).sort("created_at", -1)
    items = await cursor.to_list(length=100)
    return [serialize_doc(i) for i in items]

@router.get("/{id}", response_model=InvestigationResponse)
async def get_investigation(id: str):
    db = get_db()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid investigation ID")

    inv = await db.investigations.find_one({"_id": ObjectId(id)})
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return serialize_doc(inv)
