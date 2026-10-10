import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query
from bson import ObjectId
from app.database import get_db

logger = logging.getLogger("brandshield.routes.analytics")
router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])

@router.get("")
async def get_analytics_metrics(
    brand_id: Optional[str] = None,
    timeframe: str = Query("30d", pattern="^(7d|30d|90d)$")
):
    db = get_db()
    days = 7 if timeframe == "7d" else (90 if timeframe == "90d" else 30)
    cutoff = datetime.utcnow() - timedelta(days=days)

    match_stage = {"is_official_safe": {"$ne": True}}
    if brand_id and ObjectId.is_valid(brand_id):
        match_stage["brand_id"] = brand_id

    # Base counts
    total_threats = await db.threats.count_documents(match_stage)
    social_threats = await db.threats.count_documents({**match_stage, "asset_type": "social"})
    app_threats = await db.threats.count_documents({**match_stage, "asset_type": "app"})
    critical_threats = await db.threats.count_documents({**match_stage, "risk_level": "CRITICAL"})
    high_threats = await db.threats.count_documents({**match_stage, "risk_level": "HIGH"})
    medium_threats = await db.threats.count_documents({**match_stage, "risk_level": "MEDIUM"})
    low_threats = await db.threats.count_documents({**match_stage, "risk_level": "LOW"})
    resolved_threats = await db.threats.count_documents({**match_stage, "status": "RESOLVED"})
    active_threats = await db.threats.count_documents({**match_stage, "status": {"$in": ["NEW", "UNDER_INVESTIGATION", "REVIEWED"]}})

    # Campaigns count
    camp_query = {}
    if brand_id and ObjectId.is_valid(brand_id):
        camp_query["brand_id"] = brand_id
    active_campaigns = await db.campaigns.count_documents(camp_query)

    # Threats by platform aggregation
    pipeline_platform = [
        {"$match": match_stage},
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    platform_agg = await db.threats.aggregate(pipeline_platform).to_list(length=20)
    threats_by_platform = [{"platform": doc["_id"] or "Unknown", "count": doc["count"]} for doc in platform_agg]

    # Threats by type aggregation
    pipeline_types = [
        {"$match": match_stage},
        {"$group": {"_id": "$threat_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    types_agg = await db.threats.aggregate(pipeline_types).to_list(length=20)
    threat_types = [{"type": doc["_id"] or "General Impersonation", "count": doc["count"]} for doc in types_agg]

    # Customer impact distribution
    pipeline_impact = [
        {"$match": match_stage},
        {"$bucket": {
            "groupBy": "$customer_impact_score",
            "boundaries": [0, 25, 50, 75, 100],
            "default": "Other",
            "output": {"count": {"$sum": 1}}
        }}
    ]
    try:
        impact_agg = await db.threats.aggregate(pipeline_impact).to_list(length=10)
        impact_labels = {0: "Low (0-24)", 25: "Moderate (25-49)", 50: "High (50-74)", 75: "Severe (75-100)"}
        customer_impact_dist = [{"level": impact_labels.get(d["_id"], str(d["_id"])), "count": d["count"]} for d in impact_agg]
    except Exception:
        customer_impact_dist = [
            {"level": "Severe (75-100)", "count": critical_threats},
            {"level": "High (50-74)", "count": high_threats},
            {"level": "Moderate (25-49)", "count": medium_threats},
            {"level": "Low (0-24)", "count": low_threats}
        ]

    # Trend timeline (daily buckets for the selected timeframe)
    # Generate continuous dates so charts render nicely without gaps
    num_intervals = 7 if days == 7 else (14 if days == 30 else 12)
    step_days = max(1, days // num_intervals)
    
    threat_trend = []
    for i in range(num_intervals, -1, -1):
        target_date = datetime.utcnow() - timedelta(days=i * step_days)
        next_date = target_date + timedelta(days=step_days)
        
        t_tot = await db.threats.count_documents({
            **match_stage,
            "detected_time": {"$lte": next_date}
        })
        t_soc = await db.threats.count_documents({
            **match_stage,
            "asset_type": "social",
            "detected_time": {"$lte": next_date}
        })
        t_app = await db.threats.count_documents({
            **match_stage,
            "asset_type": "app",
            "detected_time": {"$lte": next_date}
        })
        
        threat_trend.append({
            "date": target_date.strftime("%b %d"),
            "total": t_tot,
            "social": t_soc,
            "apps": t_app
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
            "active_campaigns": active_campaigns
        },
        "risk_distribution": [
            {"name": "Critical", "count": critical_threats, "color": "#f43f5e"},
            {"name": "High", "count": high_threats, "color": "#f97316"},
            {"name": "Medium", "count": medium_threats, "color": "#eab308"},
            {"name": "Low", "count": low_threats, "color": "#10b981"}
        ],
        "threats_by_platform": threats_by_platform,
        "threat_types": threat_types,
        "customer_impact_distribution": customer_impact_dist,
        "threat_trend": threat_trend,
        "timeframe": timeframe
    }
