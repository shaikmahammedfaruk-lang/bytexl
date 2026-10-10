import re
import logging
from typing import Dict, Any, List, Optional
from rapidfuzz import fuzz
from app.utils.lookalike import analyze_lookalike, normalize_text
from app.services.detection_engine import clean_handle, check_official_registry_match

logger = logging.getLogger("brandshield.impersonation_service")

def calculate_impersonation_metrics(
    username: str,
    display_name: Optional[str],
    brand: Dict[str, Any],
    official_assets: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Computes fine-grained impersonation metrics comparing an Instagram handle/profile
    against a protected brand entity.
    Returns:
      - username_similarity_score (0-100)
      - brand_similarity_score (0-100)
      - impersonation_risk_score (0-100)
      - lookalike_details (swap, added words, homoglyphs)
      - is_official_asset (bool)
      - official_match_details (dict if matched)
    """
    clean_user = clean_handle(username)
    brand_name = brand.get("name", "")
    brand_aliases = brand.get("brand_aliases", [])
    official_assets = official_assets or []

    # 1. Check if this username is directly registered as an official brand asset
    official_match = None
    for asset in official_assets:
        off_handle = clean_handle(asset.get("identifier", ""))
        off_url = asset.get("url", "").lower().rstrip("/")
        if off_handle and clean_user in [off_handle, f"{off_handle}_official", f"{off_handle}official"]:
            official_match = asset
            break
        if off_url and off_url.endswith(f"/{clean_user}"):
            official_match = asset
            break

    if official_match:
        return {
            "is_official_asset": True,
            "official_asset_name": official_match.get("name"),
            "username_similarity_score": 100.0,
            "brand_similarity_score": 100.0,
            "impersonation_risk_score": 0.0,
            "impersonation_level": "OFFICIAL_SAFE",
            "lookalike_details": {
                "lookalike_type": "OFFICIAL_REGISTERED",
                "explanation": f"Matches verified official brand asset '{official_match.get('name')}' in registry."
            }
        }

    # 2. Look-alike analysis for username against brand name and aliases
    lookalike_user = analyze_lookalike(clean_user, brand_name, brand_aliases)
    username_sim = lookalike_user.get("similarity_score", 0.0)

    # 3. Look-alike analysis for display name against brand name
    brand_sim = 0.0
    if display_name:
        lookalike_display = analyze_lookalike(display_name, brand_name, brand_aliases)
        brand_sim = lookalike_display.get("similarity_score", 0.0)
    else:
        brand_sim = username_sim

    # 4. Keyword presence in username (e.g. 'support', 'help', 'bank', 'official', 'service')
    added_words = lookalike_user.get("added_words", [])
    has_deceptive_suffix = len(added_words) > 0

    # 5. Composite impersonation risk score
    # High username similarity + deceptive suffix = very high impersonation likelihood
    base_impersonation = (username_sim * 0.6) + (brand_sim * 0.4)
    if has_deceptive_suffix and username_sim >= 60:
        base_impersonation = max(base_impersonation, 85.0)

    imp_score = round(min(100.0, max(0.0, base_impersonation)), 1)

    if imp_score >= 80:
        imp_level = "CRITICAL"
    elif imp_score >= 60:
        imp_level = "HIGH"
    elif imp_score >= 30:
        imp_level = "MEDIUM"
    else:
        imp_level = "LOW"

    return {
        "is_official_asset": False,
        "official_asset_name": None,
        "username_similarity_score": round(username_sim, 1),
        "brand_similarity_score": round(brand_sim, 1),
        "impersonation_risk_score": imp_score,
        "impersonation_level": imp_level,
        "lookalike_details": lookalike_user,
        "added_deceptive_words": added_words
    }
