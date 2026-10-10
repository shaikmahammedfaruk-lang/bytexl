import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  AlertOctagon,
  FileText,
  SearchCode,
  Users,
  Image as ImageIcon,
  Globe,
  ExternalLink,
  Sparkles,
  ArrowRight,
  Activity,
  Bookmark,
  Check,
  Building,
  HelpCircle,
  Clock,
  Info,
  Flame,
  Copy,
  Download,
  RefreshCw,
  X,
  Edit3,
  Shield,
  Eye,
  Send,
  Lock,
  Layers,
  FileCheck,
  AlertCircle
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import {
  analyzeInstagramProfile,
  getInstagramHistory,
  createInvestigationFromInstagram,
  updateBrand
} from '../services/api';

const InstagramIcon = ({ className = "w-5 h-5" }) => (
  <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
  </svg>
);

const SCAN_STAGES = [
  { id: 1, title: "Collecting profile signals", desc: "Querying public telemetry, followers, following, posts, bio, and metrics" },
  { id: 2, title: "Comparing username", desc: "Calculating Levenshtein distance, look-alike patterns & brand roots" },
  { id: 3, title: "Comparing profile image", desc: "Computing perceptual dHash and trademark visual correlation" },
  { id: 4, title: "Comparing bio", desc: "Scanning for fake customer care claims and unauthorized slogans" },
  { id: 5, title: "Analyzing content", desc: "Auditing post captions, duplicated promo photography and graphics" },
  { id: 6, title: "Checking external links", desc: "Inspecting destination domains, URL shorteners and auth portals" },
  { id: 7, title: "Checking account behavior", desc: "Evaluating followers (0-50/51-500/501+), posts, following & bio words" },
  { id: 8, title: "Calculating risk score", desc: "Computing 10-factor weighted model & behavioral tier rules (0-100)" },
  { id: 9, title: "Generating threat report", desc: "Synthesizing explainable AI evidence dossier and recommendations" }
];

export default function InstagramAnalyzerPage() {
  const navigate = useNavigate();
  const { brands, selectedBrand, setSelectedBrand, refreshBrands } = useBrand();

  const [username, setUsername] = useState('');
  const [verificationOverride, setVerificationOverride] = useState(null); // null = auto, true = verified, false = unverified
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);
  const [scanProgress, setScanProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [toastMessage, setToastMessage] = useState('');
  const [investigating, setInvestigating] = useState(false);

  // Investigation status & notes state
  const [investigationStatus, setInvestigationStatus] = useState('NEW');
  const [analystNotes, setAnalystNotes] = useState('');
  const [notesList, setNotesList] = useState([]);

  // Modals state
  const [isEditGroundTruthOpen, setIsEditGroundTruthOpen] = useState(false);
  const [isTakedownModalOpen, setIsTakedownModalOpen] = useState(false);

  // Ground truth edit form
  const [gtForm, setGtForm] = useState({
    name: '',
    official_instagram_username: '',
    official_instagram_url: '',
    official_bio: '',
    official_instagram_logo: '',
    website: ''
  });

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3000);
  };

  const fetchHistory = async () => {
    if (!selectedBrand) return;
    try {
      const res = await getInstagramHistory(selectedBrand.id);
      setHistory(res.data);
    } catch (err) {
      console.error("Failed to load Instagram history", err);
    }
  };

  useEffect(() => {
    if (selectedBrand?.id) {
      fetchHistory();
    }
  }, [selectedBrand?.id]);

  useEffect(() => {
    if (selectedBrand) {
      const bName = selectedBrand.name || '';
      const cleanKey = bName.toLowerCase().replace(/[^a-z0-9_]/g, '');
      const igUser = selectedBrand.official_instagram_username || cleanKey;
      const igUrl = selectedBrand.official_instagram_url || (igUser ? `https://instagram.com/${igUser}` : '');
      const website = selectedBrand.website || (cleanKey ? `https://${cleanKey}.com` : '');
      const bio = selectedBrand.official_bio || selectedBrand.description || (bName ? `Official brand profile for ${bName}.` : '');
      const logo = selectedBrand.official_instagram_logo || selectedBrand.logo_url || '';

      setGtForm({
        name: bName,
        official_instagram_username: igUser,
        official_instagram_url: igUrl,
        official_bio: bio,
        official_instagram_logo: logo,
        website: website
      });
    }
  }, [selectedBrand]);

  const handleSaveGroundTruth = async (e) => {
    e.preventDefault();
    if (!selectedBrand?.id) return;
    try {
      const res = await updateBrand(selectedBrand.id, gtForm);
      showToast("Official Ground Truth updated successfully!");
      setIsEditGroundTruthOpen(false);
      if (res?.data) {
        setSelectedBrand(res.data);
      }
      await refreshBrands();
    } catch (err) {
      console.error("Failed to update ground truth", err);
      showToast("Error updating ground truth reference.");
    }
  };

  const handleAnalyze = async (e, customUsername = null, forcedVerified = undefined) => {
    if (e) e.preventDefault();
    const rawUser = (customUsername || username).trim();

    if (!rawUser) {
      setError("Please enter a valid Instagram username or profile URL.");
      return;
    }

    // Auto-clean pasted URLs
    const sanitized = rawUser
      .replace(/^https?:\/\/(www\.)?instagram\.com\//, '')
      .split('/')[0]
      .split('?')[0]
      .replace(/^@/, '');

    setError('');
    setLoading(true);
    setResult(null);
    setLoadingStage(0);
    setScanProgress(5);

    // 9-Stage animated cyber scanning progression
    const totalDuration = 2200; // 2.2 seconds total scan animation
    const intervalTime = totalDuration / SCAN_STAGES.length;

    let currentStage = 0;
    const stageTimer = setInterval(() => {
      currentStage += 1;
      if (currentStage < SCAN_STAGES.length) {
        setLoadingStage(currentStage);
        setScanProgress(Math.round(((currentStage + 1) / SCAN_STAGES.length) * 95));
      } else {
        clearInterval(stageTimer);
      }
    }, intervalTime);

    const verifiedParam = forcedVerified !== undefined ? forcedVerified : verificationOverride;

    try {
      const res = await analyzeInstagramProfile({
        username: sanitized,
        brand_id: selectedBrand?.id,
        is_verified: verifiedParam
      });

      // Complete progress bar
      setTimeout(() => {
        clearInterval(stageTimer);
        setScanProgress(100);
        setResult(res.data);
        setUsername(res.data.profile?.username || sanitized);
        setInvestigationStatus(res.data.risk?.level === 'CRITICAL' || res.data.risk?.level === 'HIGH' ? 'NEW' : 'RESOLVED');
        setNotesList([
          {
            time: new Date().toLocaleTimeString(),
            author: "Automated Risk Engine",
            text: `Initial AI Risk Assessment computed: ${res.data.risk?.score}/100 (${res.data.risk?.level} RISK). Summary: ${res.data.risk?.summary || res.data.risk?.reason || 'Multi-Signal Analysis'}.`
          }
        ]);
        setLoading(false);
        fetchHistory();
        refreshBrands();
      }, 400);

    } catch (err) {
      clearInterval(stageTimer);
      setLoading(false);
      const detail = err.response?.data?.detail || "Instagram profile analysis failed. Please verify the username.";
      setError(detail);
    }
  };

  const handleQuickPreset = (presetUsername, forcedVerified = null) => {
    setUsername(presetUsername);
    setVerificationOverride(forcedVerified);
    handleAnalyze(null, presetUsername, forcedVerified);
  };

  const handleCreateInvestigation = async () => {
    if (!result?.analysis_id) return;
    setInvestigating(true);
    try {
      const invRes = await createInvestigationFromInstagram({
        analysis_id: result.analysis_id,
        analyst_name: "SecOps Threat Analyst"
      });
      showToast(`Escalated to Case #${invRes.data.case_number || 'INV-IG'}`);
      if (invRes.data.id) {
        navigate(`/investigations/${invRes.data.id}`);
      }
    } catch (err) {
      showToast("Investigation escalated locally.");
      setInvestigationStatus('UNDER_INVESTIGATION');
    } finally {
      setInvestigating(false);
    }
  };

  const handleAddAnalystNote = (e) => {
    e.preventDefault();
    if (!analystNotes.trim()) return;
    setNotesList((prev) => [
      ...prev,
      {
        time: new Date().toLocaleTimeString(),
        author: "SecOps Analyst",
        text: analystNotes.trim()
      }
    ]);
    setAnalystNotes('');
    showToast("Analyst note recorded.");
  };

  const handleExportReport = () => {
    if (!result) return;
    const reportData = {
      brand_name: selectedBrand?.name,
      analyzed_username: result.profile?.username,
      timestamp: new Date().toISOString(),
      risk_score: result.risk?.score,
      risk_level: result.risk?.level,
      primary_threat: result.primary_threat,
      secondary_threat: result.secondary_threat,
      confidence_pct: result.confidence_pct,
      executive_explanation: result.explanation,
      why_flagged: result.why_flagged,
      profile_risk_matrix: result.profile_risk_matrix,
      signals: result.signals,
      evidence_cards: result.evidence_cards,
      recommendations: result.recommendations,
      official_comparison: result.official_comparison
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `brandshield-threat-report-${result.profile?.username || 'instagram'}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast("Forensic Threat Report exported as JSON!");
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    showToast("Forensic case link copied to clipboard!");
  };

  const profile = result?.profile;
  const risk = result?.risk;
  const isOfficial = result?.is_official_brand_asset;
  const comparison = result?.official_comparison;
  const suggestedOriginal = result?.suggested_original_account;

  // Bio words count helper
  const bioWordsCount = profile?.biography ? profile.biography.trim().split(/\s+/).filter(Boolean).length : 0;

  // Color helpers
  const getRiskColor = (score) => {
    if (score >= 81) return { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/30', ring: 'ring-rose-500/20' };
    if (score >= 61) return { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30', ring: 'ring-orange-500/20' };
    if (score >= 31) return { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30', ring: 'ring-amber-500/20' };
    return { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30', ring: 'ring-emerald-500/20' };
  };

  const riskPalette = getRiskColor(risk?.score || 0);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 border border-cyan-500/50 text-cyan-300 px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-2 text-xs font-semibold animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-cyan-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-pink-500 via-rose-500 to-amber-500 flex items-center justify-center text-white shadow-lg shadow-pink-500/25">
              <InstagramIcon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-black text-white tracking-tight">
                  Instagram Impersonation Risk Analyzer
                </h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-pink-500/15 text-pink-400 border border-pink-500/30">
                  Meta Graph API & Heuristics
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Profile behavioral rules, trademark duplication analysis, and explainable threat scoring.
              </p>
            </div>
          </div>
        </div>

        {/* Protected Brand Indicator / Switcher */}
        <div className="flex items-center gap-3 bg-slate-900/90 border border-slate-800 p-2.5 rounded-2xl shadow-sm">
          <div className="flex items-center gap-2">
            <Building className="w-4 h-4 text-cyan-400" />
            <span className="text-slate-400 text-xs font-medium">Protected Brand:</span>
          </div>
          <select
            value={selectedBrand?.id || ''}
            onChange={(e) => {
              const b = brands.find((x) => x.id === e.target.value);
              if (b) setSelectedBrand(b);
            }}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1 text-xs text-cyan-300 font-bold focus:outline-none focus:border-cyan-500"
          >
            {brands.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 1. OFFICIAL BRAND PROFILE CARD (GROUND TRUTH REFERENCE) */}
      <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/95 to-slate-950 border border-cyan-500/20 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3.5">
            <div className="relative">
              <img
                src={gtForm.official_instagram_logo || selectedBrand?.logo_url || "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200"}
                alt={selectedBrand?.name}
                className="w-13 h-13 rounded-2xl object-cover border-2 border-emerald-500/40 p-0.5 bg-slate-950"
              />
              <div className="absolute -bottom-1 -right-1 bg-emerald-500 text-slate-950 rounded-full p-0.5" title="Verified Ground Truth">
                <Check className="w-3 h-3 stroke-[3]" />
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">{selectedBrand?.name || "Official Brand"}</h2>
                <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <ShieldCheck className="w-3 h-3" />
                  Official Ground Truth
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                The authoritative baseline reference against which all external social handles are screened.
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsEditGroundTruthOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700 text-xs font-semibold transition"
          >
            <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
            Edit Ground Truth
          </button>
        </div>

        {/* Ground Truth Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 pt-4">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">Official Handle</span>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-400 font-mono">
                @{gtForm.official_instagram_username || selectedBrand?.official_instagram_username || (selectedBrand?.name ? selectedBrand.name.toLowerCase().replace(/[^a-z0-9_]/g, '') : 'brand')}
              </span>
              <a
                href={gtForm.official_instagram_url || `https://instagram.com/${gtForm.official_instagram_username || selectedBrand?.official_instagram_username || ''}`}
                target="_blank"
                rel="noreferrer"
                className="text-slate-500 hover:text-cyan-400 transition"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">Official Website</span>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200 truncate pr-2">
                {gtForm.website || selectedBrand?.website || (selectedBrand?.name ? `${selectedBrand.name.toLowerCase().replace(/[^a-z0-9]/g, '')}.com` : 'brand.com')}
              </span>
              <a
                href={(gtForm.website && gtForm.website.startsWith('http')) ? gtForm.website : `https://${gtForm.website || selectedBrand?.website || 'brand.com'}`}
                target="_blank"
                rel="noreferrer"
                className="text-slate-500 hover:text-cyan-400 transition flex-shrink-0"
              >
                <Globe className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1 sm:col-span-2">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">Official Biography Baseline</span>
            <p className="text-xs text-slate-300 italic truncate">
              "{gtForm.official_bio || selectedBrand?.official_bio || selectedBrand?.description || `Official verified presence for ${selectedBrand?.name || 'brand'}.`}"
            </p>
          </div>
        </div>
      </div>

      {/* 2. SUSPICIOUS ACCOUNT SCANNER */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
        <form onSubmit={handleAnalyze} className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <label className="text-xs font-bold text-white uppercase tracking-wider block">
                Target Account Under Surveillance
              </label>
              <p className="text-[11px] text-slate-400">
                Enter any Instagram handle or full profile URL to trigger multi-signal behavioral and heuristic screening.
              </p>
            </div>

            {/* Verification Status Control */}
            <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 text-[11px]">
              <span className="text-slate-400 font-medium px-2 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                Badge Mode:
              </span>
              <button
                type="button"
                onClick={() => setVerificationOverride(null)}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  verificationOverride === null
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Auto-Detect
              </button>
              <button
                type="button"
                onClick={() => setVerificationOverride(true)}
                className={`px-2.5 py-1 rounded-lg font-medium flex items-center gap-1 transition ${
                  verificationOverride === true
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <CheckCircle2 className="w-3 h-3 text-blue-400" />
                Verified ✓
              </button>
              <button
                type="button"
                onClick={() => setVerificationOverride(false)}
                className={`px-2.5 py-1 rounded-lg font-medium transition ${
                  verificationOverride === false
                    ? 'bg-slate-700 text-slate-200 border border-slate-600 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Unverified
              </button>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-2.5">
            <div className="relative flex-1">
              <span className="absolute left-3.5 top-3 text-slate-500 font-bold text-sm">@</span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. nike_support247, nike_customer_help, or alluarjunonline"
                className="w-full pl-8 pr-10 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:border-cyan-500 font-mono transition"
              />
              {username && (
                <button
                  type="button"
                  onClick={() => setUsername('')}
                  className="absolute right-3 top-3 text-slate-500 hover:text-slate-300"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !username?.trim()}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-sm shadow-lg shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Scanning Profile...</span>
                </>
              ) : (
                <>
                  <SearchCode className="w-4 h-4" />
                  <span>SCAN ACCOUNT</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Quick Demo Presets */}
        <div className="pt-2 border-t border-slate-800/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Live Demo Presets:
            </span>
            <span className="text-[10px] text-slate-500">Quick test cases</span>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleQuickPreset('nike_support247', false)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center gap-1.5 transition"
            >
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              <span>@nike_support247</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 font-mono font-bold">
                Critical Risk
              </span>
            </button>

            <button
              onClick={() => handleQuickPreset('nike_customer_help', false)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1.5 transition"
            >
              <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
              <span>@nike_customer_help</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-mono font-bold">
                Medium Risk
              </span>
            </button>

            <button
              onClick={() => handleQuickPreset('nike_india_support', false)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5 transition"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>@nike_india_support</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold">
                Low Risk
              </span>
            </button>

            <button
              onClick={() => handleQuickPreset('nike', true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center gap-1.5 transition"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              <span>@nike</span>
              <span className="text-[10px] opacity-75 font-mono">(Official Ground Truth)</span>
            </button>

            <button
              onClick={() => handleQuickPreset('alluarjunonline', true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5 transition"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
              <span>@alluarjunonline</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold">
                Original Verified
              </span>
            </button>

            <button
              onClick={() => handleQuickPreset('alluarjun_online', false)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/40 flex items-center gap-1.5 transition"
            >
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              <span>@alluarjun_online</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/30 text-rose-200 font-mono font-bold">
                Duplicate Fake
              </span>
            </button>

            <button
              onClick={() => handleQuickPreset('virat.kohli', true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5 transition"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
              <span>@virat.kohli</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold">
                Original Verified
              </span>
            </button>

            <button
              onClick={() => handleQuickPreset('virat_kohli', false)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/40 flex items-center gap-1.5 transition"
            >
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              <span>@virat_kohli</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/30 text-rose-200 font-mono font-bold">
                Duplicate Fake
              </span>
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2 font-medium">
            <AlertOctagon className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* 3. ANIMATED 9-STAGE CYBERSECURITY SCANNING SEQUENCE */}
      {loading && (
        <div className="p-8 rounded-2xl bg-slate-900 border border-cyan-500/30 shadow-2xl relative overflow-hidden space-y-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              {/* Radar Sonar Pulse Animation */}
              <div className="relative w-20 h-20 flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-2 border-cyan-500/20 animate-ping" />
                <div className="absolute inset-2 rounded-full border border-cyan-400/40 animate-pulse" />
                <div className="w-12 h-12 rounded-full bg-cyan-500/10 border-2 border-cyan-400 flex items-center justify-center text-cyan-400 shadow-lg shadow-cyan-500/30">
                  <SearchCode className="w-6 h-6 animate-pulse" />
                </div>
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-cyan-400 font-bold uppercase">
                    Stage {loadingStage + 1} of {SCAN_STAGES.length}:
                  </span>
                  <span className="text-xs font-bold text-white">
                    {SCAN_STAGES[loadingStage]?.title}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 max-w-md">
                  {SCAN_STAGES[loadingStage]?.desc}
                </p>
              </div>
            </div>

            {/* Progress Percentage Display */}
            <div className="text-right flex-shrink-0">
              <span className="text-3xl font-black text-cyan-400 font-mono">{scanProgress}%</span>
              <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">
                Telemetry Processed
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-cyan-500 via-blue-500 to-rose-500 h-full transition-all duration-300"
              style={{ width: `${scanProgress}%` }}
            />
          </div>

          {/* Checklist of all 9 stages */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-2">
            {SCAN_STAGES.map((stg, idx) => {
              const isDone = idx < loadingStage;
              const isCurrent = idx === loadingStage;
              return (
                <div
                  key={stg.id}
                  className={`p-2.5 rounded-xl border text-xs flex items-center gap-2.5 transition ${
                    isDone
                      ? 'bg-slate-950/80 border-cyan-500/30 text-slate-200'
                      : isCurrent
                      ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-300 font-bold'
                      : 'bg-slate-950/40 border-slate-800/60 text-slate-600'
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                  ) : isCurrent ? (
                    <RefreshCw className="w-4 h-4 text-cyan-400 animate-spin flex-shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-700 flex items-center justify-center text-[9px] flex-shrink-0">
                      {stg.id}
                    </div>
                  )}
                  <span className="truncate">{stg.title}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* RESULT SECTION */}
      {result && !loading && (
        <div className="space-y-6 animate-fadeIn">
          {/* 4. EXECUTIVE RISK SCORE & CLASSIFICATION BANNER */}
          <div className={`p-6 rounded-2xl bg-slate-900/90 border ${riskPalette.border} shadow-2xl relative overflow-hidden space-y-5`}>
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 pb-5 border-b border-slate-800">
              <div className="flex items-start gap-4">
                {/* Risk Score Circle Gauge */}
                <div className={`w-22 h-22 rounded-2xl ${riskPalette.bg} border-2 ${riskPalette.border} flex flex-col items-center justify-center p-2 shadow-xl flex-shrink-0`}>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Risk Score</span>
                  <span className={`text-3xl font-black ${riskPalette.text} font-mono leading-none my-1`}>
                    {risk?.score}
                  </span>
                  <span className="text-[9px] font-bold text-slate-500 font-mono">/ 100</span>
                </div>

                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`text-sm font-black px-2.5 py-0.5 rounded-lg border ${riskPalette.bg} ${riskPalette.text} ${riskPalette.border}`}>
                      {risk?.level} RISK
                    </span>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-lg bg-slate-800 text-slate-200 border border-slate-700">
                      Threat: {result.primary_threat}
                    </span>
                    {result.secondary_threat && (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-lg bg-slate-950 text-slate-400 border border-slate-800">
                        Vector: {result.secondary_threat}
                      </span>
                    )}
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                      {result.confidence_pct}% Confidence
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>@{profile?.username}</span>
                    {profile?.is_verified && (
                      <CheckCircle2 className="w-4 h-4 text-blue-400" title="Meta Verified Badge" />
                    )}
                  </h3>

                  <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                    {result.explanation}
                  </p>
                </div>
              </div>

              {/* Action Buttons Toolbar */}
              <div className="flex flex-wrap lg:flex-col gap-2 w-full lg:w-auto">
                <button
                  onClick={handleCreateInvestigation}
                  disabled={investigating}
                  className="flex-1 lg:flex-none px-4 py-2 rounded-xl bg-gradient-to-r from-rose-500 to-red-600 hover:from-rose-600 hover:to-red-700 text-white font-bold text-xs shadow-md shadow-rose-500/20 flex items-center justify-center gap-1.5 transition"
                >
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>Escalate to Investigation</span>
                </button>

                <div className="flex gap-2 w-full">
                  <button
                    onClick={handleExportReport}
                    className="flex-1 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                    title="Export complete threat dossier as JSON"
                  >
                    <Download className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Export Report</span>
                  </button>

                  <button
                    onClick={() => setIsTakedownModalOpen(true)}
                    className="flex-1 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                    title="Generate DMCA / Trademark Takedown package"
                  >
                    <Send className="w-3.5 h-3.5 text-amber-400" />
                    <span>Meta Notice</span>
                  </button>

                  <button
                    onClick={handleCopyLink}
                    className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                    title="Copy shareable case link"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Official Asset Exclusion Notice */}
            {isOfficial && (
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2.5">
                <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                <div>
                  <strong className="font-bold">Authorized Official Asset:</strong> This profile is verified and cataloged in the BrandShield ground truth registry. Digital risk alerts are suppressed by policy.
                </div>
              </div>
            )}

            {/* Quick Metrics Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Followers</span>
                <span className="text-sm font-black text-white font-mono">{profile?.followers_count?.toLocaleString()}</span>
                <span className="text-[9px] text-slate-400 block font-mono mt-0.5">
                  Audience Reach
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Posts</span>
                <span className="text-sm font-black text-white font-mono">{profile?.media_count?.toLocaleString()}</span>
                <span className="text-[9px] text-slate-400 block font-mono mt-0.5">
                  Content Volume
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Following</span>
                <span className="text-sm font-black text-white font-mono">{profile?.following_count?.toLocaleString()}</span>
                <span className="text-[9px] text-slate-400 block font-mono mt-0.5">
                  Outbound Ratio
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Bio Length</span>
                <span className="text-sm font-black text-white font-mono">{bioWordsCount} words</span>
                <span className="text-[9px] text-slate-400 block font-mono mt-0.5 truncate">
                  {bioWordsCount === 0 ? "Empty Bio" : `${bioWordsCount} Words Bio`}
                </span>
              </div>
            </div>
          </div>

          {/* 4.5 DUPLICATE ACCOUNT DETECTED — SUGGESTED ORIGINAL ACCOUNT */}
          {suggestedOriginal?.is_duplicate && (
            <div className="p-6 rounded-2xl bg-gradient-to-br from-rose-950/40 via-slate-900 to-slate-950 border-2 border-rose-500/60 shadow-2xl relative overflow-hidden space-y-5">
              <div className="absolute top-0 right-0 w-96 h-96 bg-rose-500/10 rounded-full blur-3xl pointer-events-none" />

              {/* Header Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-rose-500/30">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400 shadow-lg shadow-rose-500/30 flex-shrink-0">
                    <ShieldAlert className="w-5 h-5 animate-pulse" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black px-2.5 py-0.5 rounded-full bg-rose-500 text-white shadow-sm tracking-wider">
                        DUPLICATE ACCOUNT DETECTED
                      </span>
                      <span className="text-xs font-mono font-bold text-rose-300">
                        {suggestedOriginal.similarity_pct}% Handle Similarity
                      </span>
                    </div>
                    <p className="text-xs text-rose-200/90 mt-1">
                      Target profile <span className="font-mono font-bold text-white">@{profile?.username}</span> appears to duplicate and impersonate authentic verified entity <span className="font-mono font-bold text-cyan-300">@{suggestedOriginal.original_username}</span>.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-rose-500/30">
                  <Flame className="w-4 h-4 text-rose-400" />
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 block uppercase font-bold">Escalated Risk Factor</span>
                    <span className="text-sm font-black text-rose-400 font-mono leading-none">
                      {risk?.score}/100 ({risk?.level})
                    </span>
                  </div>
                </div>
              </div>

              {/* Explanatory Callout */}
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-200 text-xs flex items-start gap-2.5">
                <AlertOctagon className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="font-semibold text-rose-300">
                    {suggestedOriginal.risk_escalation_reason || "Risk score escalated due to trademark handlesquatting and look-alike impersonation."}
                  </div>
                  <div className="text-[11px] text-slate-300">
                    {suggestedOriginal.recommendation}
                  </div>
                </div>
              </div>

              {/* Dual Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Left: Screened Duplicate */}
                <div className="p-4 rounded-xl bg-slate-950/80 border border-rose-500/40 space-y-3 relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                      🚨 Scanned Duplicate Impersonator
                    </span>
                    <span className="text-[11px] font-mono font-bold text-rose-400">
                      Risk: {risk?.score}/100
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <img
                      src={profile?.profile_picture_url || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200"}
                      alt={profile?.username}
                      className="w-12 h-12 rounded-xl object-cover border-2 border-rose-500/50 p-0.5 bg-slate-900"
                    />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-bold text-white">{profile?.display_name || profile?.username}</span>
                        {!profile?.is_verified && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-amber-400 border border-amber-500/30 font-medium">
                            Unverified
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-rose-400 font-mono font-bold">
                        @{profile?.username}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1 text-xs text-slate-300">
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-500">Audience:</span>
                      <span className="font-mono text-white">{profile?.followers_count?.toLocaleString()} followers</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-500">Post Count:</span>
                      <span className="font-mono text-white">{profile?.media_count?.toLocaleString()} posts</span>
                    </div>
                    <div className="pt-2">
                      <span className="text-[10px] text-slate-500 block uppercase font-bold mb-1">Detected Duplication Tactics:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {suggestedOriginal.duplicate_tactics?.map((tactic, tIdx) => (
                          <span key={tIdx} className="text-[10px] px-2 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
                            ⚠ {tactic}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: Suggested Authentic Original */}
                <div className="p-4 rounded-xl bg-slate-950/80 border border-emerald-500/50 space-y-3 relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" />
                      Suggested Authentic Original
                    </span>
                    <span className="text-[11px] font-mono text-emerald-400 font-bold">
                      Authentic Entity
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <img
                      src={suggestedOriginal.original_avatar || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200"}
                      alt={suggestedOriginal.original_name}
                      className="w-12 h-12 rounded-xl object-cover border-2 border-emerald-500/50 p-0.5 bg-slate-900"
                    />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-bold text-white">{suggestedOriginal.original_name}</span>
                        {suggestedOriginal.original_is_verified && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" title="Meta Verified Account" />
                        )}
                      </div>
                      <span className="text-xs text-emerald-400 font-mono font-bold">
                        @{suggestedOriginal.original_username}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1 text-xs text-slate-300">
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-500">Verified Reach:</span>
                      <span className="font-mono text-emerald-300 font-bold">
                        {suggestedOriginal.original_followers_formatted || (suggestedOriginal.original_followers_count ? suggestedOriginal.original_followers_count.toLocaleString() : 'Official')} followers
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-500">Platform Status:</span>
                      <span className="text-blue-400 font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Meta Verified
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-500">Official URL:</span>
                      <span className="font-mono text-slate-300 truncate max-w-[200px]">
                        {suggestedOriginal.original_url}
                      </span>
                    </div>
                  </div>

                  {/* Actions for Original Account */}
                  <div className="flex items-center gap-2 pt-2">
                    <a
                      href={suggestedOriginal.original_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex-1 py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                    >
                      <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
                      <span>View on Instagram</span>
                    </a>

                    <button
                      type="button"
                      onClick={() => handleQuickPreset(suggestedOriginal.original_username, true)}
                      className="flex-1 py-1.5 px-3 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                    >
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Scan Original</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* VERIFIED AUTHENTIC ORIGINAL ACCOUNT BANNER */}
          {suggestedOriginal?.is_authentic_original && (
            <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/40 to-slate-900 border border-emerald-500/40 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 flex-shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-emerald-400">
                      AUTHENTIC ORIGINAL PROFILE CONFIRMED
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                      Verified Identity
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-0.5">
                    This account (<span className="font-mono text-cyan-300">@{profile?.username}</span>) is cataloged as the legitimate authentic entity with {profile?.followers_count?.toLocaleString()} followers. Threat risk is negligible ({risk?.score}/100).
                  </p>
                </div>
              </div>

              <a
                href={suggestedOriginal.original_url || `https://www.instagram.com/${profile?.username}/`}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium flex items-center gap-1.5 flex-shrink-0 transition"
              >
                <ExternalLink className="w-3.5 h-3.5 text-emerald-400" />
                <span>Instagram Profile</span>
              </a>
            </div>
          )}

          {/* 5. SIDE-BY-SIDE ACCOUNT COMPARISON VIEW */}
          {comparison && (
            <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Side-by-Side Brand Likeness Comparison
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">
                  Ground Truth Reference vs Screened Target
                </span>
              </div>

              {/* Comparison Metrics Header Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                <div className="text-center">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">Username Match</span>
                  <span className="text-sm font-black text-rose-400 font-mono">
                    {comparison.metrics?.username_match_pct}%
                  </span>
                </div>
                <div className="text-center">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">Logo Match</span>
                  <span className="text-sm font-black text-rose-400 font-mono">
                    {comparison.metrics?.logo_match_pct}%
                  </span>
                </div>
                <div className="text-center">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">Bio Similarity</span>
                  <span className="text-sm font-black text-orange-400 font-mono">
                    {comparison.metrics?.bio_match_pct}%
                  </span>
                </div>
                <div className="text-center">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">External Domain</span>
                  <span className={`text-xs font-bold ${comparison.metrics?.domain_mismatch ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {comparison.metrics?.domain_mismatch ? "⚠️ MISMATCH" : "✓ MATCH"}
                  </span>
                </div>
              </div>

              {/* Dual Column Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Left: Official Brand Account */}
                <div className="p-4 rounded-xl bg-slate-950/70 border border-emerald-500/30 space-y-3 relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      ✓ Official Brand Ground Truth
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono">Protected Reference</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <img
                      src={comparison.official?.logo_url || gtForm.official_instagram_logo}
                      alt="Official Logo"
                      className="w-12 h-12 rounded-xl object-cover border border-emerald-500/50 p-0.5 bg-slate-900"
                    />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-bold text-white">{comparison.official?.display_name}</span>
                        <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
                      </div>
                      <span className="text-xs text-emerald-400 font-mono font-semibold">
                        {comparison.official?.username}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-300">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Official Biography</span>
                      <p className="italic text-slate-300 text-[11px]">"{comparison.official?.bio}"</p>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-500 block">Authorized Domain</span>
                      <a href={comparison.official?.website} target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline flex items-center gap-1 text-[11px] font-mono">
                        <Globe className="w-3 h-3" />
                        {comparison.official?.website}
                      </a>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-500 block">Follower Base</span>
                      <span className="font-mono text-white font-bold text-[11px]">
                        {comparison.official?.followers_count ? comparison.official.followers_count.toLocaleString() : '305,000,000'} followers
                      </span>
                    </div>
                  </div>
                </div>

                {/* Right: Suspicious Target Profile */}
                <div className={`p-4 rounded-xl bg-slate-950/70 border ${riskPalette.border} space-y-3 relative`}>
                  <div className="flex items-center justify-between">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${riskPalette.bg} ${riskPalette.text} border ${riskPalette.border}`}>
                      🚨 Screened Target Profile
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono">Target Telemetry</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <img
                      src={comparison.suspicious?.logo_url || profile?.profile_picture_url || gtForm.official_instagram_logo}
                      alt="Target Avatar"
                      className="w-12 h-12 rounded-xl object-cover border border-rose-500/50 p-0.5 bg-slate-900"
                    />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-bold text-white">{comparison.suspicious?.display_name || profile?.display_name}</span>
                        {profile?.is_verified && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
                        )}
                      </div>
                      <span className="text-xs text-rose-400 font-mono font-semibold">
                        {comparison.suspicious?.username}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-300">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Target Biography</span>
                      <p className="italic text-slate-300 text-[11px]">
                        "{comparison.suspicious?.bio || profile?.biography || 'No bio provided.'}"
                      </p>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-500 block">External Link Target</span>
                      {comparison.suspicious?.website ? (
                        <div className="flex items-center gap-1 text-[11px] font-mono text-rose-400">
                          <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                          <span className="truncate">{comparison.suspicious.website}</span>
                        </div>
                      ) : (
                        <span className="text-slate-500 italic text-[11px]">None provided</span>
                      )}
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-500 block">Follower Telemetry</span>
                      <span className="font-mono text-white font-bold text-[11px]">
                        {profile?.followers_count?.toLocaleString()} followers · {profile?.following_count?.toLocaleString()} following
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 6. EXPLAINABLE AI ("WHY THIS ACCOUNT WAS FLAGGED") */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Explainable AI: Why This Account Was Flagged
                </h3>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                Model: Antigravity Multi-Signal Behavioral Engine v2.4
              </span>
            </div>

            <div className="space-y-2.5">
              {result.why_flagged?.map((item, idx) => {
                const isRed = item.severity_dot === 'RED';
                const isOrange = item.severity_dot === 'ORANGE';
                const cardBorder = isRed ? 'border-rose-500/20 bg-rose-500/5' : isOrange ? 'border-amber-500/20 bg-amber-500/5' : 'border-emerald-500/20 bg-emerald-500/5';

                return (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border ${cardBorder} flex items-start gap-3 text-xs`}
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      {isRed ? (
                        <span className="flex h-2.5 w-2.5 relative">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                        </span>
                      ) : isOrange ? (
                        <span className="inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
                      ) : (
                        <span className="inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                      )}
                    </div>
                    <span className="text-slate-200 font-medium leading-relaxed">
                      {typeof item === 'string' ? item : item?.text || ''}
                    </span>
                  </div>
                );
              })}
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
              <Info className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
              <span>
                Assessment based on calibrated behavioral rules (followers, posts, following, bio) and Meta API telemetry. Does not represent a definitive legal conclusion without human triage.
              </span>
            </div>
          </div>

          {/* 7. 10 DETECTION SIGNALS (100% WEIGHTED BREAKDOWN) */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  10-Factor Detection Signal Breakdown (100% Model Weight)
                </h3>
              </div>
              <span className="text-[11px] text-cyan-400 font-mono font-bold">
                Σ Weights = 100%
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {result.signals?.map((sig, idx) => {
                const sevColor =
                  sig.severity === 'CRITICAL' ? 'text-rose-400 border-rose-500/30 bg-rose-500/10' :
                  sig.severity === 'HIGH' ? 'text-orange-400 border-orange-500/30 bg-orange-500/10' :
                  sig.severity === 'MEDIUM' ? 'text-amber-400 border-amber-500/30 bg-amber-500/10' :
                  sig.severity === 'POSITIVE' ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' :
                  'text-slate-400 border-slate-800 bg-slate-950';

                const progressWidth = Math.min(100, Math.max(0, (sig.score / sig.weight) * 100));

                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2 hover:border-slate-700 transition"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">{sig.name}</span>
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          {sig.weight}% Weight
                        </span>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${sevColor}`}>
                        {sig.severity}
                      </span>
                    </div>

                    {/* Progress Bar for Signal Score Contribution */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] font-mono">
                        <span className="text-slate-500">Contribution</span>
                        <span className="font-bold text-cyan-400">+{sig.score} / {sig.weight} pts</span>
                      </div>
                      <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${sig.score > 0 ? (sig.severity === 'CRITICAL' ? 'bg-rose-500' : sig.severity === 'HIGH' ? 'bg-orange-500' : 'bg-cyan-500') : 'bg-slate-700'}`}
                          style={{ width: `${progressWidth}%` }}
                        />
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-300 leading-normal">
                      {sig.reason}
                    </p>

                    {sig.evidence && (
                      <div className="pt-1 border-t border-slate-900 text-[10px] text-slate-500 font-mono truncate">
                        Evidence: {sig.evidence}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* 8. FORENSIC EVIDENCE CARDS */}
          {result.evidence_cards && result.evidence_cards.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-rose-400" />
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Forensic Evidence Cards
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">
                  Authoritative Forensic Artifacts
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {result.evidence_cards?.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 relative overflow-hidden"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 uppercase font-mono">
                        {ev.category}
                      </span>
                      <span className="text-[10px] font-black text-cyan-400 font-mono">
                        {ev.badge}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-white">{ev.title}</h4>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{ev.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 9. INVESTIGATION WORKFLOW & STATUS TRIAGE */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Active Investigation Lifecycle & Triage
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-medium">Status:</span>
                <select
                  value={investigationStatus}
                  onChange={(e) => {
                    setInvestigationStatus(e.target.value);
                    showToast(`Investigation status updated to: ${e.target.value}`);
                  }}
                  className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs font-bold text-cyan-300 focus:outline-none focus:border-cyan-500"
                >
                  <option value="NEW">NEW</option>
                  <option value="UNDER_INVESTIGATION">UNDER_INVESTIGATION</option>
                  <option value="CONFIRMED_THREAT">CONFIRMED_THREAT</option>
                  <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
                  <option value="RESOLVED">RESOLVED</option>
                </select>
              </div>
            </div>

            {/* Recommendations */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Recommended Actions:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {result.recommendations?.map((rec, i) => (
                  <div key={i} className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-start gap-2">
                    <ArrowRight className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Analyst Notes & Timeline */}
            <div className="pt-3 border-t border-slate-800 space-y-3">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Analyst Investigation Notes:
              </span>

              {notesList.length > 0 && (
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {notesList.map((n, i) => (
                    <div key={i} className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 space-y-0.5">
                      <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                        <span className="font-bold text-cyan-400">{n.author}</span>
                        <span>{n.time}</span>
                      </div>
                      <p>{n.text}</p>
                    </div>
                  ))}
                </div>
              )}

              <form onSubmit={handleAddAnalystNote} className="flex gap-2">
                <input
                  type="text"
                  value={analystNotes}
                  onChange={(e) => setAnalystNotes(e.target.value)}
                  placeholder="Record an analyst finding or forensic triage note..."
                  className="flex-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
                />
                <button
                  type="submit"
                  disabled={!analystNotes.trim()}
                  className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs disabled:opacity-50 transition"
                >
                  Add Note
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* 10. HISTORICAL ANALYSES TABLE */}
      {history.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-purple-400" />
              Recent Profile Risk Scans ({history.length})
            </h3>
            <span className="text-[11px] text-slate-500 font-mono">Stored in MongoDB</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase font-bold">
                  <th className="py-2.5 px-3">Target Handle</th>
                  <th className="py-2.5 px-3">Risk Score</th>
                  <th className="py-2.5 px-3">Level</th>
                  <th className="py-2.5 px-3">Threat Assessment</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3 text-right">Quick Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {history.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-mono font-bold text-cyan-300">@{item.username}</td>
                    <td className="py-2.5 px-3 font-black text-rose-400 font-mono">{item.risk?.score}/100</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {item.risk?.level}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-[11px] text-slate-400 font-mono truncate max-w-xs">
                      {item.risk?.reason || item.risk?.summary || item.why_flagged?.[0]?.text || (typeof item.why_flagged?.[0] === 'string' ? item.why_flagged[0] : null) || "Risk Assessment"}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleQuickPreset(item.username)}
                        className="text-cyan-400 hover:text-cyan-300 text-xs font-bold underline"
                      >
                        Re-inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL: EDIT GROUND TRUTH */}
      {isEditGroundTruthOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-white">Edit Official Ground Truth Reference</h3>
              </div>
              <button onClick={() => setIsEditGroundTruthOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveGroundTruth} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-semibold block mb-1">Brand Name</label>
                <input
                  type="text"
                  value={gtForm.name}
                  onChange={(e) => setGtForm({ ...gtForm, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100"
                  required
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Official Instagram Handle</label>
                <input
                  type="text"
                  value={gtForm.official_instagram_username}
                  onChange={(e) => setGtForm({ ...gtForm, official_instagram_username: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-cyan-300 font-mono"
                  placeholder="e.g. nike"
                  required
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Official Instagram URL</label>
                <input
                  type="text"
                  value={gtForm.official_instagram_url}
                  onChange={(e) => setGtForm({ ...gtForm, official_instagram_url: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 font-mono"
                  placeholder="https://instagram.com/nike"
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Official Website</label>
                <input
                  type="text"
                  value={gtForm.website}
                  onChange={(e) => setGtForm({ ...gtForm, website: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 font-mono"
                  placeholder="https://nike.com"
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Official Bio / Trademark Slogan</label>
                <textarea
                  value={gtForm.official_bio}
                  onChange={(e) => setGtForm({ ...gtForm, official_bio: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100"
                  placeholder="Just Do It. #Nike"
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Official Logo Image URL</label>
                <input
                  type="text"
                  value={gtForm.official_instagram_logo}
                  onChange={(e) => setGtForm({ ...gtForm, official_instagram_logo: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 font-mono text-[11px]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsEditGroundTruthOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20"
                >
                  Save Ground Truth
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: META TAKEDOWN NOTICE GENERATOR */}
      {isTakedownModalOpen && result && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Send className="w-5 h-5 text-amber-400" />
                <h3 className="text-sm font-bold text-white">Meta Platform IP Infringement Notice</h3>
              </div>
              <button onClick={() => setIsTakedownModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Pre-filled legal infringement declaration ready to submit via the Meta Intellectual Property Reporting form.
            </p>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 space-y-2 max-h-60 overflow-y-auto">
              <p><strong>To:</strong> Meta Trust & Safety / Brand Protection Desk</p>
              <p><strong>Reporting Brand:</strong> {selectedBrand?.name} ({gtForm.website})</p>
              <p><strong>Official Handle:</strong> @{gtForm.official_instagram_username}</p>
              <p><strong>Infringing Handle:</strong> @{result.profile?.username} (https://instagram.com/{result.profile?.username})</p>
              <p><strong>Risk Score:</strong> {result.risk?.score}/100 ({result.risk?.level} RISK)</p>
              <p><strong>Violations Observed:</strong></p>
              <ul className="list-disc list-inside space-y-1 pl-2 text-slate-400">
                {result.why_flagged?.map((w, idx) => (
                  <li key={idx}>{typeof w === 'string' ? w : w?.text || ''}</li>
                ))}
              </ul>
              <p><strong>Demand:</strong> Immediate profile suspension or trademark de-indexing to prevent imminent consumer financial fraud.</p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => {
                  const legalNotice = `To: Meta Trust & Safety Desk\nBrand: ${selectedBrand?.name}\nInfringing Handle: @${result.profile?.username}\nRisk Score: ${result.risk?.score}/100 (${result.risk?.level})\nExecutive Summary: ${result.explanation}\nDemand: Immediate profile suspension under Trademark Impersonation Policy.`;
                  navigator.clipboard.writeText(legalNotice);
                  showToast("Takedown Notice copied to clipboard!");
                  setIsTakedownModalOpen(false);
                }}
                className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20 flex items-center gap-1.5"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>Copy Notice to Clipboard</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
