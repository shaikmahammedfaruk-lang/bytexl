import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Layers,
  Search,
  Sliders,
  Sparkles,
  AlertTriangle,
  Activity,
  ShieldCheck,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { scanDuplicates } from '../services/api';
import PlatformSelector from '../components/PlatformSelector';
import DuplicateMatchList from '../components/DuplicateMatchList';
import { formatScore } from '../utils/formatters';

export default function DuplicateDetectionPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { selectedBrand, openEvidenceModal } = useBrand();

  const [platform, setPlatform] = useState(location.state?.platform || 'ALL');
  const [referenceUrl, setReferenceUrl] = useState(location.state?.referenceUrl || '');
  const [threshold, setThreshold] = useState(40);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const brandName = selectedBrand?.name || 'Brand';

  const handleScan = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await scanDuplicates({
        brand_id: selectedBrand?.id,
        platform: platform,
        reference_account_url: referenceUrl.trim() || undefined,
        target_keyword: brandName,
        threshold: Number(threshold)
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Duplicate discovery scan failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (location.state?.referenceUrl) {
      handleScan();
    }
  }, []);

  const handleInvestigateMatch = (match) => {
    navigate('/multi-platform-verification', {
      state: {
        platform: match.platform,
        accountIdentifier: match.profile_url || match.username
      }
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            Duplicate & Impersonation Account Detection
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Identify look-alike profiles, brand keyword hijackers, and unauthorized duplicate accounts across social networks.
          </p>
        </div>

        <button
          onClick={() => navigate('/multi-platform-verification')}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center gap-2 transition active:scale-95"
        >
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <span>Account Verification &rarr;</span>
        </button>
      </div>

      {/* Control Card */}
      <div className="p-5 rounded-2xl bg-[#0b101e] border border-slate-800 space-y-4 shadow-xl">
        {/* Platform Selection */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
          <div>
            <span className="text-xs font-bold text-white uppercase tracking-wider block">
              Platform Scope
            </span>
            <span className="text-[11px] text-slate-400">
              Scanning for: <strong className="text-cyan-400">{brandName}</strong>
            </span>
          </div>
          <PlatformSelector selectedPlatform={platform} onSelectPlatform={setPlatform} includeAll={true} />
        </div>

        {/* Input Form & Threshold Slider */}
        <form onSubmit={handleScan} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 relative">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                Reference Verified Account or Protected Trademark URL
              </label>
              <div className="relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5 pointer-events-none" />
                <input
                  type="text"
                  value={referenceUrl}
                  onChange={(e) => setReferenceUrl(e.target.value)}
                  placeholder={`e.g. https://www.facebook.com/${brandName.toLowerCase().replace(/\s+/g, '')} or leave blank for default brand baseline`}
                  disabled={loading}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-300 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                  Similarity Threshold
                </span>
                <span className="font-mono font-bold text-cyan-400 text-xs">
                  {formatScore(threshold)}%
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="90"
                step="5"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                className="w-full accent-cyan-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
              />
              <span className="text-[10px] text-slate-500 block">
                Lowering threshold catches broader phonetic lookalikes.
              </span>
            </div>
          </div>

          {/* Trigger Button */}
          <div className="flex justify-end pt-1">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-cyan-500/20 transition active:scale-95 flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin text-cyan-200" />
                  <span>Scanning Platform Directories...</span>
                </>
              ) : (
                <>
                  <Layers className="w-4 h-4" />
                  <span>Run Duplicate Discovery Scan</span>
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

      {/* Results View */}
      {result && (
        <div className="space-y-4 animate-fade-in">
          <DuplicateMatchList
            matches={result.matches}
            apiNotice={result.api_limitations_notice}
            referenceAccount={result.reference_account}
            onInvestigateMatch={handleInvestigateMatch}
          />
        </div>
      )}
    </div>
  );
}
