import React, { useState } from 'react';
import {
  Settings,
  Sliders,
  Shield,
  Database,
  CheckCircle2,
  RefreshCw,
  Cpu,
  FileCode2,
  Sparkles,
  HelpCircle
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';

export default function SettingsPage() {
  const { selectedBrand } = useBrand();

  const [nameThreshold, setNameThreshold] = useState(70);
  const [logoThreshold, setLogoThreshold] = useState(80);
  const [targetingWeight, setTargetingWeight] = useState(85);
  const [homoglyphsEnabled, setHomoglyphsEnabled] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Settings className="w-5 h-5 text-slate-400" />
          Platform & Detection Engine Configuration
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Tune algorithmic thresholds, look-alike sensitivity, and system connectivity parameters.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Detection Engine Parameters */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                Multi-Signal Detection Weights
              </h3>
              <p className="text-[11px] text-slate-400">Configure sensitivity thresholds for threat flagging</p>
            </div>
            {saved && (
              <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Saved & Synchronized
              </span>
            )}
          </div>

          <form onSubmit={handleSave} className="space-y-4 text-xs">
            {/* Name Similarity Slider */}
            <div className="space-y-1.5 p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="flex justify-between">
                <span className="font-semibold text-slate-200">Look-Alike Name Resemblance Threshold</span>
                <span className="font-mono text-cyan-400 font-bold">{nameThreshold}%</span>
              </div>
              <input
                type="range"
                min="50"
                max="95"
                value={nameThreshold}
                onChange={(e) => setNameThreshold(e.target.value)}
                className="w-full accent-cyan-400"
              />
              <p className="text-[10px] text-slate-500">
                Minimum RapidFuzz and homoglyph score required to flag candidate impersonations.
              </p>
            </div>

            {/* Logo Similarity Slider */}
            <div className="space-y-1.5 p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="flex justify-between">
                <span className="font-semibold text-slate-200">Logo Perceptual Hash (dHash) Sensitivity</span>
                <span className="font-mono text-purple-400 font-bold">{logoThreshold}%</span>
              </div>
              <input
                type="range"
                min="60"
                max="98"
                value={logoThreshold}
                onChange={(e) => setLogoThreshold(e.target.value)}
                className="w-full accent-purple-400"
              />
              <p className="text-[10px] text-slate-500">
                Perceptual difference threshold for comparing suspicious profile avatars with official brand mark.
              </p>
            </div>

            {/* Customer Targeting Sensitivity */}
            <div className="space-y-1.5 p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="flex justify-between">
                <span className="font-semibold text-slate-200">Customer Phishing Language Urgency Weight</span>
                <span className="font-mono text-amber-400 font-bold">{targetingWeight}%</span>
              </div>
              <input
                type="range"
                min="50"
                max="100"
                value={targetingWeight}
                onChange={(e) => setTargetingWeight(e.target.value)}
                className="w-full accent-amber-400"
              />
              <p className="text-[10px] text-slate-500">
                Risk multiplier applied when bio/description contains OTP, KYC, or customer care extraction triggers.
              </p>
            </div>

            {/* Homoglyph and Unicode lookalikes toggle */}
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200 block">Homoglyph & Unicode Squatting Defense</span>
                <span className="text-[10px] text-slate-500">
                  Detects Cyrillic, Greek, and visual confusable characters (e.g. '0' for 'o', 'rn' for 'm').
                </span>
              </div>
              <input
                type="checkbox"
                checked={homoglyphsEnabled}
                onChange={(e) => setHomoglyphsEnabled(e.target.checked)}
                className="w-4 h-4 accent-cyan-400 cursor-pointer"
              />
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20 active:scale-95 transition"
              >
                Apply Engine Settings
              </button>
            </div>
          </form>
        </div>

        {/* System Diagnostics & Backend Architecture */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            DRP Architecture & Diagnostics
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Database Layer</span>
              <span className="font-bold text-emerald-400 flex items-center gap-1 font-mono text-[11px]">
                <CheckCircle2 className="w-3 h-3" /> MongoDB Connected
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Name Match Engine</span>
              <span className="font-bold text-cyan-400 font-mono text-[11px]">RapidFuzz 3.14 (Active)</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Image Hash Engine</span>
              <span className="font-bold text-purple-400 font-mono text-[11px]">Pillow dHash (Active)</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Exclusion Rule Registry</span>
              <span className="font-bold text-emerald-400 font-mono text-[11px]">Enforced (0-Risk Shield)</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Active Brand Target</span>
              <span className="font-bold text-slate-200 font-mono text-[11px] truncate max-w-[130px]">
                {selectedBrand?.name || 'ABC Bank'}
              </span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <span className="font-bold text-slate-200 block">BrandShield AI Product Roadmap</span>
            <p>2026: DRP Social & App Monitoring</p>
            <p>2027: Cross-platform syndicate correlation</p>
            <p>2028: Automated platform takedown API bridge</p>
          </div>
        </div>
      </div>
    </div>
  );
}
