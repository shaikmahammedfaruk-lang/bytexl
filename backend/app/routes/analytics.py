import logging
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.routes.access_control import (
    readable_brand_children_filter,
    readable_brand_filter,
)
from app.services.auth_service import require_current_user

logger = logging.getLogger("brandshield.routes.analytics")

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics & Reporting"],
)


def get_user_id(user: dict) -> str:
    user_id = user.get("id") or user.get("_id")
    return str(user_id) if user_id else ""


@router.get("")
async def get_analytics_metrics(
    brand_id: Optional[str] = None,
    timeframe: str = Query("30d", pattern="^(7d|30d|90d)$"),
    current_user: dict = Depends(require_current_user),
):
    db = get_db()
    user_id = get_user_id(current_user)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid user session",
        )

    # Restrict analytics to brands owned by this user and explicitly
    # marked as shared/demo data.
    readable_brands = await db.brands.find(
        readable_brand_filter(user_id),
        {"_id": 1, "owner_id": 1, "is_demo": 1, "is_shared": 1},
    ).to_list(length=5000)

    readable_brand_ids = [
        str(brand["_id"]) for brand in readable_brands
    ]

    # If a particular brand was requested, validate it strictly.
    if brand_id is not None:
        if not ObjectId.is_valid(brand_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid brand ID",
            )

        if brand_id not in readable_brand_ids:
            raise HTTPException(
                status_code=404,
                detail="Brand not found",
            )

        selected_brands = [
            brand for brand in readable_brands
            if str(brand["_id"]) == brand_id
        ]
    else:
        selected_brands = readable_brands

    days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
    }[timeframe]

    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)

    match_stage = {
        **readable_brand_children_filter(selected_brands, user_id),
        "is_official_safe": {"$ne": True},
    }

    # Base threat counts
    total_threats = await db.threats.count_documents(match_stage)

    social_threats = await db.threats.count_documents({
        **match_stage,
        "asset_type": "social",
    })

    app_threats = await db.threats.count_documents({
        **match_stage,
        "asset_type": "app",
    })

    critical_threats = await db.threats.count_documents({
        **match_stage,
        "risk_level": "CRITICAL",
    })

    high_threats = await db.threats.count_documents({
        **match_stage,
        "risk_level": "HIGH",
    })

    medium_threats = await db.threats.count_documents({
        **match_stage,
        "risk_level": "MEDIUM",
    })

    low_threats = await db.threats.count_documents({
        **match_stage,
        "risk_level": "LOW",
    })

    resolved_threats = await db.threats.count_documents({
        **match_stage,
        "status": "RESOLVED",
    })

    active_threats = await db.threats.count_documents({
        **match_stage,
        "status": {
            "$in": [
                "NEW",
                "UNDER_INVESTIGATION",
                "REVIEWED",
            ]
        },
    })

    # Campaigns belonging to readable brands only
    active_campaigns = await db.campaigns.count_documents({
        "$and": [
            readable_brand_children_filter(selected_brands, user_id),
            {"status": {"$nin": ["RESOLVED", "CLOSED"]}},
        ]
    })

    # Threats grouped by platform
    platform_pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$platform",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]

    platform_agg = await db.threats.aggregate(
        platform_pipeline
    ).to_list(length=20)

    threats_by_platform = [
        {
            "platform": item["_id"] or "Unknown",
            "count": item["count"],
        }
        for item in platform_agg
    ]

    # Threats grouped by type
    type_pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$threat_type",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]

    type_agg = await db.threats.aggregate(
        type_pipeline
    ).to_list(length=20)

    threat_types = [
        {
            "type": item["_id"] or "General Impersonation",
            "count": item["count"],
        }
        for item in type_agg
    ]

    # Customer impact distribution
    impact_pipeline = [
        {
            "$match": {
                **match_stage,
                "customer_impact_score": {
                    "$gte": 0,
                    "$lte": 100,
                },
            }
        },
        {
            "$bucket": {
                "groupBy": "$customer_impact_score",
                "boundaries": [0, 25, 50, 75, 101],
                "default": "Other",
                "output": {
                    "count": {"$sum": 1},
                },
            }
        },
    ]

    try:
        impact_agg = await db.threats.aggregate(
            impact_pipeline
        ).to_list(length=10)

        impact_labels = {
            0: "Low (0-24)",
            25: "Moderate (25-49)",
            50: "High (50-74)",
            75: "Severe (75-100)",
        }

        customer_impact_dist = [
            {
                "level": impact_labels.get(
                    item["_id"],
                    str(item["_id"]),
                ),
                "count": item["count"],
            }
            for item in impact_agg
        ]

    except Exception:
        logger.exception("Could not calculate customer impact distribution")

        customer_impact_dist = [
            {"level": "Severe (75-100)", "count": 0},
            {"level": "High (50-74)", "count": 0},
            {"level": "Moderate (25-49)", "count": 0},
            {"level": "Low (0-24)", "count": 0},
        ]

    # Trend timeline: count threats detected within each interval.
    # This avoids repeatedly counting all historical threats.
    num_intervals = {
        "7d": 7,
        "30d": 14,
        "90d": 12,
    }[timeframe]

    interval_seconds = (days * 24 * 60 * 60) / num_intervals

    threat_trend = []

    for i in range(num_intervals):
        start_date = cutoff + timedelta(
            seconds=i * interval_seconds
        )

        end_date = (
            cutoff
            + timedelta(seconds=(i + 1) * interval_seconds)
        )

        if i == num_intervals - 1:
            end_date = now

        interval_match = {
            **match_stage,
            "detected_time": {
                "$gte": start_date,
                "$lt": end_date,
            },
        }

        total = await db.threats.count_documents(interval_match)

        social = await db.threats.count_documents({
            **interval_match,
            "asset_type": "social",
        })

        apps_count = await db.threats.count_documents({
            **interval_match,
            "asset_type": "app",
        })

        threat_trend.append({
            "date": start_date.strftime("%b %d"),
            "total": total,
            "social": social,
            "apps": apps_count,
        })

    return {
        "summary": {
            "total_threats": total_threats,
            "active_threats": active_threats,
            "social_threats": social_threats,
            "app_threats": app_threats,
            "critical_threats": critical_threats,
            "high_threats": high_threats,
            "medium_threats": medium_threats,
            "low_threats": low_threats,
            "resolved_threats": resolved_threats,
            "active_campaigns": active_campaigns,
        },
        "risk_distribution": [
            {
                "name": "Critical",
                "count": critical_threats,
                "color": "#f43f5e",
            },
            {
                "name": "High",
                "count": high_threats,
                "color": "#f97316",
            },
            {
                "name": "Medium",
                "count": medium_threats,
                "color": "#eab308",
            },
            {
                "name": "Low",
                "count": low_threats,
                "color": "#10b981",
            },
        ],
        "threats_by_platform": threats_by_platform,
        "threat_types": threat_types,
        "customer_impact_distribution": customer_impact_dist,
        "threat_trend": threat_trend,
        "timeframe": timeframe,
    }