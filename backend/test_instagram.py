"""
Test Suite for BrandShield AI Instagram Risk Analyzer & Impersonation Engine
Tests cover:
1. Input sanitization (URLs, @ prefixes, whitespace)
2. Meta API service demo mode & presets
3. Impersonation detection logic & official asset exclusion
4. Multi-signal risk calculation (Verification != Absolute Rule)
5. FastAPI integration endpoints
"""

import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.instagram_service import (
    sanitize_instagram_username,
    is_valid_instagram_username,
    fetch_instagram_profile,
    DEMO_PROFILES
)
from app.services.impersonation_service import calculate_impersonation_metrics
from app.services.instagram_risk_engine import RiskAnalyzer, risk_analyzer

client = TestClient(app)

def test_instagram_username_sanitization():
    assert sanitize_instagram_username("@brand_official") == "brand_official"
    assert sanitize_instagram_username("https://instagram.com/abcbank_official/") == "abcbank_official"
    assert sanitize_instagram_username("http://www.instagram.com/abc_bank_help?igsh=123") == "abc_bank_help"
    assert sanitize_instagram_username("  @MyBrand_Support/  ") == "mybrand_support"
    assert is_valid_instagram_username("valid_user.123") is True
    assert is_valid_instagram_username("invalid user with spaces") is False

async def test_demo_profile_presets():
    # 1. Official/Low Risk Preset
    p1 = await fetch_instagram_profile("abcbank_official")
    assert p1["username"] == "abcbank_official"
    assert p1["is_verified"] is True
    assert p1["followers_count"] == 284000
    assert p1["is_demo_data"] is True

    # 2. Medium Risk Look-alike Preset
    p2 = await fetch_instagram_profile("abc_bank_help")
    assert p2["username"] == "abc_bank_help"
    assert p2["is_verified"] is False
    assert p2["followers_count"] == 1820

    # 3. High Risk Impersonator Preset
    p3 = await fetch_instagram_profile("abc_bank_support_official")
    assert p3["username"] == "abc_bank_support_official"
    assert p3["is_verified"] is False
    assert "URGENT" in (p3["biography"] or "")

def test_impersonation_service_lookalike():
    brand = {
        "id": "brand-123",
        "name": "ABC Bank",
        "official_handles": ["abcbank", "abcbank_official"]
    }
    official_assets = [
        {"name": "Official Instagram", "identifier": "abcbank_official", "type": "social_account", "url": "https://instagram.com/abcbank_official"}
    ]

    # Look-alike test
    metrics_suspicious = calculate_impersonation_metrics(
        username="abc_bank_help",
        display_name="ABC Bank Help & Support",
        brand=brand,
        official_assets=official_assets
    )
    assert metrics_suspicious["is_official_asset"] is False
    assert metrics_suspicious["impersonation_risk_score"] > 50

    # Official asset exclusion test
    metrics_official = calculate_impersonation_metrics(
        username="abcbank_official",
        display_name="ABC Bank Official",
        brand=brand,
        official_assets=official_assets
    )
    assert metrics_official["is_official_asset"] is True
    assert metrics_official["impersonation_risk_score"] == 0.0

def test_risk_engine_verification_not_absolute():
    """
    Requirement Check:
    The system must NOT assume:
    Verified account = safe
    Unverified account = fake
    Verification status must be only ONE risk signal.
    """
    analyzer = RiskAnalyzer()
    brand = {
        "id": "brand-test",
        "name": "ABC Bank",
        "website": "abcbank.example"
    }

    # 1. Unverified account with benign/unrelated name and no brand impersonation
    benign_profile = {
        "username": "daily_cooking_recipes",
        "display_name": "Daily Cooking",
        "biography": "Homemade artisan breads and healthy breakfast recipes.",
        "followers_count": 8500,
        "following_count": 320,
        "media_count": 210,
        "is_verified": False,
        "website": "https://myfoodblog.example"
    }
    benign_result = analyzer.analyze(benign_profile, brand=brand)
    # Even though unverified, score must remain LOW (< 30) because there's no impersonation
    assert benign_result["level"] == "LOW"
    assert benign_result["score"] < 30

    # 2. Verified account but exhibits high-risk brand impersonation keywords & phishing link
    verified_phishing_profile = {
        "username": "abc_bank_security_alerts",
        "display_name": "ABC Bank Alert Support",
        "biography": "Urgent notification! Suspended account detected. Verify KYC and OTP credentials now at link below.",
        "followers_count": 1500,
        "following_count": 80,
        "media_count": 5,
        "is_verified": True,  # VERIFIED!
        "website": "http://bit.ly/fake-bank-auth"
    }
    phishing_result = analyzer.analyze(verified_phishing_profile, brand=brand)
    # Even though verified, risk score must be elevated (HIGH or CRITICAL) due to severe phishing & lookalike signals
    assert phishing_result["score"] >= 50
    assert any("Customer Phishing Intent" in s["name"] for s in phishing_result["signals"])

def test_official_asset_exclusion_zero_risk():
    analyzer = RiskAnalyzer()
    brand = {
        "id": "brand-abc",
        "name": "ABC Bank",
        "website": "abcbank.example"
    }
    official_assets = [
        {"name": "ABC Bank IG", "identifier": "abcbank_official", "type": "social_account"}
    ]
    official_profile = {
        "username": "abcbank_official",
        "display_name": "ABC Bank Official",
        "biography": "Official Instagram account of ABC Bank.",
        "is_verified": True,
        "followers_count": 284000,
        "following_count": 142,
        "media_count": 890,
        "website": "https://abcbank.example"
    }
    result = analyzer.analyze(official_profile, brand=brand, official_assets=official_assets)
    assert result["is_official_brand_asset"] is True
    assert result["score"] == 0
    assert result["level"] == "LOW"
    assert "official verified asset registry" in result["explanation"]

def test_api_analyze_endpoint():
    # Test valid analysis
    payload = {
        "username": "abc_bank_help"
    }
    response = client.post("/api/instagram/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "profile" in data
    assert "risk" in data
    assert "signals" in data
    assert "recommendations" in data
    assert 0 <= data["risk"]["score"] <= 100
    assert data["risk"]["level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

def test_api_analyze_empty_username_validation():
    response = client.post("/api/instagram/analyze", json={"username": "   "})
    assert response.status_code in [400, 422]

def test_api_history_endpoint():
    response = client.get("/api/instagram/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_api_investigate_endpoint():
    # 1. Analyze profile
    analysis_res = client.post("/api/instagram/analyze", json={"username": "abc_bank_support_official"})
    assert analysis_res.status_code == 200
    analysis_id = analysis_res.json()["analysis_id"]

    # 2. Escalate to formal investigation
    inv_res = client.post("/api/instagram/investigate", json={
        "analysis_id": analysis_id,
        "analyst_name": "SecOps Lead"
    })
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert "id" in inv_data
    assert "case_number" in inv_data
    assert "evidence_items" in inv_data
    assert inv_data["analyst"] == "SecOps Lead"

def test_duplicate_account_detection_and_original_suggestion():
    # 1. Analyze duplicate account @alluarjun_online
    dup_res = client.post("/api/instagram/analyze", json={"username": "alluarjun_online"})
    assert dup_res.status_code == 200
    dup_data = dup_res.json()

    assert dup_data["risk"]["score"] >= 80, f"Expected escalated risk score >= 80, got {dup_data['risk']['score']}"
    assert dup_data["risk"]["level"] == "CRITICAL"
    assert dup_data["primary_threat"] == "Duplicate Impersonation Account"
    
    suggested = dup_data.get("suggested_original_account")
    assert suggested is not None, "suggested_original_account should not be None"
    assert suggested["is_duplicate"] is True
    assert suggested["is_authentic_original"] is False
    assert suggested["original_username"] == "alluarjunonline"
    assert suggested["original_is_verified"] is True
    assert suggested["similarity_pct"] >= 95.0
    assert len(suggested["duplicate_tactics"]) > 0

    # 2. Analyze authentic original account @alluarjunonline
    orig_res = client.post("/api/instagram/analyze", json={"username": "alluarjunonline"})
    assert orig_res.status_code == 200
    orig_data = orig_res.json()

    assert orig_data["risk"]["score"] <= 5, f"Expected authentic account risk score <= 5, got {orig_data['risk']['score']}"
    assert orig_data["risk"]["level"] == "LOW"
    
    orig_suggested = orig_data.get("suggested_original_account")
    assert orig_suggested is not None
    assert orig_suggested["is_authentic_original"] is True
    assert orig_suggested["is_duplicate"] is False
    assert orig_suggested["original_username"] == "alluarjunonline"

def test_all_verified_accounts_are_originals_and_fakes_suggest_original():
    """
    User Requirement:
    'i want all verify accounts it is original accounts but any similar fake account to risk factor detect and original account suggest'
    """
    pairs = [
        # (Verified Authentic Account, Fake Duplicate Account)
        ("alluarjunonline", "alluarjun_online"),
        ("alluarjunonline", "alluarjun_official"),
        ("virat.kohli", "virat_kohli"),
        ("apple", "apple_support")
    ]

    for verified_handle, fake_handle in pairs:
        # 1. Test Verified Authentic Original Account
        v_res = client.post("/api/instagram/analyze", json={"username": verified_handle})
        assert v_res.status_code == 200
        v_data = v_res.json()
        assert v_data["risk"]["score"] <= 5, f"Verified account @{verified_handle} should have minimal risk, got {v_data['risk']['score']}"
        assert v_data["risk"]["level"] == "LOW"
        v_sug = v_data.get("suggested_original_account")
        assert v_sug is not None
        assert v_sug["is_authentic_original"] is True, f"@{verified_handle} must be identified as authentic original"
        assert v_sug["is_duplicate"] is False

        # 2. Test Similar Fake Duplicate Account
        f_res = client.post("/api/instagram/analyze", json={"username": fake_handle})
        assert f_res.status_code == 200
        f_data = f_res.json()
        assert f_data["risk"]["score"] >= 80, f"Fake account @{fake_handle} must have escalated risk >= 80, got {f_data['risk']['score']}"
        assert f_data["risk"]["level"] == "CRITICAL"
        f_sug = f_data.get("suggested_original_account")
        assert f_sug is not None
        assert f_sug["is_duplicate"] is True, f"Fake account @{fake_handle} must be detected as duplicate"
        assert f_sug["original_username"] == verified_handle, f"Expected suggested original @{verified_handle}, got @{f_sug['original_username']}"

if __name__ == "__main__":
    print("Testing username sanitization...")
    test_instagram_username_sanitization()
    print("Testing impersonation look-alike & official asset detection...")
    test_impersonation_service_lookalike()
    print("Testing verification is not absolute rule (Verified != Safe, Unverified != Fake)...")
    test_risk_engine_verification_not_absolute()
    print("Testing official asset exclusion rule (0 risk score)...")
    test_official_asset_exclusion_zero_risk()
    print("Testing async profile fetching & demo presets...")
    asyncio.run(test_demo_profile_presets())
    print("Testing FastAPI endpoints (/api/instagram/analyze, /api/instagram/history, /api/instagram/investigate)...")
    test_api_analyze_endpoint()
    test_api_analyze_empty_username_validation()
    test_api_history_endpoint()
    test_api_investigate_endpoint()
    print("Testing duplicate account detection and original account suggestion...")
    test_duplicate_account_detection_and_original_suggestion()
    print("Testing all verified accounts are originals and similar fakes have escalated risk + suggest original...")
    test_all_verified_accounts_are_originals_and_fakes_suggest_original()
    print("\n>>> ALL 10 TEST SUITES PASSED FLAWLESSLY! <<<")
