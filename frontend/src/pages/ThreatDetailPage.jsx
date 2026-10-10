import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Flame,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  FileText,
  SearchCode,
  CheckCircle2,
  ExternalLink,
  MessageSquare,
  Network,
  Clock,
  Send,
  AlertOctagon,
  Sparkles,
  Lock
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import {
  getThreat,
  updateThreat,
  resolveThreat,
  markThreatReviewed,
  markThreatLegitimate,
  createInvestigation
} from '../services/api';
import { formatScore } from '../utils/formatters';

export default function ThreatDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { openEvidenceModal } = useBrand();

  const [threat, setThreat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState('');
  const [analystName, setAnalystName] = useState('SecOps Analyst');

  const fetchThreatDetails = async () => {
    setLoading(true);
    try {
      const res = await getThreat(id);
      setThreat(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThreatDetails();
  }, [id]);

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    try {
      await updateThreat(id, { note: newNote.trim(), analyst_assigned: analystName });
      setNewNote('');
      fetchThreatDetails();
    } catch (err) {
      console.error(err);
    }
  };

  const handleResolve = async () => {
    await resolveThreat(id);
    fetchThreatDetails();
  };

  const handleReview = async () => {
    await markThreatReviewed(id);
    fetchThreatDetails();
  };

  const handleLegitimate = async () => {
    if (confirm("Confirm as Legitimate Asset? This records analyst feedback for False Positive Protection.")) {
      await markThreatLegitimate(id);
      fetchThreatDetails();
    }
  };

  const handleOpenInvestigation = async () => {
    try {
      const res = await createInvestigation({ threat_id: id });
      navigate(`/investigations/${res.data.id}`);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading threat telemetry...</div>;
  }

  if (!threat) {
    return <div className="p-8 text-center text-rose-400">Threat record not found.</div>;
  }

  const factors = threat.detection_factors || {};
  const comp = threat.official_comparison || { official: {}, suspicious: {}, differences: [] };

  return (
    <div className="space-y-6">
      {/* Back button & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate('/threat-center')}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Threat Center</span>
        </button>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => openEvidenceModal(threat.id)}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700"
          >
            <FileText className="w-3.5 h-3.5 text-cyan-400" />
            <span>Generate Evidence</span>
          </button>

          <button
            onClick={handleOpenInvestigation}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold flex items-center gap-1.5 border border-slate-700"
          >
            <SearchCode className="w-3.5 h-3.5" />
            <span>AI Investigation</span>
          </button>

          {threat.status !== 'REVIEWED' && threat.status !== 'RESOLVED' && (
            <button
              onClick={handleReview}
              className="px-3.5 py-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-semibold"
            >
              Mark Reviewed
            </button>
          )}

          {threat.status !== 'RESOLVED' && (
            <button
              onClick={handleResolve}
              className="px-3.5 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold"
            >
              Resolve Threat
            </button>
          )}

          {threat.status !== 'LEGITIMATE_FALSE_POSITIVE' && (
            <button
              onClick={handleLegitimate}
              className="px-3 py-1.5 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-slate-300 text-xs"
              title="Tune false positive protection"
            >
              Mark Legitimate
            </button>
          )}
        </div>
      </div>

      {/* Main Threat Header Card */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <img
              src={threat.profile_or_icon_url || 'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=100'}
              alt=""
              className="w-16 h-16 rounded-2xl object-cover bg-slate-800 border border-slate-700"
            />
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 uppercase">
                  {threat.threat_type}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-cyan-300 border border-slate-700">
                  {threat.platform}
                </span>
              </div>
              <h1 className="text-xl font-bold text-white mt-1">{threat.account_or_app_name}</h1>
              <p className="text-xs text-slate-400 font-mono flex items-center gap-1 mt-0.5">
                <span>{threat.username_or_package || threat.developer_name}</span>
                <span>•</span>
                <a href={threat.url} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline flex items-center gap-1">
                  <span>{threat.url}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`px-3 py-1 rounded-lg text-xs font-bold ${
                threat.status === 'RESOLVED'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : threat.status === 'UNDER_INVESTIGATION'
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                  : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
              }`}
            >
              Status: {threat.status}
            </span>
          </div>
        </div>

        {/* BRANDSHIELD AI UNIQUE 4-METRIC SIGNATURE BAR */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t border-slate-800">
          {/* THREAT RISK */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-rose-900/30">
            <span className="text-[10px] font-bold uppercase text-slate-400 block tracking-wider">Threat Risk</span>
            <div className="text-2xl font-black text-rose-400 mt-1">
              {formatScore(threat.risk_score)}<span className="text-xs font-medium text-slate-500">/100</span>
            </div>
            <span className="text-[10px] font-bold text-rose-500 uppercase">{threat.risk_level} SEVERITY</span>
          </div>

          {/* CUSTOMER IMPACT */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-amber-900/30">
            <span className="text-[10px] font-bold uppercase text-slate-400 block tracking-wider">Customer Impact</span>
            <div className="text-2xl font-black text-amber-400 mt-1">
              {formatScore(threat.customer_impact_score)}<span className="text-xs font-medium text-slate-500">/100</span>
            </div>
            <span className="text-[10px] text-amber-500/80 font-medium">Fraud & Phishing Potential</span>
          </div>

          {/* CONFIDENCE */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-cyan-900/30">
            <span className="text-[10px] font-bold uppercase text-slate-400 block tracking-wider">Confidence</span>
            <div className="text-2xl font-black text-cyan-400 mt-1">
              {formatScore(threat.confidence)}%
            </div>
            <span className="text-[10px] text-cyan-500/80 font-medium">Algorithmic Match Certainty</span>
          </div>

          {/* CAMPAIGN RISK */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-purple-900/30">
            <span className="text-[10px] font-bold uppercase text-slate-400 block tracking-wider">Campaign Risk</span>
            <div className="text-2xl font-black text-purple-400 mt-1">
              {formatScore(Math.min(99, Number(threat.risk_score) + 4))}<span className="text-xs font-medium text-slate-500">/100</span>
            </div>
            <span className="text-[10px] text-purple-400/80 font-medium">Multi-Platform Syndicate</span>
          </div>
        </div>
      </div>

      {/* WHY FLAGGED & RECOMMENDED ACTION BOXES */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Why Flagged */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-rose-400" />
            Why Flagged (Algorithmic Reasoning)
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800 font-sans">
            {threat.why_flagged}
          </p>
        </div>

        {/* Recommended Action */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Recommended SOC Action
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800 font-sans">
            {threat.recommended_action}
          </p>
        </div>
      </div>

      {/* SIDE-BY-SIDE COMPARISON (OFFICIAL VS SUSPICIOUS) */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Official vs Suspicious Identity Comparison
            </h3>
            <p className="text-[11px] text-slate-400">Side-by-side trademark and asset divergence audit</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* LEFT: OFFICIAL */}
          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/25 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" />
                Official Legitimate Asset
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                VERIFIED (0 RISK)
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-3">
                <img
                  src={comp.official?.logo || 'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=100'}
                  alt=""
                  className="w-12 h-12 rounded-xl object-cover bg-slate-800 border border-emerald-500/30"
                />
                <div>
                  <p className="font-bold text-white">{comp.official?.name || 'Official Brand Asset'}</p>
                  <p className="text-[11px] text-slate-400 font-mono">{comp.official?.username_or_dev}</p>
                </div>
              </div>
              <div className="pt-2 border-t border-emerald-900/30 space-y-1 text-[11px]">
                <p className="text-slate-400">
                  Platform: <strong className="text-slate-200">{comp.official?.platform}</strong>
                </p>
                <p className="text-slate-400 truncate">
                  Registered URL: <strong className="text-cyan-400">{comp.official?.url}</strong>
                </p>
              </div>
            </div>
          </div>

          {/* RIGHT: SUSPICIOUS */}
          <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/25 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                Suspicious Infringing Candidate
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                UNAUTHORIZED MISMATCH
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-3">
                <img
                  src={comp.suspicious?.logo || 'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=100'}
                  alt=""
                  className="w-12 h-12 rounded-xl object-cover bg-slate-800 border border-rose-500/30"
                />
                <div>
                  <p className="font-bold text-white">{comp.suspicious?.name || threat.account_or_app_name}</p>
                  <p className="text-[11px] text-slate-400 font-mono">{comp.suspicious?.username_or_dev || threat.username_or_package}</p>
                </div>
              </div>
              <div className="pt-2 border-t border-rose-900/30 space-y-1 text-[11px]">
                <p className="text-slate-400">
                  Targeted Channel: <strong className="text-slate-200">{threat.platform}</strong>
                </p>
                <p className="text-slate-400 truncate">
                  Infringing URL: <strong className="text-rose-400">{threat.url}</strong>
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Differences highlighted */}
        {comp.differences && comp.differences.length > 0 && (
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-1">
            <span className="text-[10px] font-bold uppercase text-slate-400 block tracking-wider">
              Identified Divergences & Impersonation Cues:
            </span>
            <ul className="list-disc list-inside space-y-0.5 text-rose-300 text-[11px]">
              {comp.differences.map((diff, i) => (
                <li key={i}>{diff}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* MULTI-SIGNAL DETECTION FACTORS PROGRESS BARS */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Multi-Signal Score Breakdown
          </h3>
          <p className="text-[11px] text-slate-400">Individual signal weights feeding the composite risk engine</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Name Similarity */}
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-300 font-semibold">Name Resemblance (RapidFuzz / Lookalike)</span>
              <strong className="text-cyan-400">{factors.name_similarity || 0}%</strong>
            </div>
            <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
              <div className="h-full bg-cyan-400 rounded-full" style={{ width: `${factors.name_similarity || 0}%` }} />
            </div>
            <p className="text-[10px] text-slate-500 font-mono">{factors.lookalike_explanation || 'Fuzzy pattern match.'}</p>
          </div>

          {/* Logo Similarity */}
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-300 font-semibold">Logo Perceptual Hash (dHash)</span>
              <strong className="text-purple-400">{factors.logo_similarity || 0}%</strong>
            </div>
            <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
              <div className="h-full bg-purple-400 rounded-full" style={{ width: `${factors.logo_similarity || 0}%` }} />
            </div>
            <p className="text-[10px] text-slate-500">Visual correlation with official registered brand mark.</p>
          </div>

          {/* Customer Targeting Score */}
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-300 font-semibold">Customer Targeting & Deceptive Intent</span>
              <strong className="text-amber-400">{factors.customer_targeting_score || 0}%</strong>
            </div>
            <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
              <div className="h-full bg-amber-400 rounded-full" style={{ width: `${factors.customer_targeting_score || 0}%` }} />
            </div>
            <p className="text-[10px] text-slate-500">
              Triggers: {factors.targeting_phrases?.join(', ') || 'Customer support / OTP extraction claims.'}
            </p>
          </div>

          {/* Official Registry Mismatch */}
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-300 font-semibold">Official Asset Registry Mismatch</span>
              <strong className="text-rose-400">{factors.official_mismatch || 100}%</strong>
            </div>
            <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
              <div className="h-full bg-rose-400 rounded-full" style={{ width: `${factors.official_mismatch || 100}%` }} />
            </div>
            <p className="text-[10px] text-slate-500">Asset is absent from verified brand registry (100% mismatch).</p>
          </div>
        </div>
      </div>

      {/* ANALYST INVESTIGATION NOTES */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-cyan-400" />
            Analyst Investigation Notes & Audit Trail
          </h3>
          <p className="text-[11px] text-slate-400">Collaborative case commentary persisted to MongoDB</p>
        </div>

        {/* Existing Notes List */}
        <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
          {threat.notes && threat.notes.length > 0 ? (
            threat.notes.map((note, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-bold text-cyan-300">{note.author}</span>
                  <span className="text-slate-500 font-mono">
                    {new Date(note.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-slate-300 text-xs leading-relaxed">{note.text}</p>
              </div>
            ))
          ) : (
            <p className="text-slate-500 text-xs italic">No analyst notes recorded yet.</p>
          )}
        </div>

        {/* Add Note Form */}
        <form onSubmit={handleAddNote} className="flex gap-2 pt-2 border-t border-slate-800">
          <input
            type="text"
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Add investigation findings or evidence note..."
            className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={!newNote.trim()}
            className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Add Note</span>
          </button>
        </form>
      </div>
    </div>
  );
}
