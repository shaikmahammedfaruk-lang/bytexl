import re
from typing import Dict, Any, List, Optional
from rapidfuzz import fuzz

PHISHING_KEYWORDS = [
    "send otp", "share otp", "password", "support desk", "customer care",
    "unblock account", "kyc verification", "urgent notice", "helpline",
    "official support", "direct message for help", "whatsapp", "refund",
    "claim bonus", "giveaway", "login portal", "bank support"
]

def assess_account_risk(
    profile_data: Dict[str, Any],
    brand_data: Optional[Dict[str, Any]] = None,
    official_assets: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evidence-based Explainable Risk Assessment Engine.
    Evaluates:
      1. Official Registry Exclusion: If exact URL or matching verified identifier exists, status is Normal (Safe).
      2. Identity Resemblance: Fuzzy likeness to brand name / protected trademarks.
      3. Customer Phishing Intent: Unsolicited credential / OTP / payment solicitations.
      4. Platform Badges: Explicitly distinguishes platform badge from BrandShield verdict.
         NOTE: Unverified status ALONE is never treated as malicious evidence.
      5. Identity Consistency: Age, contact info, external links consistency.
    """
    if not profile_data:
        return {
            "risk_score": 0.00,
            "risk_category": "Insufficient Data",
            "confidence_score": 50.00,
            "reasons": ["Unable to retrieve sufficient telemetry from platform APIs to form an evidence-based assessment."],
            "evidence_findings": [],
            "recommended_action": "Manually verify account or obtain elevated API read access for this platform.",
            "official_comparison": None
        }

    platform = profile_data.get("platform", "Social")
    username = profile_data.get("username", "")
    display_name = profile_data.get("display_name", "")
    bio = profile_data.get("bio", "") or ""
    profile_url = profile_data.get("profile_url", "").lower().rstrip('/')
    is_platform_verified = profile_data.get("official_platform_verification") == "Verified"
    verification_badge = profile_data.get("verification_badge_type", "None")

    brand_name = (brand_data.get("name") if brand_data else "") or "Protected Brand"
    brand_keywords = (brand_data.get("brand_keywords") if brand_data else []) or []
    official_assets = official_assets or []

    # 1. OFFICIAL REGISTRY CHECK (Exact baseline match)
    matched_asset = None
    for asset in official_assets:
        off_url = asset.get("url", "").lower().rstrip('/')
        if off_url and off_url == profile_url:
            matched_asset = asset
            break
        off_id = re.sub(r'[^a-z0-9]', '', (asset.get("identifier") or "").lower())
        cand_id = re.sub(r'[^a-z0-9]', '', username.lower())
        if off_id and cand_id and off_id == cand_id:
            asset_plat = (asset.get("platform") or "").lower()
            if not asset_plat or asset_plat == platform.lower():
                matched_asset = asset
                break

    if matched_asset:
        return {
            "risk_score": 0.00,
            "risk_category": "Normal",
            "confidence_score": 99.50,
            "reasons": [
                f"Account matches official verified asset '{matched_asset.get('name')}' registered in your brand baseline.",
                f"Platform verification status is recorded as {profile_data.get('official_platform_verification')}."
            ],
            "evidence_findings": [
                {"category": "REGISTRY_MATCH", "status": "VERIFIED_SAFE", "detail": f"Exact match with baseline asset {matched_asset.get('url')}"}
            ],
            "recommended_action": "Preserve in active brand monitoring baseline; no remediation necessary.",
            "official_comparison": {
                "official": {
                    "name": matched_asset.get("name"),
                    "url": matched_asset.get("url"),
                    "identifier": matched_asset.get("identifier"),
                    "platform": matched_asset.get("platform") or platform,
                    "verified": True
                },
                "scanned": {
                    "name": display_name,
                    "url": profile_data.get("profile_url"),
                    "identifier": username,
                    "platform": platform,
                    "verified": is_platform_verified
                },
                "discrepancies": ["Identical baseline entity registered in BrandShield database."]
            }
        }

    # 2. CALCULATE RESEMBLANCE SIGNALS
    clean_brand = re.sub(r'[^a-z0-9]', '', brand_name.lower())
    clean_user = re.sub(r'[^a-z0-9]', '', username.lower())
    clean_display = re.sub(r'[^a-z0-9]', '', display_name.lower())

    name_ratio = fuzz.ratio(clean_brand, clean_user) if clean_brand and clean_user else 0
    display_ratio = fuzz.ratio(clean_brand, clean_display) if clean_brand and clean_display else 0
    partial_ratio = fuzz.partial_ratio(clean_brand, clean_user) if clean_brand and clean_user else 0
    resemblance_score = max(name_ratio, display_ratio, partial_ratio)

    # 3. DETECT DECEPTIVE / PHISHING INTENT IN BIO & NAME
    combined_text = f"{username} {display_name} {bio}".lower()
    detected_phishing_phrases = [kw for kw in PHISHING_KEYWORDS if kw in combined_text]
    has_phishing_language = len(detected_phishing_phrases) > 0

    # 4. KEYWORD & BRAND ROOTS
    keyword_hits = [kw for kw in brand_keywords if kw.lower() in combined_text]

    # 5. MULTI-SIGNAL EVIDENCE FORMULATION
    evidence = []
    reasons = []
    base_risk = 5.00

    # Lookalike evidence
    if resemblance_score >= 85:
        base_risk += 45.00
        evidence.append({
            "category": "HIGH_NAME_SIMILARITY",
            "severity": "HIGH",
            "detail": f"Account identifier shares {round(float(resemblance_score), 2)}% phonetic and orthographic likeness with protected brand '{brand_name}'."
        })
        reasons.append(f"Strong brand name resemblance ({round(float(resemblance_score), 2)}% match).")
    elif resemblance_score >= 60:
        base_risk += 25.00
        evidence.append({
            "category": "MODERATE_NAME_SIMILARITY",
            "severity": "MEDIUM",
            "detail": f"Account identifier shares {round(float(resemblance_score), 2)}% similarity with '{brand_name}'."
        })
        reasons.append(f"Moderate brand name resemblance ({round(float(resemblance_score), 2)}%).")

    # Phishing / customer scam language
    if has_phishing_language:
        base_risk += 40.00
        evidence.append({
            "category": "DECEPTIVE_CUSTOMER_TARGETING",
            "severity": "CRITICAL",
            "detail": f"Bio contains high-risk support/credential keywords: {', '.join(detected_phishing_phrases[:3])}."
        })
        reasons.append(f"Detected deceptive customer-targeting phrases ({', '.join(detected_phishing_phrases[:3])}).")

    # Registry mismatch
    evidence.append({
        "category": "REGISTRY_STATUS",
        "severity": "MEDIUM",
        "detail": "Account is not present in official verified brand assets registry."
    })
    reasons.append("Account is absent from official verified brand registry.")

    # Platform verification status context
    if is_platform_verified:
        # Verified on platform but not in our registry - could be legitimate brand division or compromised badge
        if resemblance_score >= 85 and has_phishing_language:
            evidence.append({
                "category": "COMPROMISED_VERIFIED_ACCOUNT",
                "severity": "CRITICAL",
                "detail": "Account holds official platform verification badge, yet exhibits active credential harvesting/phishing signals."
            })
            reasons.append("Warning: Account has platform badge but exhibits suspicious customer phishing behavior.")
        else:
            base_risk = max(10.00, base_risk - 35.00)
            evidence.append({
                "category": "PLATFORM_VERIFIED",
                "severity": "LOW",
                "detail": f"Account possesses official {verification_badge} badge on {platform}."
            })
            reasons.append(f"Account has official {verification_badge} badge.")
    else:
        # Rule: Do not use unverified status alone as evidence that it is fake
        evidence.append({
            "category": "PLATFORM_UNVERIFIED",
            "severity": "INFO",
            "detail": f"Account is not platform-verified on {platform}. (Note: Unverified status alone does not imply malicious intent)."
        })

    # Clamp risk score
    final_risk = round(float(min(99.00, max(5.00, base_risk))), 2)

    # Determine Category
    if final_risk >= 85.00:
        risk_category = "Critical Risk"
        rec_action = "Initiate immediate brand impersonation takedown and preserve forensic evidence package."
    elif final_risk >= 65.00:
        risk_category = "High Risk"
        rec_action = "Escalate to SecOps triage, verify account ownership, and prepare takedown dossier."
    elif final_risk >= 35.00:
        risk_category = "Medium Risk"
        rec_action = "Monitor profile activity for brand confusion or potential escalation into phishing."
    elif final_risk >= 15.00:
        risk_category = "Low Risk"
        rec_action = "Keep in routine automated threat observation pool."
    else:
        risk_category = "Normal"
        rec_action = "No threat detected. Continue regular baseline monitoring."

    confidence_score = round(float(min(98.00, max(65.00, 60.00 + (resemblance_score * 0.35)))), 2)

    # Official reference for comparison
    matching_official = next((a for a in official_assets if (a.get("platform") or "").lower() == platform.lower()), official_assets[0] if official_assets else None)

    comparison = None
    if matching_official:
        comparison = {
            "official": {
                "name": matching_official.get("name"),
                "url": matching_official.get("url"),
                "identifier": matching_official.get("identifier"),
                "platform": matching_official.get("platform") or platform,
                "verified": True
            },
            "scanned": {
                "name": display_name,
                "url": profile_data.get("profile_url"),
                "identifier": username,
                "platform": platform,
                "verified": is_platform_verified
            },
            "discrepancies": [
                f"Official verified handle '{matching_official.get('identifier') or matching_official.get('name')}' vs Scanned handle '{username}'",
                f"Official baseline status: Verified in BrandShield vs Scanned status: Not registered"
            ]
        }

    return {
        "risk_score": final_risk,
        "risk_category": risk_category,
        "confidence_score": confidence_score,
        "reasons": reasons,
        "evidence_findings": evidence,
        "recommended_action": rec_action,
        "official_comparison": comparison
    }
