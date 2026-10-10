import re

# High-risk customer targeting patterns classified by risk category
TARGETING_PATTERNS = {
    "CREDENTIAL_THEFT": {
        "weight": 35,
        "category": "Credential Theft & Account Takeover",
        "patterns": [
            r"\bsend\s+otp\b",
            r"\bshare\s+otp\b",
            r"\benter\s+pin\b",
            r"\bpassword\s+reset\b",
            r"\blogin\s+credentials\b",
            r"\bverify\s+login\b",
            r"\bsecurity\s+code\b",
            r"\bcvv\b",
            r"\bcard\s+expiry\b",
            r"\bauth\s+code\b",
            r"\b2fa\s+code\b",
            r"\botp\s+credentials\b",
            r"\botp\b",
            r"\bcredentials\b"
        ]
    },
    "KYC_FRAUD": {
        "weight": 30,
        "category": "KYC & Identity Harvesting",
        "patterns": [
            r"\bupdate\s+kyc\b",
            r"\bverify\s+kyc\b",
            r"\bkyc\s+verification\b",
            r"\bcomplete\s+kyc\b",
            r"\bverify\s+account\b",
            r"\bunblock\s+account\b",
            r"\baccount\s+suspended\b",
            r"\bsuspended\s+account\b",
            r"\baccount\s+blocked\b",
            r"\bblocked\s+account\b",
            r"\bverify\s+pan\b",
            r"\bidentity\s+verification\b",
            r"\bupload\s+id\b",
            r"\bkyc\b"
        ]
    },
    "SUPPORT_IMPERSONATION": {
        "weight": 25,
        "category": "Fake Customer Support",
        "patterns": [
            r"\bcontact\s+customer\s+care\b",
            r"\bcustomer\s+support\b",
            r"\bcall\s+helpline\b",
            r"\btoll\s*free\s+number\b",
            r"\bwhatsapp\s+support\b",
            r"\btelegram\s+support\b",
            r"\bhelpdesk\b",
            r"\bofficial\s+support\b",
            r"\b24/7\s+support\b",
            r"\b24x7\s+help\b",
            r"\binstant\s+resolution\b"
        ]
    },
    "FINANCIAL_SCAM": {
        "weight": 30,
        "category": "Payment & Financial Scams",
        "patterns": [
            r"\bclaim\s+reward\b",
            r"\bclaim\s+cashback\b",
            r"\bclaim\s+bonus\b",
            r"\bpayment\s+verification\b",
            r"\brefund\s+processing\b",
            r"\bwire\s+transfer\b",
            r"\bfree\s+voucher\b",
            r"\blottery\s+winner\b",
            r"\bclaim\s+prize\b",
            r"\binvestment\s+return\b",
            r"\bdouble\s+deposit\b"
        ]
    }
}

def analyze_customer_targeting(text: str) -> dict:
    """
    Scans bio, description, posts, or developer notes for deceptive customer-targeting language.
    Returns targeted categories, detected phrases, and customer impact score components.
    """
    if not text:
        return {
            "is_customer_targeting": False,
            "targeting_score": 0.0,
            "detected_phrases": [],
            "categories_triggered": [],
            "urgency_level": "LOW",
            "potential_impacts": []
        }

    clean_text = text.lower()
    detected_phrases = []
    categories_triggered = set()
    total_impact_score = 15.0  # Baseline customer confusion for impersonation
    potential_impacts = ["Customer Confusion", "Reputation Damage"]

    for cat_key, config in TARGETING_PATTERNS.items():
        matched_in_cat = []
        for pat in config["patterns"]:
            matches = re.findall(pat, clean_text)
            if matches:
                matched_in_cat.extend(matches)
                detected_phrases.extend(matches)
        
        if matched_in_cat:
            categories_triggered.add(config["category"])
            total_impact_score += config["weight"]
            
            if cat_key == "CREDENTIAL_THEFT":
                potential_impacts.append("Credential Theft")
                potential_impacts.append("Account Takeover")
            elif cat_key == "KYC_FRAUD":
                potential_impacts.append("Identity Theft (KYC Harvesting)")
            elif cat_key == "SUPPORT_IMPERSONATION":
                potential_impacts.append("Social Engineering Support Fraud")
            elif cat_key == "FINANCIAL_SCAM":
                potential_impacts.append("Financial Loss / Unauthorized Payment")

    is_targeting = len(detected_phrases) > 0
    final_score = min(98.0, total_impact_score) if is_targeting else 20.0
    
    if final_score >= 80:
        urgency = "CRITICAL"
    elif final_score >= 50:
        urgency = "HIGH"
    elif final_score >= 30:
        urgency = "MEDIUM"
    else:
        urgency = "LOW"

    return {
        "is_customer_targeting": is_targeting,
        "targeting_score": round(final_score, 1),
        "detected_phrases": list(set(detected_phrases)),
        "categories_triggered": list(categories_triggered),
        "urgency_level": urgency,
        "potential_impacts": list(set(potential_impacts))
    }
