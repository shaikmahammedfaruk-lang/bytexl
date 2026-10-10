import logging
from datetime import datetime, timedelta
from bson import ObjectId
from app.services.detection_engine import run_multi_signal_detection
from app.services.correlation_engine import correlate_threats_into_campaigns

logger = logging.getLogger("brandshield.demo")


async def ensure_sample_brands(db):
    """Add requested starter profiles without replacing existing brand data."""
    now = datetime.utcnow()
    sample_brands = [
        {
            "name": "Puma",
            "website": "https://us.puma.com",
            "industry": "Sportswear & Apparel",
            "description": "Official brand profile for Puma digital asset monitoring.",
            "brand_keywords": ["puma", "sportswear", "sneakers", "running"],
            "brand_aliases": ["PUMA SE"],
        },
        {
            "name": "OneNight",
            "industry": "Other",
            "description": "Starter profile for OneNight. Add verified assets to complete monitoring.",
            "brand_keywords": ["onenight", "one night"],
            "brand_aliases": [],
        },
        {
            "name": "Sparks",
            "industry": "Other",
            "description": "Starter profile for Sparks. Add verified assets to complete monitoring.",
            "brand_keywords": ["sparks"],
            "brand_aliases": [],
        },
    ]

    for brand in sample_brands:
        if await db.brands.find_one({"name": brand["name"]}, {"_id": 1}):
            continue

        brand.update({
            "is_archived": False,
            "created_at": now,
            "updated_at": now,
        })
        await db.brands.insert_one(brand)


async def load_demo_data(db):
    """
    Populates database with the official hackathon demo scenario:
    Brand: ABC Bank
    Official assets:
      - Instagram: @abcbank
      - Facebook: ABC Bank
      - X: @abcbank
      - Official App: ABC Bank Mobile (Dev: ABC Technologies Ltd)
    Suspicious assets:
      - @abcbank_support (Instagram)
      - ABC Bank Customer Care (Facebook)
      - Fake ABC Bank Mobile (Google Play, Dev: Unknown Apps Ltd)
    """
    logger.info("Purging existing demo data for clean slate...")
    # Find if ABC Bank already exists
    existing_brand = await db.brands.find_one({"name": "ABC Bank"})
    if existing_brand:
        b_id = str(existing_brand["_id"])
        await db.official_assets.delete_many({"brand_id": b_id})
        await db.threats.delete_many({"brand_id": b_id})
        await db.campaigns.delete_many({"brand_id": b_id})
        await db.investigations.delete_many({"brand_id": b_id})
        await db.alerts.delete_many({"brand_id": b_id})
        await db.brands.delete_one({"_id": existing_brand["_id"]})

    # 1. Create ABC Bank Brand
    now = datetime.utcnow()
    await ensure_sample_brands(db)
    brand_doc = {
        "name": "ABC Bank",
        "website": "https://abcbank.example",
        "industry": "Banking & Financial Services",
        "description": "Premier retail and commercial digital banking provider serving over 4 million customers worldwide.",
        "logo_url": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=200",
        "official_instagram_username": "abcbank",
        "official_instagram_url": "https://instagram.com/abcbank",
        "official_bio": "Official Instagram account of ABC Bank. Serving over 4M digital banking customers. FDIC Insured.",
        "official_instagram_logo": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=200",
        "official_social_links": ["https://twitter.com/abcbank", "https://facebook.com/abcbank"],
        "official_app_links": ["https://play.google.com/store/apps/details?id=com.abcbank.mobile"],
        "brand_keywords": ["abc", "bank", "wealth", "mobile banking", "customer support", "cards", "savings"],
        "brand_aliases": ["ABCBank", "ABC Financial", "ABC Bank Group"],
        "is_archived": False,
        "created_at": now - timedelta(days=30),
        "updated_at": now
    }
    res = await db.brands.insert_one(brand_doc)
    brand_id = str(res.inserted_id)

    # 1b. Ensure Nike exists with complete official ground truth reference
    nike_brand = await db.brands.find_one({"name": "Nike"})
    if not nike_brand:
        nike_doc = {
            "name": "Nike",
            "website": "https://nike.com",
            "industry": "Athletic Footwear & Apparel",
            "description": "Global sportswear and athletic equipment corporation.",
            "logo_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200",
            "official_instagram_username": "nike",
            "official_instagram_url": "https://instagram.com/nike",
            "official_bio": "Just Do It. #Nike",
            "official_instagram_logo": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200",
            "official_social_links": ["https://twitter.com/nike", "https://facebook.com/nike", "https://youtube.com/nike"],
            "official_app_links": ["https://apps.apple.com/app/nike-shoes-apparel-stories/id1095459556"],
            "brand_keywords": ["nike", "swoosh", "just do it", "air max", "jordan", "snkrs"],
            "brand_aliases": ["Nike Inc", "Nike Official", "Nike Sportswear"],
            "is_archived": False,
            "created_at": now - timedelta(days=60),
            "updated_at": now
        }
        n_res = await db.brands.insert_one(nike_doc)
        n_id = str(n_res.inserted_id)
        await db.official_assets.insert_one({
            "brand_id": n_id,
            "name": "Nike Official Instagram",
            "asset_type": "social",
            "platform": "Instagram",
            "url": "https://instagram.com/nike",
            "identifier": "@nike",
            "verification_status": "VERIFIED",
            "logo_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200",
            "created_at": now - timedelta(days=60)
        })
    else:
        await db.brands.update_one(
            {"_id": nike_brand["_id"]},
            {"$set": {
                "official_instagram_username": "nike",
                "official_instagram_url": "https://instagram.com/nike",
                "official_bio": "Just Do It. #Nike",
                "official_instagram_logo": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200",
                "official_social_links": ["https://twitter.com/nike", "https://facebook.com/nike", "https://youtube.com/nike"],
                "official_app_links": ["https://apps.apple.com/app/nike-shoes-apparel-stories/id1095459556"],
            }}
        )

    # 2. Add Official Assets
    official_assets_raw = [
        {
            "brand_id": brand_id,
            "name": "ABC Bank Official Instagram",
            "asset_type": "social",
            "platform": "Instagram",
            "url": "https://instagram.com/abcbank",
            "identifier": "@abcbank",
            "verification_status": "VERIFIED",
            "logo_url": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=200",
            "created_at": now - timedelta(days=28)
        },
        {
            "brand_id": brand_id,
            "name": "ABC Bank Official Facebook",
            "asset_type": "social",
            "platform": "Facebook",
            "url": "https://facebook.com/abcbank",
            "identifier": "ABC Bank",
            "verification_status": "VERIFIED",
            "logo_url": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=200",
            "created_at": now - timedelta(days=28)
        },
        {
            "brand_id": brand_id,
            "name": "ABC Bank Official X Profile",
            "asset_type": "social",
            "platform": "X",
            "url": "https://x.com/abcbank",
            "identifier": "@abcbank",
            "verification_status": "VERIFIED",
            "logo_url": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=200",
            "created_at": now - timedelta(days=28)
        },
        {
            "brand_id": brand_id,
            "name": "ABC Bank Mobile App",
            "asset_type": "app",
            "platform": "Google Play",
            "url": "https://play.google.com/store/apps/details?id=com.abcbank.mobile",
            "identifier": "com.abcbank.mobile",
            "package_id": "com.abcbank.mobile",
            "developer_name": "ABC Technologies Ltd",
            "verification_status": "VERIFIED",
            "logo_url": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=200",
            "created_at": now - timedelta(days=25)
        }
    ]
    
    official_assets = []
    for asset in official_assets_raw:
        a_res = await db.official_assets.insert_one(asset)
        asset_copy = dict(asset)
        asset_copy["_id"] = a_res.inserted_id
        official_assets.append(asset_copy)

    # 3. Create Suspicious Candidates and Run through Detection Engine
    suspicious_candidates = [
        {
            "asset_type": "social",
            "platform": "Instagram",
            "url": "https://instagram.com/abcbank_support",
            "display_name": "ABC Bank Support & Helpdesk",
            "username": "@abcbank_support",
            "bio": "Official 24/7 ABC Bank Support team. Send OTP or DM us to unblock account & update KYC verification immediately.",
            "profile_image_url": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=180",
            "followers": 1280,
            "following": 84,
            "detected_time": now - timedelta(hours=4)
        },
        {
            "asset_type": "social",
            "platform": "Facebook",
            "url": "https://facebook.com/abcbank.customercare",
            "display_name": "ABC Bank Customer Care",
            "username": "abcbank.customercare",
            "bio": "Contact customer care for urgent assistance with payment verification and pending transactions. WhatsApp helpline available.",
            "profile_image_url": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=180",
            "followers": 3450,
            "following": 12,
            "detected_time": now - timedelta(hours=18)
        },
        {
            "asset_type": "app",
            "platform": "Google Play",
            "store": "Google Play",
            "url": "https://play.google.com/store/apps/details?id=com.fake.abcbank",
            "app_name": "ABC Bank Support & Quick Loan",
            "developer": "Unknown Apps Ltd",
            "publisher": "Unknown Apps Ltd",
            "package_id": "com.fake.abcbank",
            "description": "Access fast mobile support for ABC Bank accounts. Enter login credentials and verify account to receive pre-approved cashback rewards.",
            "app_icon_url": "https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=180",
            "rating": 2.1,
            "downloads": "5,000+",
            "detected_time": now - timedelta(hours=36)
        },
        {
            "asset_type": "social",
            "platform": "X",
            "url": "https://x.com/abcbnak_rewards",
            "display_name": "ABCBnak Loyalty Rewards",
            "username": "@abcbnak_rewards",
            "bio": "Special anniversary promotion for ABC Bank cardholders. Claim reward and double deposit bonus! Click link to claim prize.",
            "profile_image_url": "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=180",
            "followers": 890,
            "following": 5,
            "detected_time": now - timedelta(days=2)
        }
    ]

    brand_for_engine = {
        "name": brand_doc["name"],
        "brand_aliases": brand_doc["brand_aliases"],
        "brand_keywords": brand_doc["brand_keywords"],
        "logo_url": brand_doc["logo_url"],
        "website": brand_doc["website"],
        "description": brand_doc["description"]
    }

    created_threats = []
    for cand in suspicious_candidates:
        detection = await run_multi_signal_detection(
            brand=brand_for_engine,
            official_assets=official_assets,
            candidate_data=cand,
            asset_type=cand["asset_type"]
        )

        threat_doc = {
            "brand_id": brand_id,
            "title": f"Impersonation: {cand.get('display_name') or cand.get('app_name')}",
            "threat_type": detection["threat_type"],
            "asset_type": cand["asset_type"],
            "platform": cand["platform"],
            "url": cand["url"],
            "account_or_app_name": cand.get("display_name") or cand.get("app_name"),
            "username_or_package": cand.get("username") or cand.get("package_id"),
            "developer_name": cand.get("developer"),
            "profile_or_icon_url": cand.get("profile_image_url") or cand.get("app_icon_url"),
            "bio_or_description": cand.get("bio") or cand.get("description"),
            "risk_score": detection["risk_score"],
            "risk_level": detection["risk_level"],
            "customer_impact_score": detection["customer_impact_score"],
            "confidence": detection["confidence"],
            "status": "NEW",
            "why_flagged": detection["why_flagged"],
            "recommended_action": detection["recommended_action"],
            "detection_factors": detection["detection_factors"],
            "official_comparison": detection["official_comparison"],
            "is_official_safe": detection["is_official_safe"],
            "detected_time": cand["detected_time"],
            "analyst_assigned": "Senior Analyst (SecOps)",
            "notes": [
                {
                    "author": "System",
                    "text": "Detected by automated real-time multi-signal scanner.",
                    "created_at": cand["detected_time"].isoformat()
                }
            ]
        }

        t_res = await db.threats.insert_one(threat_doc)
        threat_doc["_id"] = t_res.inserted_id
        created_threats.append(threat_doc)

    # 4. Trigger Cross-Platform Correlation Engine
    campaigns = await correlate_threats_into_campaigns(db, brand_id)

    # 5. Create Sample Active Investigation for the top threat
    top_threat = created_threats[0]
    inv_doc = {
        "threat_id": str(top_threat["_id"]),
        "brand_id": brand_id,
        "case_number": f"INV-{now.strftime('%Y')}-0842",
        "title": f"Investigation: Customer Support Phishing Syndicate ({top_threat.get('account_or_app_name')})",
        "status": "IN_PROGRESS",
        "analyst": "Senior Threat Analyst (SecOps)",
        "summary": "Coordinated campaign detected across social media and mobile app stores targeting ABC Bank customers with urgent KYC requests and credential-harvesting dialogs.",
        "evidence_items": [
            {"type": "URL", "detail": top_threat.get("url")},
            {"type": "MATCH_CONFIDENCE", "detail": f"{top_threat.get('confidence')}% algorithmic confidence"},
            {"type": "TARGETING_TRIGGER", "detail": "Solicits OTP and KYC credentials via direct message"}
        ],
        "recommended_actions": [
            "Submit takedown request to Meta Trust & Safety for immediate profile suspension",
            "Publish proactive fraud advisory notice to legitimate ABC Bank mobile banking users",
            "Correlate IP infrastructure with registrar domain abuse desk"
        ],
        "timeline": [
            {"time": (now - timedelta(hours=4)).isoformat(), "event": "Threat discovered by BrandShield crawler"},
            {"time": (now - timedelta(hours=3)).isoformat(), "event": "Multi-signal risk score calculated (92/100 CRITICAL)"},
            {"time": (now - timedelta(hours=2)).isoformat(), "event": "Assigned to Security Operations analyst"},
            {"time": (now - timedelta(hours=1)).isoformat(), "event": "Cross-platform campaign correlation established with Facebook and Google Play threats"}
        ],
        "created_at": now - timedelta(hours=2)
    }
    await db.investigations.insert_one(inv_doc)

    # 6. Create Alerts
    alerts = [
        {
            "brand_id": brand_id,
            "threat_id": str(top_threat["_id"]),
            "title": "Critical Impersonation Detected",
            "message": "Instagram account @abcbank_support is actively posing as ABC Bank customer support.",
            "severity": "CRITICAL",
            "category": "SOCIAL_IMPERSONATION",
            "is_read": False,
            "created_at": now - timedelta(hours=4)
        },
        {
            "brand_id": brand_id,
            "threat_id": str(created_threats[2]["_id"]),
            "title": "Suspicious Mobile App Published",
            "message": "Google Play app 'ABC Bank Support & Quick Loan' published by unauthorized developer 'Unknown Apps Ltd'.",
            "severity": "CRITICAL",
            "category": "APP_SPOOFING",
            "is_read": False,
            "created_at": now - timedelta(hours=36)
        },
        {
            "brand_id": brand_id,
            "threat_id": str(created_threats[1]["_id"]),
            "title": "Coordinated Multi-Platform Campaign",
            "message": "ABC Bank Customer Support Impersonation Campaign identified across 3 platforms.",
            "severity": "HIGH",
            "category": "CAMPAIGN_DETECTED",
            "is_read": False,
            "created_at": now - timedelta(hours=1)
        }
    ]
    await db.alerts.insert_many(alerts)

    return {
        "status": "success",
        "brand_id": brand_id,
        "brand_name": brand_doc["name"],
        "official_assets_count": len(official_assets),
        "threats_count": len(created_threats),
        "campaigns_count": len(campaigns),
        "alerts_count": len(alerts)
    }
