import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Search,
  Layers,
  Sparkles,
  AlertTriangle,
  History,
  Copy,
  ArrowRight
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { verifyAccount, getScanHistory } from '../services/api';
import AccountVerificationForm from '../components/AccountVerificationForm';
import AccountResultCard from '../components/AccountResultCard';
import RiskScoreCard from '../components/RiskScoreCard';

export default function MultiPlatformVerificationPage() {
  const navigate = useNavigate();
  const { selectedBrand, openEvidenceModal } = useBrand();

  const [platform, setPlatform] = useState('Facebook');
  const [accountIdentifier, setAccountIdentifier] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [recentScans, setRecentScans] = useState([]);

  // Generate dynamic test presets based on active brand & chosen platform
  const brandName = selectedBrand?.name || 'Brand';
  const isBlackberrys = brandName.toLowerCase().includes('blackberry');
  const isAmazon = brandName.toLowerCase().includes('amazon') || brandName.toLowerCase().includes('amzone');

  const getQuickPresets = () => {
    if (isBlackberrys) {
      switch (platform) {
        case 'Facebook':
          return [
            { label: 'Official Facebook (Safe)', url: 'https://www.facebook.com/BlackberrysMenswear/', isSafe: true },
            { label: 'Fake Customer Care Page', url: 'https://www.facebook.com/blackberrys_customer_care_online/', isSafe: false }
          ];
        case 'X':
          return [
            { label: 'Official X (Safe)', url: 'https://x.com/Blackberrys', isSafe: true },
            { label: 'Fake Care Handle (@Blackberrys_care)', url: 'https://x.com/Blackberrys_care', isSafe: false }
          ];
        case 'LinkedIn':
          return [
            { label: 'Official LinkedIn (Safe)', url: 'https://www.linkedin.com/company/blackberrys/', isSafe: true },
            { label: 'Fake Recruitment Page', url: 'https://www.linkedin.com/company/blackberrys-careers-recruitment/', isSafe: false }
          ];
        default: // Instagram
          return [
            { label: 'Official IG (Safe)', url: 'https://instagram.com/blackberrysmenswear', isSafe: true },
            { label: 'Fake Support (@blackberrys_support)', url: 'https://instagram.com/blackberrys_support_care', isSafe: false }
          ];
      }
    } else if (isAmazon) {
      switch (platform) {
        case 'Facebook':
          return [
            { label: 'Official Facebook (Safe)', url: 'https://www.facebook.com/Amazon/', isSafe: true },
            { label: 'Fake Helpdesk Page', url: 'https://www.facebook.com/amazon_order_refund_support/', isSafe: false }
          ];
        case 'X':
          return [
            { label: 'Official X (Safe)', url: 'https://x.com/amazon', isSafe: true },
            { label: 'Fake Support Handle', url: 'https://x.com/amazon_help_desk_24x7', isSafe: false }
          ];
        case 'LinkedIn':
          return [
            { label: 'Official LinkedIn (Safe)', url: 'https://www.linkedin.com/company/amazon/', isSafe: true },
            { label: 'Fake HR Agency', url: 'https://www.linkedin.com/company/amazon-remote-jobs-hiring/', isSafe: false }
          ];
        default:
          return [
            { label: 'Official IG (Safe)', url: 'https://instagram.com/amazon', isSafe: true },
            { label: 'Fake IG (@amazon_support)', url: 'https://instagram.com/amazon_support_service', isSafe: false }
          ];
      }
    }

    return [
      { label: `Official ${brandName}`, url: `https://${platform.toLowerCase()}.com/${brandName.toLowerCase().replace(/\s+/g, '')}`, isSafe: true },
      { label: `Fake ${brandName} Support`, url: `https://${platform.toLowerCase()}.com/${brandName.toLowerCase().replace(/\s+/g, '')}_support`, isSafe: false }
    ];
  };

  const fetchRecentScans = async () => {
    try {
      const res = await getScanHistory({ brand_id: selectedBrand?.id, limit: 5 });
      setRecentScans(res.data || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchRecentScans();
  }, [selectedBrand]);

  const handleVerify = async (e) => {
    if (e) e.preventDefault();
    if (!accountIdentifier.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await verifyAccount({
        platform,
        account_identifier: accountIdentifier.trim(),
        brand_id: selectedBrand?.id,
        brand_name: selectedBrand?.name
      });
      setResult(res.data);
      fetchRecentScans();
    } catch (err) {
      setError(err.response?.data?.detail || 'Account verification failed. Please check the identifier.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeDuplicates = () => {
    navigate('/duplicate-detection', {
      state: {
        platform,
        referenceUrl: accountIdentifier.trim()
      }
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            Multi-Platform Account Verification
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Verify official identity badges, check identity consistency, and audit impersonation risks across Instagram, Facebook, X, and LinkedIn.
          </p>
        </div>

        <button
          onClick={() => navigate('/duplicate-detection')}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center gap-2 transition active:scale-95"
        >
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>Duplicate Detection Scanner &rarr;</span>
        </button>
      </div>

      {/* Verification Input Card */}
      <AccountVerificationForm
        platform={platform}
        setPlatform={setPlatform}
        accountIdentifier={accountIdentifier}
        setAccountIdentifier={setAccountIdentifier}
        onVerify={handleVerify}
        onAnalyzeDuplicates={handleAnalyzeDuplicates}
        loading={loading}
        selectedBrand={selectedBrand}
        quickPresets={getQuickPresets()}
      />

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5 animate-fade-in">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AccountResultCard
                profile={result.profile}
                identityConsistency={result.identity_consistency}
                timestamp={result.timestamp}
              />
            </div>

            <div className="lg:col-span-1">
              <RiskScoreCard
                risk={result.risk}
                onEscalate={() => openEvidenceModal(result.scan_id)}
                onTakedown={() => openEvidenceModal(result.scan_id)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Recent Scans Section */}
      {recentScans && recentScans.length > 0 && !result && (
        <div className="p-5 rounded-2xl bg-[#0b101e] border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <History className="w-4 h-4 text-cyan-400" />
              Recent Verification Audits
            </span>
            <button
              onClick={() => navigate('/scan-history')}
              className="text-xs text-cyan-400 hover:underline font-semibold"
            >
              View Full History &rarr;
            </button>
          </div>

          <div className="divide-y divide-slate-800/80">
            {recentScans.map((scan) => (
              <div
                key={scan.id}
                onClick={() => {
                  setPlatform(scan.platform);
                  setAccountIdentifier(scan.profile_url || scan.username);
                }}
                className="py-2.5 flex items-center justify-between text-xs hover:bg-slate-900/50 px-2 rounded-lg cursor-pointer transition"
              >
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                  <span className="font-semibold text-white">{scan.display_name}</span>
                  <span className="font-mono text-slate-400 text-[11px]">{scan.username}</span>
                  <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-slate-800 text-slate-300">
                    {scan.platform}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    scan.risk_category === 'Critical Risk' ? 'bg-rose-500/20 text-rose-400' :
                    scan.risk_category === 'High Risk' ? 'bg-orange-500/20 text-orange-400' :
                    scan.risk_category === 'Medium Risk' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    {scan.risk_category}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {new Date(scan.scanned_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
