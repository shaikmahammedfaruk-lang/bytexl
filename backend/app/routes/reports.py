import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from app.database import get_db
from app.models.schemas import ReportsSummaryResponse

logger = logging.getLogger("brandshield.routes.reports")
router = APIRouter(prefix="/reports", tags=["Compliance & Risk Reports"])

def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/summary", response_model=ReportsSummaryResponse)
async def get_reports_summary(brand_id: Optional[str] = None):
    """
    Returns executive multi-platform risk & compliance telemetry report.
    """
    db = get_db()
    brand_name = "Global Monitoring"

    if db is None:
        now = datetime.utcnow()
        return {
            "brand_name": brand_name,
            "total_scans": 0,
            "platform_breakdown": {"Instagram": 0, "Facebook": 0, "X": 0, "LinkedIn": 0},
            "risk_distribution": {"Critical Risk": 0, "High Risk": 0, "Medium Risk": 0, "Low Risk": 0, "Normal": 0},
            "active_threats_count": 0,
            "duplicates_detected_count": 0,
            "official_assets_protected": 0,
            "compliance_score": 98.50,
            "recent_threats": [],
            "generated_at": now
        }

    # Brand context
    if brand_id and ObjectId.is_valid(brand_id):
        b = await db.brands.find_one({"_id": ObjectId(brand_id)})
        if b:
            brand_name = b.get("name", "Brand")
    else:
        b = await db.brands.find_one({"is_archived": {"$ne": True}})
        if b:
            brand_name = b.get("name", "Brand")
            brand_id = str(b["_id"])

    # Query scan history
    scan_query = {}
    threat_query = {"is_official_safe": {"$ne": True}}
    asset_query = {}
    if brand_id:
        scan_query["brand_id"] = brand_id
        threat_query["brand_id"] = brand_id
        asset_query["brand_id"] = brand_id

    total_scans = await db.scan_history.count_documents(scan_query)
    
    # Platform breakdown
    fb_count = await db.scan_history.count_documents({**scan_query, "platform": "Facebook"})
    x_count = await db.scan_history.count_documents({**scan_query, "platform": "X"})
    li_count = await db.scan_history.count_documents({**scan_query, "platform": "LinkedIn"})
    ig_count = await db.scan_history.count_documents({**scan_query, "platform": "Instagram"})

    # Risk distribution
    crit_count = await db.scan_history.count_documents({**scan_query, "risk_category": "Critical Risk"})
    high_count = await db.scan_history.count_documents({**scan_query, "risk_category": "High Risk"})
    med_count = await db.scan_history.count_documents({**scan_query, "risk_category": "Medium Risk"})
    low_count = await db.scan_history.count_documents({**scan_query, "risk_category": "Low Risk"})
    norm_count = await db.scan_history.count_documents({**scan_query, "risk_category": "Normal"})

    # Active threats and official assets
    active_threats = await db.threats.count_documents(threat_query)
    protected_assets = await db.official_assets.count_documents(asset_query)
    dup_count = await db.duplicate_scans.count_documents(scan_query)

    # Calculate compliance / protection posture score
    compliance_score = 98.50
    if active_threats > 0:
        compliance_score = max(55.00, round(98.50 - (active_threats * 3.5), 2))

    # Recent threat samples
    recent_threats_cursor = db.threats.find(threat_query).sort("detected_time", -1).limit(5)
    recent_threats = await recent_threats_cursor.to_list(length=5)

    return {
        "brand_name": brand_name,
        "total_scans": total_scans,
        "platform_breakdown": {
            "Instagram": ig_count,
            "Facebook": fb_count,
            "X": x_count,
            "LinkedIn": li_count
        },
        "risk_distribution": {
            "Critical Risk": crit_count,
            "High Risk": high_count,
            "Medium Risk": med_count,
            "Low Risk": low_count,
            "Normal": norm_count
        },
        "active_threats_count": active_threats,
        "duplicates_detected_count": dup_count,
        "official_assets_protected": protected_assets,
        "compliance_score": round(compliance_score, 2),
        "recent_threats": [serialize_doc(t) for t in recent_threats],
        "generated_at": datetime.utcnow()
    }

@router.get("/export")
async def export_audit_report(brand_id: Optional[str] = None):
    """
    Generates a full JSON audit dossier for legal, forensics, and compliance.
    """
    summary = await get_reports_summary(brand_id)
    db = get_db()
    scans = []
    if db is not None:
        query = {"brand_id": brand_id} if brand_id else {}
        cursor = db.scan_history.find(query).sort("scanned_at", -1).limit(100)
        items = await cursor.to_list(length=100)
        scans = [serialize_doc(it) for it in items]

    return {
        "report_id": f"REP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "executive_summary": summary,
        "detailed_scans": scans,
        "generated_at": datetime.utcnow().isoformat(),
        "disclaimer": "This document contains automated digital risk protection telemetry compiled by BrandShield AI for brand integrity verification and trademark enforcement."
    }
