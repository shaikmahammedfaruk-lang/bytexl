import React from 'react';
import { Search, ShieldCheck, Copy, Sparkles, Activity, AlertCircle } from 'lucide-react';
import PlatformSelector from './PlatformSelector';

export default function AccountVerificationForm({
  platform,
  setPlatform,
  accountIdentifier,
  setAccountIdentifier,
  onVerify,
  onAnalyzeDuplicates,
  loading,
  selectedBrand,
  quickPresets = []
}) {
  const brandName = selectedBrand?.name || 'Brand';

  const getPlaceholder = () => {
    switch (platform) {
      case 'Instagram':
        return 'Enter Instagram handle or URL (e.g. @blackberrysmenswear or https://instagram.com/blackberrysmenswear)...';
      case 'Facebook':
        return 'Enter Facebook Page URL or vanity handle (e.g. https://www.facebook.com/BlackberrysMenswear)...';
      case 'X':
        return 'Enter X (Twitter) handle or URL (e.g. @Blackberrys or https://x.com/Blackberrys)...';
      case 'LinkedIn':
        return 'Enter LinkedIn Company URL or vanity name (e.g. https://www.linkedin.com/company/blackberrys)...';
      default:
        return 'Enter social profile URL or account handle...';
    }
  };

  return (
    <div className="p-5 rounded-2xl bg-[#0b101e] border border-slate-800/90 shadow-xl space-y-4">
      {/* Platform Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
        <div>
          <span className="text-xs font-bold text-white uppercase tracking-wider block">
            Select Social Platform
          </span>
          <span className="text-[11px] text-slate-400">
            Targeting authenticated registry for: <strong className="text-cyan-400">{brandName}</strong>
          </span>
        </div>
        <PlatformSelector selectedPlatform={platform} onSelectPlatform={setPlatform} />
      </div>

      {/* Quick Test Presets if available */}
      {quickPresets && quickPresets.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap text-[11px]">
          <span className="text-slate-400 font-medium flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-cyan-400" />
            Quick Test Links:
          </span>
          {quickPresets.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setAccountIdentifier(preset.url || preset.handle)}
              className={`px-2.5 py-1 rounded-lg border font-mono transition text-[10px] ${
                preset.isSafe
                  ? 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                  : 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border-rose-500/30'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={onVerify} className="space-y-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5 pointer-events-none" />
          <input
            type="text"
            value={accountIdentifier}
            onChange={(e) => setAccountIdentifier(e.target.value)}
            placeholder={getPlaceholder()}
            disabled={loading}
            className="w-full pl-10 pr-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition shadow-inner font-mono"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
          <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span>Checks official platform badge vs BrandShield forensic likeness baseline.</span>
          </div>

          <div className="flex items-center gap-2">
            {onAnalyzeDuplicates && (
              <button
                type="button"
                onClick={onAnalyzeDuplicates}
                disabled={loading || !accountIdentifier.trim()}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold border border-slate-700 transition active:scale-95 whitespace-nowrap"
              >
                Analyze Duplicate Accounts
              </button>
            )}

            <button
              type="submit"
              disabled={loading || !accountIdentifier.trim()}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-cyan-500/20 transition active:scale-95 flex items-center gap-2 whitespace-nowrap"
            >
              {loading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin text-cyan-200" />
                  <span>Verifying Account...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Verify Account</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
