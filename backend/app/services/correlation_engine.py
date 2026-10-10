import logging
from typing import List, Dict, Any
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger("brandshield.correlation")

async def correlate_threats_into_campaigns(db, brand_id: str) -> List[Dict[str, Any]]:
    """
    Examines threats for a given brand and groups related multi-channel threats into coordinated Threat Campaigns.
    Generates node and edge graph data for visual graph rendering in the frontend.
    """
    threats_cursor = db.threats.find({"brand_id": brand_id, "is_official_safe": {"$ne": True}})
    threats = await threats_cursor.to_list(length=200)

    if not threats:
        return []

    # Cluster threats based on common lookalike motifs (e.g. "support", "care", "banking", "kyc", or common threat actor indicators)
    clusters: Dict[str, List[Dict[str, Any]]] = {}

    for t in threats:
        name_lower = (t.get("account_or_app_name") or "").lower()
        desc_lower = (t.get("bio_or_description") or "").lower()
        dev_lower = (t.get("developer_name") or "").lower()

        # Identify thematic cluster
        if any(w in name_lower or w in desc_lower for w in ["support", "care", "help", "desk", "assist"]):
            cluster_key = "Customer Support Impersonation"
        elif any(w in name_lower or w in desc_lower for w in ["reward", "cashback", "prize", "bonus", "lottery"]):
            cluster_key = "Fraudulent Reward / Cashback Scam"
        elif any(w in name_lower or w in desc_lower for w in ["kyc", "otp", "verify", "unblock"]):
            cluster_key = "Credential & KYC Phishing Syndicate"
        else:
            cluster_key = "General Brand Impersonation Wave"

        clusters.setdefault(cluster_key, []).append(t)

    brand_doc = await db.brands.find_one({"_id": ObjectId(brand_id) if ObjectId.is_valid(brand_id) else brand_id})
    brand_name = brand_doc.get("name") if brand_doc else "Target Brand"

    campaigns = []

    for theme, group in clusters.items():
        # Even single or multi threats form a campaign if risk is substantial
        if len(group) >= 1:
            platforms = list(set([t.get("platform") for t in group if t.get("platform")]))
            threat_ids = [str(t.get("_id")) for t in group]
            
            # Campaign risk is aggregated and elevated because coordinated multi-vector attacks are more lethal
            max_risk = max([t.get("risk_score", 50.0) for t in group])
            campaign_risk = round(min(99.0, max_risk + (len(group) - 1) * 3.5), 1)

            campaign_name = f"{brand_name} {theme} Campaign"

            # Construct graph nodes & edges
            nodes = [
                {
                    "id": "brand_root",
                    "label": brand_name,
                    "type": "brand",
                    "platform": "Core Brand",
                    "risk": 0
                }
            ]

            edges = []

            for threat in group:
                t_id = str(threat.get("_id"))
                t_label = threat.get("account_or_app_name") or threat.get("username_or_package") or "Asset"
                t_platform = threat.get("platform", "Web")
                t_risk = threat.get("risk_score", 50.0)
                t_type = threat.get("asset_type", "social")

                nodes.append({
                    "id": t_id,
                    "label": t_label,
                    "type": t_type,
                    "platform": t_platform,
                    "risk": t_risk,
                    "threat_type": threat.get("threat_type"),
                    "url": threat.get("url")
                })

                # Edge from brand to threat
                edges.append({
                    "source": "brand_root",
                    "target": t_id,
                    "label": f"Impersonating via {t_platform}",
                    "relationship": "TARGETS"
                })

                # If mobile app with developer, add developer node
                dev = threat.get("developer_name")
                if dev and dev.lower() != "unknown" and dev != "":
                    dev_id = f"dev_{t_id}"
                    nodes.append({
                        "id": dev_id,
                        "label": dev,
                        "type": "developer",
                        "platform": "Developer Entity",
                        "risk": t_risk
                    })
                    edges.append({
                        "source": t_id,
                        "target": dev_id,
                        "label": "Published By",
                        "relationship": "PUBLISHED_BY"
                    })

            campaign_doc = {
                "brand_id": brand_id,
                "name": campaign_name,
                "campaign_risk": campaign_risk,
                "status": "ACTIVE",
                "platforms": platforms,
                "threat_count": len(group),
                "related_threat_ids": threat_ids,
                "detected_time": datetime.utcnow(),
                "description": f"Cross-platform coordinated campaign targeting {brand_name} users across {', '.join(platforms)}. Multiple synthetic assets exhibit synchronized branding and targeting semantics.",
                "nodes": nodes,
                "edges": edges
            }

            # Upsert into campaigns collection
            existing = await db.campaigns.find_one({"brand_id": brand_id, "name": campaign_name})
            if existing:
                await db.campaigns.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "campaign_risk": campaign_risk,
                        "platforms": platforms,
                        "threat_count": len(group),
                        "related_threat_ids": threat_ids,
                        "nodes": nodes,
                        "edges": edges
                    }}
                )
                campaign_doc["id"] = str(existing["_id"])
            else:
                res = await db.campaigns.insert_one(campaign_doc)
                campaign_doc["id"] = str(res.inserted_id)

            campaigns.append(campaign_doc)

            # Link threat documents to this campaign
            await db.threats.update_many(
                {"_id": {"$in": [t["_id"] for t in group]}},
                {"$set": {"campaign_id": campaign_doc["id"], "campaign_name": campaign_name}}
            )

    return campaigns
