
import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.routes.access_control import (
    brand_child_filter,
    readable_brand_filter,
)
from app.models.schemas import ReportsSummaryResponse
from app.services.auth_service import require_current_user

logger = logging.getLogger("brandshield.routes.reports")

router = APIRouter(
    prefix="/reports",
    tags=["Compliance & Risk Reports"],
)


def get_user_id(user: dict) -> str:
    user_id = user.get("_id") or user.get("id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid user session")
    return str(user_id)


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc

    result = dict(doc)
    result["id"] = str(result.pop("_id"))
    return result


async def get_readable_brand(db, brand_id: str, user_id: str):
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    brand = await db.brands.find_one({
        "_id": ObjectId(brand_id),
        **readable_brand_filter(user_id),
        "is_archived": {"$ne": True},
    })

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    return brand


def brand_history_filter(brand: dict, user_id: str) -> dict:
    """Include this user's analyses and explicitly shared demo history."""
    return {
        "$or": [
            {
                "brand_id": str(brand["_id"]),
                "owner_id": user_id,
            },
            brand_child_filter(brand, user_id),
        ]
    }


def build_empty_summary(brand_name: str = "No data available") -> dict:
    return {
        "brand_name": brand_name,
        "total_scans": 0,
        "platform_breakdown": {
            "Instagram": 0,
            "Facebook": 0,
            "X": 0,
            "LinkedIn": 0,
        },
        "risk_distribution": {
            "Critical Risk": 0,
            "High Risk": 0,
            "Medium Risk": 0,
            "Low Risk": 0,
            "Normal": 0,
        },
        "active_threats_count": 0,
        "duplicates_detected_count": 0,
        "official_assets_protected": 0,
        "compliance_score": 98.50,
        "recent_threats": [],
        "generated_at": datetime.utcnow(),
    }


@router.get("/summary", response_model=ReportsSummaryResponse)
async def get_reports_summary(
    brand_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_current_user),
):
    user_id = get_user_id(current_user)
    db = get_db()

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Please try again later.",
        )

    brand = None
    if brand_id:
        brand = await get_readable_brand(db, brand_id, user_id)
    else:
        # Default to this user's brand, never another user's first brand.
        brand = await db.brands.find_one(
            {
                "owner_id": user_id,
                "is_archived": {"$ne": True},
            }
        )

    if brand:
        selected_brand_id = str(brand["_id"])
        brand_name = brand.get("name", "Brand")
    else:
        selected_brand_id = None
        brand_name = "No brand selected"

    # Reports without a brand are private and must not become global reports.
    if not selected_brand_id:
        return build_empty_summary(brand_name)

    scan_query = brand_history_filter(brand, user_id)
    threat_query = {
        "$and": [
            brand_child_filter(brand, user_id),
            {"is_official_safe": {"$ne": True}},
        ]
    }
    asset_query = brand_child_filter(brand, user_id)
    duplicate_query = brand_history_filter(brand, user_id)

    try:
        total_scans = await db.scan_history.count_documents(scan_query)

        platform_breakdown = {
            "Instagram": await db.scan_history.count_documents(
                {**scan_query, "platform": "Instagram"}
            ),
            "Facebook": await db.scan_history.count_documents(
                {**scan_query, "platform": "Facebook"}
            ),
            "X": await db.scan_history.count_documents(
                {**scan_query, "platform": "X"}
            ),
            "LinkedIn": await db.scan_history.count_documents(
                {**scan_query, "platform": "LinkedIn"}
            ),
        }

        risk_distribution = {
            category: await db.scan_history.count_documents(
                {**scan_query, "risk_category": category}
            )
            for category in (
                "Critical Risk",
                "High Risk",
                "Medium Risk",
                "Low Risk",
                "Normal",
            )
        }

        active_threats = await db.threats.count_documents(threat_query)
        protected_assets = await db.official_assets.count_documents(asset_query)
        duplicate_count = await db.duplicate_scans.count_documents(
            duplicate_query
        )

        compliance_score = 98.50
        if active_threats > 0:
            compliance_score = max(
                55.00,
                round(98.50 - (active_threats * 3.5), 2),
            )

        cursor = (
            db.threats.find(threat_query)
            .sort("detected_time", -1)
            .limit(5)
        )
        recent_threats = await cursor.to_list(length=5)

    except Exception:
        logger.exception("Failed to generate reports summary")
        raise HTTPException(
            status_code=500,
            detail="Unable to generate report summary",
        )

    return {
        "brand_name": brand_name,
        "total_scans": total_scans,
        "platform_breakdown": platform_breakdown,
        "risk_distribution": risk_distribution,
        "active_threats_count": active_threats,
        "duplicates_detected_count": duplicate_count,
        "official_assets_protected": protected_assets,
        "compliance_score": round(compliance_score, 2),
        "recent_threats": [serialize_doc(t) for t in recent_threats],
        "generated_at": datetime.utcnow(),
    }


@router.get("/export")
async def export_audit_report(
    brand_id: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_current_user),
):
    user_id = get_user_id(current_user)
    db = get_db()

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Please try again later.",
        )

    # Validate the selected brand before exporting any data.
    if brand_id:
        brand = await get_readable_brand(db, brand_id, user_id)
    else:
        brand = await db.brands.find_one(
            {
                "owner_id": user_id,
                "is_archived": {"$ne": True},
            }
        )

    if not brand:
        summary = build_empty_summary("No brand selected")
        scans = []
    else:
        selected_brand_id = str(brand["_id"])

        # Reuse the same authenticated report logic.
        summary = await get_reports_summary(
            selected_brand_id,
            current_user,
        )

        scan_query = brand_history_filter(brand, user_id)

        cursor = (
            db.scan_history.find(scan_query)
            .sort("scanned_at", -1)
            .limit(100)
        )
        items = await cursor.to_list(length=100)
        scans = [serialize_doc(item) for item in items]

    return {
        "report_id": f"REP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "executive_summary": summary,
        "detailed_scans": scans,
        "generated_at": datetime.utcnow().isoformat(),
        "disclaimer": (
            "This document contains automated digital risk protection "
            "telemetry compiled by BrandShield AI for brand integrity "
            "verification and trademark enforcement."
        ),
    }
