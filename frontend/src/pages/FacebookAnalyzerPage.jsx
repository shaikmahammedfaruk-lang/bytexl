import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Sparkles,
  ArrowRight,
  Activity,
  Layers,
  ShieldCheck,
  ExternalLink,
  Info
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { analyzeFacebookAccount } from '../services/api';
import { FacebookIcon } from '../components/PlatformSelector';
import AccountResultCard from '../components/AccountResultCard';
import RiskScoreCard from '../components/RiskScoreCard';

export default function FacebookAnalyzerPage() {
  const navigate = useNavigate();
  const { selectedBrand, openEvidenceModal } = useBrand();

  const [inputUrl, setInputUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const brandName = selectedBrand?.name || 'Brand';
  const isBlackberrys = brandName.toLowerCase().includes('blackberry');

  const presets = isBlackberrys ? [
    { label: 'Official Facebook Page (Safe)', url: 'https://www.facebook.com/BlackberrysMenswear/', isSafe: true },
    { label: 'Fake Customer Care Helpdesk', url: 'https://www.facebook.com/blackberrys_customer_care_online/', isSafe: false }
  ] : [
    { label: `Official ${brandName} Page`, url: `https://www.facebook.com/${brandName.toLowerCase().replace(/\s+/g, '')}`, isSafe: true },
    { label: `Fake ${brandName} Support`, url: `https://www.facebook.com/${brandName.toLowerCase().replace(/\s+/g, '')}_support_help`, isSafe: false }
  ];

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!inputUrl.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await analyzeFacebookAccount({
        platform: 'Facebook',
        account_identifier: inputUrl.trim(),
        brand_id: selectedBrand?.id,
        brand_name: brandName
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Facebook analysis failed. Please verify the URL.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FacebookIcon className="w-5 h-5 text-blue-400" />
            Facebook Brand & Page Risk Analyzer
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit Facebook Pages, community accounts, and customer support lookalikes against Meta Graph ground truth.
          </p>
        </div>

        <button
          onClick={() => navigate('/duplicate-detection', { state: { platform: 'Facebook', referenceUrl: inputUrl } })}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center gap-2 transition active:scale-95"
        >
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>Scan Facebook Duplicates &rarr;</span>
        </button>
      </div>

      {/* Input Card */}
      <div className="p-5 rounded-2xl bg-[#0b101e] border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
          <span className="text-slate-400 font-medium flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            Quick Test Links for {brandName}:
          </span>
          <div className="flex items-center gap-2 flex-wrap">
            {presets.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setInputUrl(p.url)}
                className={`px-2.5 py-1 rounded-lg border font-mono text-[10px] transition ${
                  p.isSafe
                    ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    : 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border-rose-500/30'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleAnalyze} className="space-y-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5 pointer-events-none" />
            <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="Paste Facebook Page URL or vanity name (e.g. https://www.facebook.com/BlackberrysMenswear/)..."
              disabled={loading}
              className="w-full pl-10 pr-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-slate-500 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              Meta Graph API telemetry integrated with multi-signal risk rules.
            </span>

            <button
              type="submit"
              disabled={loading || !inputUrl.trim()}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition active:scale-95 flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin text-cyan-200" />
                  <span>Auditing Facebook Page...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Analyze Facebook Page</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5 animate-fade-in">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in">
          <div className="lg:col-span-2">
            <AccountResultCard
              profile={result.profile}
              identityConsistency={{
                exact_name_match: result.profile.username.toLowerCase() === brandName.toLowerCase().replace(/\s+/g, ''),
                lookalike_detected: result.risk.risk_score >= 35.0,
                official_registry_mismatch: result.risk.risk_score > 0,
                suspicious_contact_patterns: (result.profile.bio || '').toLowerCase().includes('otp') || (result.profile.bio || '').toLowerCase().includes('whatsapp')
              }}
              timestamp={result.created_at}
            />
          </div>

          <div className="lg:col-span-1">
            <RiskScoreCard
              risk={result.risk}
              onEscalate={() => openEvidenceModal(result.analysis_id)}
              onTakedown={() => openEvidenceModal(result.analysis_id)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
