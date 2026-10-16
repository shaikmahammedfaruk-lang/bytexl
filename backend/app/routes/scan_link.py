# import re
# import logging
# from fastapi import APIRouter, HTTPException
# from bson import ObjectId
# from app.database import get_db
# from app.models.schemas import UniversalScanRequest, SocialScanRequest, AppScanRequest
# from app.routes.social import scan_social_profile, detect_social_platform
# from app.routes.apps import scan_mobile_app, detect_app_store

# logger = logging.getLogger("brandshield.routes.scan_link")
# router = APIRouter(prefix="/scan-link", tags=["Universal Link Scanner"])

# SOCIAL_DOMAINS = ["instagram.com", "facebook.com", "fb.com", "twitter.com", "x.com", "linkedin.com", "youtube.com", "tiktok.com"]
# APP_DOMAINS = ["play.google.com", "apps.apple.com", "itunes.apple.com"]

# @router.post("")
# async def scan_universal_link(req: UniversalScanRequest):
#     """
#     Universal link dispatcher:
#     Analyzes URL, determines category (Social, Mobile App, or Domain),
#     routes through appropriate scanner engine, and returns standardized risk telemetry.
#     """
#     url = req.url.strip().lower()
#     if not url.startswith(("http://", "https://")):
#         url = "https://" + url

#     brand_id = req.brand_id
#     if not ObjectId.is_valid(brand_id):
#         raise HTTPException(status_code=400, detail="Invalid brand ID")

#     # 1. Check if App Store
#     if any(domain in url for domain in APP_DOMAINS):
#         app_req = AppScanRequest(
#             brand_id=brand_id,
#             url=req.url,
#             store=detect_app_store(url)
#         )
#         result = await scan_mobile_app(app_req)
#         result["scanner_used"] = "Mobile App Store Engine"
#         result["category"] = "App"
#         return result

#     # 2. Check if Social Media
#     if req.platform or any(domain in url for domain in SOCIAL_DOMAINS):
#         soc_req = SocialScanRequest(
#             brand_id=brand_id,
#             url=req.url,
#             platform=req.platform or detect_social_platform(url),
#             username=req.username
#         )
#         result = await scan_social_profile(soc_req)
#         result["scanner_used"] = "Social Media Intelligence Engine"
#         result["category"] = "Social"
#         return result

#     # 3. If standard website domain
#     soc_req = SocialScanRequest(
#         brand_id=brand_id,
#         url=req.url,
#         platform=req.platform or "External Web",
#         username=req.username
#     )
#     result = await scan_social_profile(soc_req)
#     result["scanner_used"] = "Web & Domain Impersonation Engine"
#     result["category"] = "Web"
#     return result




import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import (
    UniversalScanRequest,
    SocialScanRequest,
    AppScanRequest,
)
from app.services.auth_service import require_current_user
from app.routes.social import (
    scan_social_profile,
    detect_social_platform,
)
from app.routes.apps import (
    scan_mobile_app,
    detect_app_store,
)

logger = logging.getLogger("brandshield.routes.scan_link")

router = APIRouter(
    prefix="/scan-link",
    tags=["Universal Link Scanner"],
)

SOCIAL_DOMAINS = {
    "instagram.com",
    "facebook.com",
    "fb.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
}

APP_DOMAINS = {
    "play.google.com",
    "apps.apple.com",
    "itunes.apple.com",
}


def normalize_url(raw_url: str) -> str:
    """Normalize a URL and reject malformed or unsupported schemes."""
    url = raw_url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise HTTPException(status_code=400, detail="Invalid URL")

    return url


def hostname_matches(hostname: str, domains: set[str]) -> bool:
    """Match an exact domain or its subdomain, not a lookalike hostname."""
    hostname = hostname.lower().rstrip(".")

    return any(
        hostname == domain or hostname.endswith("." + domain)
        for domain in domains
    )


@router.post("")
async def scan_universal_link(
    req: UniversalScanRequest,
    current_user: dict = Depends(require_current_user),
):
    """
    Classify a submitted URL and dispatch it to the appropriate scanner.

    The scanner enforces brand ownership before creating or modifying
    threat records. Shared demo brands remain read-only.
    """
    url = normalize_url(req.url)
    hostname = urlparse(url).hostname.lower().rstrip(".")

    # App-store links
    if hostname_matches(hostname, APP_DOMAINS):
        app_req = AppScanRequest(
            brand_id=req.brand_id,
            url=url,
            store=detect_app_store(url),
        )

        # These scanners are called directly, so pass the authenticated
        # user explicitly rather than relying on FastAPI dependency injection.
        result = await scan_mobile_app(
            app_req,
            current_user=current_user,
        )

        result["scanner_used"] = "Mobile App Store Engine"
        result["category"] = "App"
        return result

    # Social media links
    if req.platform or hostname_matches(hostname, SOCIAL_DOMAINS):
        social_req = SocialScanRequest(
            brand_id=req.brand_id,
            url=url,
            platform=req.platform or detect_social_platform(url),
            username=req.username,
        )

        result = await scan_social_profile(
            social_req,
            current_user=current_user,
        )

        result["scanner_used"] = "Social Media Intelligence Engine"
        result["category"] = "Social"
        return result

    # Other websites and domains
    social_req = SocialScanRequest(
        brand_id=req.brand_id,
        url=url,
        platform=req.platform or "External Web",
        username=req.username,
    )

    result = await scan_social_profile(
        social_req,
        current_user=current_user,
    )

    result["scanner_used"] = "Web & Domain Impersonation Engine"
    result["category"] = "Web"
    return result