import re
import logging
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.database import get_db
from app.models.schemas import UniversalScanRequest, SocialScanRequest, AppScanRequest
from app.routes.social import scan_social_profile, detect_social_platform
from app.routes.apps import scan_mobile_app, detect_app_store

logger = logging.getLogger("brandshield.routes.scan_link")
router = APIRouter(prefix="/scan-link", tags=["Universal Link Scanner"])

SOCIAL_DOMAINS = ["instagram.com", "facebook.com", "fb.com", "twitter.com", "x.com", "linkedin.com", "youtube.com", "tiktok.com"]
APP_DOMAINS = ["play.google.com", "apps.apple.com", "itunes.apple.com"]

@router.post("")
async def scan_universal_link(req: UniversalScanRequest):
    """
    Universal link dispatcher:
    Analyzes URL, determines category (Social, Mobile App, or Domain),
    routes through appropriate scanner engine, and returns standardized risk telemetry.
    """
    url = req.url.strip().lower()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    brand_id = req.brand_id
    if not ObjectId.is_valid(brand_id):
        raise HTTPException(status_code=400, detail="Invalid brand ID")

    # 1. Check if App Store
    if any(domain in url for domain in APP_DOMAINS):
        app_req = AppScanRequest(
            brand_id=brand_id,
            url=req.url,
            store=detect_app_store(url)
        )
        result = await scan_mobile_app(app_req)
        result["scanner_used"] = "Mobile App Store Engine"
        result["category"] = "App"
        return result

    # 2. Check if Social Media
    if req.platform or any(domain in url for domain in SOCIAL_DOMAINS):
        soc_req = SocialScanRequest(
            brand_id=brand_id,
            url=req.url,
            platform=req.platform or detect_social_platform(url),
            username=req.username
        )
        result = await scan_social_profile(soc_req)
        result["scanner_used"] = "Social Media Intelligence Engine"
        result["category"] = "Social"
        return result

    # 3. If standard website domain
    soc_req = SocialScanRequest(
        brand_id=brand_id,
        url=req.url,
        platform=req.platform or "External Web",
        username=req.username
    )
    result = await scan_social_profile(soc_req)
    result["scanner_used"] = "Web & Domain Impersonation Engine"
    result["category"] = "Web"
    return result
