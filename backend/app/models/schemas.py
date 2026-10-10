from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# --- BRAND MODELS ---
class BrandBase(BaseModel):
    name: str = Field(..., example="Nike")
    website: Optional[str] = Field(None, example="https://nike.com")
    industry: Optional[str] = Field("Sportswear & Apparel", example="Sportswear & Apparel")
    description: Optional[str] = Field(None, example="Official commercial brand ground truth.")
    logo_url: Optional[str] = Field(None, example="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200")
    brand_keywords: List[str] = Field(default_factory=list, example=["nike", "swoosh", "just do it"])
    brand_aliases: List[str] = Field(default_factory=list, example=["Nike Inc", "Nike Official"])
    official_instagram_username: Optional[str] = Field(None, example="nike")
    official_instagram_url: Optional[str] = Field(None, example="https://instagram.com/nike")
    official_bio: Optional[str] = Field(None, example="Just Do It. #Nike")
    official_instagram_logo: Optional[str] = None
    official_social_links: List[Any] = Field(default_factory=list)
    official_app_links: List[Any] = Field(default_factory=list)

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    brand_keywords: Optional[List[str]] = None
    brand_aliases: Optional[List[str]] = None
    official_instagram_username: Optional[str] = None
    official_instagram_url: Optional[str] = None
    official_bio: Optional[str] = None
    official_instagram_logo: Optional[str] = None
    official_social_links: Optional[List[Any]] = None
    official_app_links: Optional[List[Any]] = None
    is_archived: Optional[bool] = None

class BrandResponse(BrandBase):
    id: str
    is_archived: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    official_assets_count: int = 0
    active_threats_count: int = 0

# --- OFFICIAL ASSET MODELS ---
class OfficialAssetCreate(BaseModel):
    brand_id: Optional[str] = None
    name: Optional[str] = "Official Asset"
    asset_type: str = Field(..., example="social") # 'social', 'app', 'domain'
    platform: str = Field(..., example="Instagram") # Instagram, Facebook, X, LinkedIn, YouTube, TikTok, Google Play, Apple App Store, Domain
    url: str = Field(..., example="https://instagram.com/abcbank")
    identifier: Optional[str] = Field(None, example="@abcbank")
    developer_name: Optional[str] = Field(None, example="ABC Technologies Ltd")
    package_id: Optional[str] = Field(None, example="com.abcbank.mobile")
    verification_status: str = Field("VERIFIED", example="VERIFIED")

class OfficialAssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    platform: Optional[str] = None
    url: Optional[str] = None
    identifier: Optional[str] = None
    developer_name: Optional[str] = None
    package_id: Optional[str] = None
    verification_status: Optional[str] = None

class OfficialAssetResponse(OfficialAssetCreate):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# --- BRAND WIZARD MULTI-STEP EDIT SCHEMAS ---
class BrandWizardAssetItem(BaseModel):
    id: Optional[str] = None
    asset_type: str = "social"  # 'social', 'app', 'domain'
    platform: Optional[str] = None
    name: Optional[str] = None
    identifier: Optional[str] = None
    url: str
    developer_name: Optional[str] = None
    package_id: Optional[str] = None
    verification_status: str = "VERIFIED"
    is_active: bool = True

class BrandWizardSyncRequest(BaseModel):
    # Step 1: Brand Info
    name: str
    website: Optional[str] = None
    industry: Optional[str] = "Other"
    description: Optional[str] = None
    brand_keywords: List[str] = Field(default_factory=list)
    brand_aliases: List[str] = Field(default_factory=list)

    # Step 2: Logo
    logo_url: Optional[str] = None

    # Step 3, 4, 5: Official Assets
    social_accounts: List[BrandWizardAssetItem] = Field(default_factory=list)
    mobile_apps: List[BrandWizardAssetItem] = Field(default_factory=list)
    domains: List[BrandWizardAssetItem] = Field(default_factory=list)

# --- DETECTION & SCAN REQUESTS ---
class SocialScanRequest(BaseModel):
    brand_id: str
    url: str
    platform: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    followers: Optional[int] = 0
    following: Optional[int] = 0

class AppScanRequest(BaseModel):
    brand_id: str
    url: str
    store: Optional[str] = None # Google Play, Apple App Store
    app_name: Optional[str] = None
    developer: Optional[str] = None
    publisher: Optional[str] = None
    package_id: Optional[str] = None
    description: Optional[str] = None
    app_icon_url: Optional[str] = None
    rating: Optional[float] = 0.0
    downloads: Optional[str] = "0"

class UniversalScanRequest(BaseModel):
    brand_id: str
    url: str
    platform: Optional[str] = None
    username: Optional[str] = None
    simulated_context: Optional[Dict[str, Any]] = None

# --- THREAT MODELS ---
class DetectionFactors(BaseModel):
    name_similarity: float = 0.0
    username_similarity: float = 0.0
    logo_similarity: float = 0.0
    description_similarity: float = 0.0
    brand_keyword_presence: float = 0.0
    official_mismatch: float = 100.0
    developer_mismatch: float = 0.0
    customer_targeting_score: float = 0.0
    lookalike_type: str = "NONE"
    lookalike_explanation: str = ""
    targeting_phrases: List[str] = []

class ComparisonAsset(BaseModel):
    logo: Optional[str] = None
    name: Optional[str] = None
    username_or_dev: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None
    verified: bool = False

class OfficialVsSuspicious(BaseModel):
    official: ComparisonAsset
    suspicious: ComparisonAsset
    differences: List[str] = []

class ThreatBase(BaseModel):
    brand_id: str
    title: str
    threat_type: str
    asset_type: str # 'social' or 'app'
    platform: str
    url: str
    account_or_app_name: str
    username_or_package: Optional[str] = None
    developer_name: Optional[str] = None
    profile_or_icon_url: Optional[str] = None
    bio_or_description: Optional[str] = None
    risk_score: float
    risk_level: str # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    customer_impact_score: float
    confidence: float
    status: str = "NEW" # 'NEW', 'UNDER_INVESTIGATION', 'REVIEWED', 'RESOLVED', 'LEGITIMATE_FALSE_POSITIVE'
    why_flagged: str
    recommended_action: str
    detection_factors: DetectionFactors
    official_comparison: OfficialVsSuspicious
    is_official_safe: bool = False
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    analyst_assigned: Optional[str] = "Unassigned"
    notes: List[Dict[str, Any]] = []

class ThreatResponse(ThreatBase):
    id: str
    detected_time: datetime
    updated_at: Optional[datetime] = None

class ThreatUpdate(BaseModel):
    status: Optional[str] = None
    analyst_assigned: Optional[str] = None
    note: Optional[str] = None
    account_or_app_name: Optional[str] = None
    username_or_package: Optional[str] = None
    developer_name: Optional[str] = None
    bio_or_description: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    customer_impact_score: Optional[float] = None
    why_flagged: Optional[str] = None
    recommended_action: Optional[str] = None

# --- CAMPAIGN MODELS ---
class CampaignResponse(BaseModel):
    id: str
    brand_id: str
    name: str
    campaign_risk: float
    status: str # 'ACTIVE', 'MONITORING', 'MITIGATED'
    platforms: List[str]
    threat_count: int
    related_threat_ids: List[str]
    detected_time: datetime
    description: str
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

# --- INVESTIGATION MODELS ---
class InvestigationCreate(BaseModel):
    threat_id: str
    title: Optional[str] = None
    analyst: Optional[str] = "Security Operations Team"

class InvestigationResponse(BaseModel):
    id: str
    threat_id: str
    brand_id: str
    case_number: str
    title: str
    status: str # 'OPEN', 'IN_PROGRESS', 'ESCALATED', 'CLOSED'
    analyst: str
    summary: str
    evidence_items: List[Dict[str, Any]]
    recommended_actions: List[str]
    timeline: List[Dict[str, Any]]
    created_at: datetime

# --- ALERT MODELS ---
class AlertResponse(BaseModel):
    id: str
    brand_id: Optional[str] = None
    threat_id: Optional[str] = None
    title: str
    message: Optional[str] = None
    details: Optional[str] = None
    severity: str = "HIGH" # 'CRITICAL', 'HIGH', 'MEDIUM', 'INFO'
    category: Optional[str] = "BRAND_IMPERSONATION" # 'SOCIAL_IMPERSONATION', 'APP_SPOOFING', 'CAMPAIGN_DETECTED', 'ASSET_VERIFICATION'
    is_read: bool = False
    created_at: Optional[datetime] = None

# --- INSTAGRAM RISK ANALYZER MODELS ---
class InstagramProfileSnapshot(BaseModel):
    username: str
    display_name: Optional[str] = None
    account_type: Optional[str] = "BUSINESS"
    is_verified: bool = False
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    media_count: Optional[int] = None
    biography: Optional[str] = None
    profile_picture_url: Optional[str] = None
    website: Optional[str] = None
    is_demo_data: bool = False

class InstagramRiskSignal(BaseModel):
    name: str
    weight: float = 0.0 # Configured weight percentage (e.g. 20.0, 15.0)
    score: float # points contributed (0 to max weight)
    similarity_percentage: float = 0.0 # 0.0 - 100.0%
    severity: str # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'POSITIVE', 'NEUTRAL'
    reason: str
    evidence: Optional[str] = None

class InstagramRiskScore(BaseModel):
    score: int # 0 to 100
    level: str # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    confidence: float # 0.0 to 1.0

class WhyFlaggedItem(BaseModel):
    severity_dot: str # 'RED', 'ORANGE', 'GREEN'
    text: str

class EvidenceCard(BaseModel):
    id: str
    category: str # 'LOGO', 'BIO', 'CONTENT', 'DOMAIN', 'BEHAVIOR', 'USERNAME'
    title: str
    description: str
    severity: str # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    badge: str

class ComparisonAccountData(BaseModel):
    username: str
    display_name: str
    logo_url: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    followers_count: Optional[int] = None
    is_verified: bool = False
    sample_posts: List[str] = []

class ComparisonMetrics(BaseModel):
    username_match_pct: float = 0.0
    logo_match_pct: float = 0.0
    bio_match_pct: float = 0.0
    content_match_pct: float = 0.0
    domain_mismatch: bool = False
    domain_mismatch_warning: Optional[str] = None

class OfficialVsSuspiciousComparison(BaseModel):
    official: ComparisonAccountData
    suspicious: ComparisonAccountData
    metrics: ComparisonMetrics

class ProfileRiskMatrix(BaseModel):
    tier: str = "LOW"  # 'CRITICAL', 'MEDIUM', 'LOW', 'EVALUATED'
    followers_eval: str = ""
    posts_eval: str = ""
    followings_eval: str = ""
    bio_eval: str = ""
    bio_words_count: int = 0
    rule_matched: str = ""
    summary: str = ""

class SuggestedOriginalAccount(BaseModel):
    is_duplicate: bool = False
    is_authentic_original: bool = False
    original_username: Optional[str] = None
    original_url: Optional[str] = None
    original_name: Optional[str] = None
    original_is_verified: bool = True
    original_followers_formatted: Optional[str] = None
    original_followers_count: Optional[int] = None
    original_avatar: Optional[str] = None
    similarity_pct: float = 0.0
    duplicate_tactics: List[str] = []
    risk_escalation_reason: Optional[str] = None
    recommendation: Optional[str] = None

class InstagramAnalyzeRequest(BaseModel):
    username: str
    brand_id: Optional[str] = None
    force_demo: Optional[bool] = None
    is_verified: Optional[bool] = None  # Auditor verification override or auto-detect

class InstagramAnalyzeResponse(BaseModel):
    success: bool
    profile: Optional[InstagramProfileSnapshot] = None
    risk: Optional[InstagramRiskScore] = None
    primary_threat: str = "Brand Impersonation"
    secondary_threat: Optional[str] = None
    confidence_pct: int = 94
    signals: List[InstagramRiskSignal] = []
    why_flagged: List[WhyFlaggedItem] = []
    evidence_cards: List[EvidenceCard] = []
    official_comparison: Optional[OfficialVsSuspiciousComparison] = None
    profile_risk_matrix: Optional[ProfileRiskMatrix] = None
    suggested_original_account: Optional[SuggestedOriginalAccount] = None
    recommendations: List[str] = []
    explanation: str = ""
    brand_name: Optional[str] = None
    analysis_id: Optional[str] = None
    is_official_brand_asset: bool = False
    created_at: Optional[datetime] = None

class InstagramInvestigationRequest(BaseModel):
    analysis_id: str
    analyst_name: Optional[str] = "SecOps Risk Analyst"

# --- BRAND & WEBSITE AUTHENTICITY VERIFICATION MODELS ---
class BrandProfileVerificationRequest(BaseModel):
    brand_name: str = Field(..., example="Nike")
    official_website: Optional[str] = Field(None, example="https://nike.com")
    official_domain: Optional[str] = Field(None, example="nike.com")
    instagram: Optional[str] = Field(None, example="@nike")
    facebook: Optional[str] = Field(None, example="https://facebook.com/nike")
    twitter: Optional[str] = Field(None, example="@nike")
    linkedin: Optional[str] = Field(None, example="https://linkedin.com/company/nike")
    youtube: Optional[str] = Field(None, example="https://youtube.com/nike")
    app_store_url: Optional[str] = Field(None, example="https://apps.apple.com/app/nike/id1095459556")
    play_store_url: Optional[str] = Field(None, example="https://play.google.com/store/apps/details?id=com.nike.omega")
    official_logo: Optional[str] = Field(None, example="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200")
    brand_images: Optional[List[str]] = Field(default_factory=list)
    brand_description: Optional[str] = Field(None, example="Just Do It. Official brand profile.")
    official_contact_email: Optional[str] = Field(None, example="privacy@nike.com")
    brand_id: Optional[str] = None

class WebsiteAuthenticityRequest(BaseModel):
    url: str = Field(..., example="https://nike-support-login.com")
    brand_id: Optional[str] = None
    brand_name: Optional[str] = None

class ImageAuthenticityRequest(BaseModel):
    candidate_image_url: Optional[str] = None
    candidate_logo_url: Optional[str] = None
    official_image_url: Optional[str] = None
    official_logo_url: Optional[str] = None
    brand_id: Optional[str] = None

class AuthenticityVerdictOverrideRequest(BaseModel):
    analysis_id: Optional[str] = None
    candidate_domain: str
    override_verdict: str  # "Possible Legitimate", "Needs Review", "Likely Impersonation", "Confirmed Threat"
    notes: Optional[str] = None
    analyst: Optional[str] = "SecOps Risk Analyst"

class AuthenticityInvestigationRequest(BaseModel):
    candidate_domain: str
    brand_name: Optional[str] = "Brand"
    risk_score: int = 85
    details: Optional[str] = None
    analyst: Optional[str] = "SecOps Risk Analyst"

# --- MULTI-PLATFORM SOCIAL VERIFICATION & DUPLICATE DETECTION MODELS ---

class AccountVerificationRequest(BaseModel):
    platform: str = Field(..., example="Facebook") # "Instagram", "Facebook", "X", "LinkedIn"
    account_identifier: str = Field(..., example="https://www.facebook.com/BlackberrysMenswear")
    brand_id: Optional[str] = None
    brand_name: Optional[str] = None
    force_live_api: Optional[bool] = False

class AccountProfileData(BaseModel):
    platform: str
    profile_url: str
    username: str
    display_name: str
    official_platform_verification: str = Field(..., example="Verified") # "Verified", "Not Verified", "Unknown"
    verification_badge_type: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    media_or_posts_count: Optional[int] = 0
    account_created_date: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    page_category: Optional[str] = None
    data_source: str = "Authorized Platform API"
    api_limitations_notice: Optional[str] = None

class IdentityConsistencyIndicators(BaseModel):
    exact_name_match: bool = False
    lookalike_detected: bool = False
    brand_keyword_presence: bool = False
    official_registry_mismatch: bool = False
    suspicious_contact_patterns: bool = False
    phishing_indicators: List[str] = []

class RiskAssessmentResult(BaseModel):
    risk_score: float = 0.0 # 0.00 to 100.00
    risk_category: str = "Normal" # "Normal", "Low Risk", "Medium Risk", "High Risk", "Critical Risk", "Insufficient Data"
    confidence_score: float = 90.0
    reasons: List[str] = []
    evidence_findings: List[Dict[str, Any]] = []
    recommended_action: str = "Continue routine monitoring."
    official_comparison: Optional[Dict[str, Any]] = None

class AccountVerificationResponse(BaseModel):
    scan_id: str
    platform: str
    scanned_identifier: str
    profile: AccountProfileData
    identity_consistency: IdentityConsistencyIndicators
    risk: RiskAssessmentResult
    brand_id: Optional[str] = None
    brand_name: Optional[str] = None
    timestamp: datetime

class DuplicateMatch(BaseModel):
    id: str
    platform: str
    username: str
    display_name: str
    profile_url: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    followers_count: Optional[int] = 0
    similarity_score: float = 0.0
    confidence_level: str = "HIGH"
    lookalike_type: str = "EXACT_OR_VARIANT"
    evidence: List[str] = []
    impersonation_risk: str = "HIGH"
    is_official: bool = False
    created_at: Optional[Any] = None

class DuplicateDetectionRequest(BaseModel):
    brand_id: Optional[str] = None
    platform: Optional[str] = "ALL" # "ALL", "Instagram", "Facebook", "X", "LinkedIn"
    reference_account_url: Optional[str] = None
    target_keyword: Optional[str] = None
    threshold: Optional[float] = 40.0

class DuplicateDetectionResponse(BaseModel):
    reference_account: Optional[Dict[str, Any]] = None
    target_brand: str
    platform_scanned: str
    total_candidates_analyzed: int
    duplicates_found: int
    matches: List[DuplicateMatch]
    api_limitations_notice: str
    timestamp: datetime

class ScanHistoryItem(BaseModel):
    id: str
    brand_id: Optional[str] = None
    brand_name: Optional[str] = None
    platform: str
    username: str
    display_name: str
    profile_url: str
    official_platform_verification: str
    risk_score: float
    risk_category: str
    primary_threat: Optional[str] = None
    data_source: str
    scanned_at: datetime

class ReportsSummaryResponse(BaseModel):
    brand_name: str
    total_scans: int
    platform_breakdown: Dict[str, int]
    risk_distribution: Dict[str, int]
    active_threats_count: int
    duplicates_detected_count: int
    official_assets_protected: int
    compliance_score: float
    recent_threats: List[Dict[str, Any]]
    generated_at: datetime


