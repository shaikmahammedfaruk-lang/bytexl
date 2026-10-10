import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  X,
  Link2,
  Search,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  FileText,
  Activity,
  ChevronRight,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { scanUniversalLink } from '../services/api';
import { formatScore } from '../utils/formatters';

const SCAN_STEPS = [
  "Collecting asset metadata & platform signatures...",
  "Analyzing tokens, look-alike patterns & homoglyphs...",
  "Comparing with Official Asset Registry (Exclusion Rule)...",
  "Evaluating multi-signal scores & customer impact...",
  "Scan Completed"
];

export default function ScanModal() {
  const navigate = useNavigate();
  const {
    isScanModalOpen,
    setIsScanModalOpen,
    scanModalInitialUrl,
    selectedBrand,
    openEvidenceModal,
    refreshBrands
  } = useBrand();

  const [url, setUrl] = useState('');
  const [platform, setPlatform] = useState('AUTO');
  const [username, setUsername] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isScanModalOpen) {
      setUrl(scanModalInitialUrl || '');
      setPlatform('AUTO');
      setUsername('');
      setScanResult(null);
      setError('');
      setIsScanning(false);
      setCurrentStep(0);
    }
  }, [isScanModalOpen, scanModalInitialUrl]);

  if (!isScanModalOpen) return null;

  const handleStartScan = async (e) => {
    e?.preventDefault();
    if (!url || !url.trim()) {
      setError('Please provide a valid URL to analyze.');
      return;
    }
    if (!selectedBrand) {
      setError('No active brand selected.');
      return;
    }

    setError('');
    setIsScanning(true);
    setScanResult(null);
    setCurrentStep(0);

    // Realistic multi-stage stepper progression for high-end real-time feel
    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < 3) return prev + 1;
        return prev;
      });
    }, 450);

    try {
      const res = await scanUniversalLink({
        brand_id: selectedBrand.id,
        url: url.trim(),
        platform: platform !== 'AUTO' ? platform : undefined,
        username: username.trim() || undefined
      });

      clearInterval(stepInterval);
      setCurrentStep(4);
      setTimeout(() => {
        setIsScanning(false);
        setScanResult(res.data);
        refreshBrands();
      }, 500);
    } catch (err) {
      clearInterval(stepInterval);
      setIsScanning(false);
      setError(err.response?.data?.detail || 'Scan failed. Please verify the URL and backend connection.');
    }
  };

  const handleQuickPreset = (presetUrl) => {
    setUrl(presetUrl);
  };

  const isSafe = scanResult?.status === 'safe' || scanResult?.detection?.is_official_safe;
  const threatData = scanResult?.threat || (scanResult?.detection ? {
    risk_score: scanResult.detection.risk_score,
    risk_level: scanResult.detection.risk_level,
    customer_impact_score: scanResult.detection.customer_impact_score,
    confidence: scanResult.detection.confidence,
    threat_type: scanResult.detection.threat_type,
    why_flagged: scanResult.detection.why_flagged,
    detection_factors: scanResult.detection.detection_factors,
    official_comparison: scanResult.detection.official_comparison
  } : null);

  const brandName = selectedBrand?.name || 'Brand';
  const brandLower = brandName.toLowerCase();
  const isBlackberrys = brandLower.includes('blackberry');
  const isAmazon = brandLower.includes('amazon') || brandLower.includes('amzone');
  const isNike = brandLower.includes('nike');

  const testPresets = isBlackberrys ? [
    { label: 'Official YouTube (Safe)', url: 'https://www.youtube.com/@BlackberrysMenswear', type: 'safe' },
    { label: 'Fake YouTube (@BlackberrysMenswearr)', url: 'https://www.youtube.com/@BlackberrysMenswearr', type: 'danger' },
    { label: 'Official Instagram (Safe)', url: 'https://instagram.com/blackberrysmenswear', type: 'safe' },
    { label: 'Fake Support Account', url: 'https://instagram.com/blackberrys_support_care', type: 'danger' },
  ] : isAmazon ? [
    { label: 'Official Amazon App (Safe)', url: 'https://play.google.com/store/apps/details?id=in.amazon.mShop.android.shopping', type: 'safe' },
    { label: 'Fake Amazon Pay App', url: 'https://play.google.com/store/apps/details?id=com.fake.amazonpay', type: 'warning' },
    { label: 'Official Instagram (Safe)', url: 'https://instagram.com/amazon', type: 'safe' },
    { label: 'Fake Support Handle', url: 'https://instagram.com/amazon_helpdesk_support', type: 'danger' },
  ] : isNike ? [
    { label: 'Official Instagram (Safe)', url: 'https://instagram.com/nike', type: 'safe' },
    { label: 'Fake Nike Support', url: 'https://instagram.com/nike_customer_support', type: 'danger' },
    { label: 'Fake Nike Store App', url: 'https://play.google.com/store/apps/details?id=com.fake.nikestore', type: 'warning' },
  ] : [
    { label: `Official ${brandName} Link (Safe)`, url: selectedBrand?.official_instagram_url || `https://instagram.com/${brandLower.replace(/[^a-z0-9]/g, '')}`, type: 'safe' },
    { label: `@${brandLower.replace(/[^a-z0-9]/g, '')}_support (Impersonator)`, url: `https://instagram.com/${brandLower.replace(/[^a-z0-9]/g, '')}_support`, type: 'danger' },
    { label: `Fake ${brandName} App Link`, url: `https://play.google.com/store/apps/details?id=com.fake.${brandLower.replace(/[^a-z0-9]/g, '')}`, type: 'warning' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0b101e] border border-slate-700/80 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Link2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Universal Digital Risk Scanner
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                  Target: {selectedBrand?.name}
                </span>
              </h3>
              <p className="text-[11px] text-slate-400">
                Analyzes Social Media profiles or Mobile App Store links for brand impersonation.
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsScanModalOpen(false)}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 overflow-y-auto">
          {/* Quick presets for winning demo testing */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-cyan-400" />
                Quick Test Links for {brandName}:
              </span>
            </div>
            <div className="flex flex-wrap gap-2 text-[10px]">
              {testPresets.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleQuickPreset(p.url)}
                  className={`px-2.5 py-1 rounded border transition font-medium ${
                    p.type === 'safe'
                      ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                      : p.type === 'danger'
                      ? 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border-rose-500/30'
                      : 'bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border-amber-500/30'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* URL & Platform Input Form */}
          <form onSubmit={handleStartScan} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                  Supported Platform / Store
                </label>
                <select
                  value={platform}
                  onChange={(e) => setPlatform(e.target.value)}
                  disabled={isScanning}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-500"
                >
                  <option value="AUTO">Auto-Detect Platform</option>
                  <option value="Instagram">Instagram</option>
                  <option value="Facebook">Facebook</option>
                  <option value="X">X (Twitter)</option>
                  <option value="LinkedIn">LinkedIn</option>
                  <option value="YouTube">YouTube</option>
                  <option value="TikTok">TikTok</option>
                  <option value="Google Play">Google Play</option>
                  <option value="Apple App Store">Apple App Store</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                  Username / Identifier (Optional)
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="@handle, username, or package"
                  disabled={isScanning}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Paste social profile or app store URL (e.g. https://instagram.com/abcbank_support)..."
                  disabled={isScanning}
                  className="w-full pl-9 pr-4 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>
              <button
                type="submit"
                disabled={isScanning || !url.trim()}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 transition-all flex items-center gap-2 whitespace-nowrap active:scale-95"
              >
                {isScanning ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin text-cyan-200" />
                    <span>Scanning...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    <span>Scan Link</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Stepper Animation */}
          {isScanning && (
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3 animate-fade-in">
              <div className="flex items-center justify-between text-xs font-semibold text-cyan-300">
                <span className="flex items-center gap-2">
                  <Activity className="w-4 h-4 animate-pulse text-cyan-400" />
                  Real-time Multi-Signal Analysis
                </span>
                <span className="font-mono text-[11px] text-slate-400">Step {currentStep + 1} of 5</span>
              </div>
              <div className="space-y-1.5">
                {SCAN_STEPS.map((stepText, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center gap-2 text-[11px] transition-all duration-300 ${
                      idx < currentStep
                        ? 'text-emerald-400 font-medium'
                        : idx === currentStep
                        ? 'text-cyan-300 font-semibold translate-x-1'
                        : 'text-slate-600'
                    }`}
                  >
                    {idx < currentStep ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    ) : idx === currentStep ? (
                      <div className="w-3.5 h-3.5 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin flex-shrink-0" />
                    ) : (
                      <div className="w-3.5 h-3.5 rounded-full bg-slate-800 flex-shrink-0" />
                    )}
                    <span>{stepText}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scan Results Display */}
          {scanResult && threatData && (
            <div className="rounded-xl border p-4 space-y-4 animate-fade-in bg-slate-900/80 border-slate-700/80">
              {/* Top Banner: Safe vs Critical Threat */}
              {isSafe ? (
                <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-3">
                  <ShieldCheck className="w-7 h-7 text-emerald-400 flex-shrink-0" />
                  <div>
                    <h4 className="text-xs font-bold text-emerald-300 uppercase tracking-wider">
                      Verified Official Asset (Exclusion Rule Applied)
                    </h4>
                    <p className="text-[11px] text-slate-300 mt-0.5">
                      {threatData.why_flagged || "This asset matches your official asset registry. Zero threat risk recorded."}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ShieldAlert className="w-8 h-8 text-rose-400 flex-shrink-0 animate-pulse" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500 text-white uppercase tracking-wider">
                          {threatData.risk_level || 'CRITICAL'} THREAT
                        </span>
                        <span className="text-xs font-bold text-white">
                          {threatData.threat_type}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-300 mt-1 line-clamp-2">
                        {threatData.why_flagged}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Unique BrandShield AI 4-Metric Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] font-bold uppercase text-slate-400 block">Threat Risk</span>
                  <div className="text-xl font-black text-rose-400 mt-0.5">
                    {formatScore(threatData.risk_score)}<span className="text-xs font-medium text-slate-500">/100</span>
                  </div>
                  <span className="text-[9px] font-medium text-slate-500">Multi-Signal Composite</span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] font-bold uppercase text-slate-400 block">Customer Impact</span>
                  <div className="text-xl font-black text-amber-400 mt-0.5">
                    {formatScore(threatData.customer_impact_score)}<span className="text-xs font-medium text-slate-500">/100</span>
                  </div>
                  <span className="text-[9px] font-medium text-slate-500">Fraud & Credential Risk</span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] font-bold uppercase text-slate-400 block">Confidence</span>
                  <div className="text-xl font-black text-cyan-400 mt-0.5">
                    {formatScore(threatData.confidence)}%
                  </div>
                  <span className="text-[9px] font-medium text-slate-500">Algorithmic Match</span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                  <span className="text-[10px] font-bold uppercase text-slate-400 block">Official Mismatch</span>
                  <div className="text-xl font-black text-indigo-400 mt-0.5">
                    {isSafe ? '0%' : '100%'}
                  </div>
                  <span className="text-[9px] font-medium text-slate-500">Registry Verification</span>
                </div>
              </div>

              {/* Side-by-Side Comparison Snippet */}
              {threatData.official_comparison && (
                <div className="space-y-2">
                  <h5 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
                    <span>Forensic Profile Comparison</span>
                    <span className="text-[10px] font-normal text-slate-400">Registry Baseline vs Scanned Candidate</span>
                  </h5>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    {/* Official Verified Card */}
                    <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 space-y-2 shadow-sm">
                      <div className="flex items-center justify-between">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          Recommended Legitimate Account
                        </span>
                        <span className="text-[10px] font-mono text-emerald-400 font-semibold">VERIFIED</span>
                      </div>
                      <div className="flex items-center gap-2.5">
                        {threatData.official_comparison.official?.logo ? (
                          <img
                            src={threatData.official_comparison.official.logo}
                            alt="Official"
                            className="w-8 h-8 rounded-lg object-contain bg-slate-900 border border-emerald-500/40 p-0.5 flex-shrink-0"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        ) : (
                          <div className="w-8 h-8 rounded-lg bg-emerald-900/50 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-xs font-bold flex-shrink-0">
                            ✓
                          </div>
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="font-bold text-white text-xs truncate">
                            {threatData.official_comparison.official?.name}
                          </p>
                          <p className="text-[11px] text-emerald-300/80 font-mono truncate">
                            {threatData.official_comparison.official?.username_or_dev || threatData.official_comparison.official?.platform}
                          </p>
                        </div>
                      </div>
                      {threatData.official_comparison.official?.url && (
                        <div className="pt-1.5 border-t border-emerald-500/20">
                          <a
                            href={threatData.official_comparison.official.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-cyan-400 hover:text-cyan-300 text-[11px] font-medium flex items-center gap-1 hover:underline truncate"
                          >
                            <span>Visit Official Channel</span>
                            <ExternalLink className="w-3 h-3 flex-shrink-0" />
                          </a>
                        </div>
                      )}
                    </div>

                    {/* Suspicious Candidate Card */}
                    <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 space-y-2 shadow-sm">
                      <div className="flex items-center justify-between">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 uppercase flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3 text-rose-400" />
                          {isSafe ? 'Scanned Asset (Safe)' : 'Detected Impersonator'}
                        </span>
                        <span className="text-[10px] font-mono text-rose-400 font-semibold">
                          {isSafe ? 'CLEAN' : 'UNAUTHORIZED'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2.5">
                        {threatData.official_comparison.suspicious?.logo ? (
                          <img
                            src={threatData.official_comparison.suspicious.logo}
                            alt="Suspicious"
                            className="w-8 h-8 rounded-lg object-contain bg-slate-900 border border-rose-500/40 p-0.5 flex-shrink-0"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        ) : (
                          <div className="w-8 h-8 rounded-lg bg-rose-900/50 border border-rose-500/30 flex items-center justify-center text-rose-400 text-xs font-bold flex-shrink-0">
                            !
                          </div>
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="font-bold text-white text-xs truncate">
                            {threatData.official_comparison.suspicious?.name}
                          </p>
                          <p className="text-[11px] text-rose-300/80 font-mono truncate">
                            {threatData.official_comparison.suspicious?.username_or_dev || threatData.official_comparison.suspicious?.url}
                          </p>
                        </div>
                      </div>
                      {threatData.official_comparison.suspicious?.url && (
                        <div className="pt-1.5 border-t border-rose-500/20">
                          <span className="text-[11px] font-mono text-slate-400 truncate block">
                            Target: {threatData.official_comparison.suspicious.url}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Forensic Differences / Key Discrepancies */}
                  {threatData.official_comparison.differences?.length > 0 && (
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
                      <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                        Forensic Discrepancy Breakdown:
                      </span>
                      <ul className="space-y-1 text-[11px] text-slate-300">
                        {threatData.official_comparison.differences.map((diff, dIdx) => (
                          <li key={dIdx} className="flex items-start gap-1.5">
                            <span className="text-rose-400 font-bold">•</span>
                            <span>{diff}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-2 border-t border-slate-800 flex items-center justify-end gap-2.5">
                {scanResult.threat?.id && (
                  <>
                    <button
                      onClick={() => {
                        setIsScanModalOpen(false);
                        openEvidenceModal(scanResult.threat.id);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-1.5"
                    >
                      <FileText className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Generate Evidence</span>
                    </button>

                    <button
                      onClick={() => {
                        setIsScanModalOpen(false);
                        navigate(`/threats/${scanResult.threat.id}`);
                      }}
                      className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-cyan-500/20"
                    >
                      <span>Investigate Threat</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </>
                )}
                {isSafe && (
                  <button
                    onClick={() => setIsScanModalOpen(false)}
                    className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
                  >
                    Done
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
