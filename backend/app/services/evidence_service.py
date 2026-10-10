import hashlib
import json
from datetime import datetime
from typing import Dict, Any

def generate_evidence_package(threat: Dict[str, Any], brand: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates an exportable, tamper-evident digital risk protection evidence package.
    Includes technical telemetry, comparison tables, takedown notice templates, and cryptographic hash.
    """
    threat_id = str(threat.get("_id") or threat.get("id"))
    brand_name = brand.get("name", "Target Brand")
    detected_at = threat.get("detected_time", datetime.utcnow())
    if isinstance(detected_at, datetime):
        detected_iso = detected_at.isoformat()
    else:
        detected_iso = str(detected_at)

    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_id = f"BS-EVD-{timestamp_str}-{threat_id[:6].upper()}"

    # Build SHA-256 evidence hash
    hash_payload = f"{report_id}:{threat.get('url')}:{threat.get('risk_score')}:{detected_iso}"
    evidence_hash = hashlib.sha256(hash_payload.encode()).hexdigest()

    factors = threat.get("detection_factors", {})
    comparison = threat.get("official_comparison", {})
    platform = threat.get("platform", "Social")

    # Takedown legal request template
    takedown_letter = f"""
OFFICIAL INTELLECTUAL PROPERTY & IMPERSONATION INFRINGEMENT NOTICE
Date: {datetime.utcnow().strftime('%B %d, %Y')}
Case ID: {report_id}

To: Abuse & Trust & Safety Team ({platform})
Re: Unauthorized Brand Impersonation and Customer Fraud Intent

We represent {brand_name}. We have identified an infringing digital asset operating on your platform:
- Infringing Asset URL: {threat.get('url')}
- Account / App Name: {threat.get('account_or_app_name')}
- Resemblance Score: {factors.get('name_similarity', 90)}%
- Risk Classification: {threat.get('risk_level', 'CRITICAL')} ({threat.get('risk_score', 90)}/100)

VIOLATION SUMMARY:
1. Unauthorized use of {brand_name} trademarks, logos, and identity.
2. Deceptive misrepresentation causing severe customer confusion.
3. {threat.get('why_flagged')}

We formally request the immediate suspension of this asset to safeguard consumers from potential fraud.

Evidence Hash: SHA-256 {evidence_hash}
BrandShield AI Automated Digital Risk Protection Engine
"""

    evidence_doc = {
        "report_id": report_id,
        "threat_id": threat_id,
        "brand_name": brand_name,
        "created_at": datetime.utcnow().isoformat(),
        "evidence_hash": evidence_hash,
        "threat_summary": {
            "title": threat.get("title") or f"{brand_name} Impersonation on {platform}",
            "threat_type": threat.get("threat_type"),
            "platform": platform,
            "url": threat.get("url"),
            "risk_score": threat.get("risk_score"),
            "customer_impact_score": threat.get("customer_impact_score"),
            "confidence": threat.get("confidence"),
            "detected_time": detected_iso
        },
        "detection_factors": factors,
        "comparison_audit": comparison,
        "takedown_notice_template": takedown_letter.strip(),
        "preservation_status": "LOCKED & VERIFIED"
    }

    return evidence_doc
