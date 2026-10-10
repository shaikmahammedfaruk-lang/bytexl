import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Flame,
  Search,
  Filter,
  FileText,
  SearchCode,
  CheckCircle2,
  AlertOctagon,
  Eye,
  ShieldAlert,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  Trash2,
  AlertTriangle,
  X
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import {
  getThreats,
  resolveThreat,
  markThreatReviewed,
  markThreatLegitimate,
  createInvestigation,
  deleteThreat,
  bulkDeleteThreats
} from '../services/api';
import { formatScore } from '../utils/formatters';

const TABS = [
  { id: 'ALL', label: 'All Threats' },
  { id: 'social', label: 'Social' },
  { id: 'app', label: 'Apps' },
  { id: 'CRITICAL', label: 'Critical' },
  { id: 'NEW', label: 'New' },
  { id: 'UNDER_INVESTIGATION', label: 'Investigating' },
  { id: 'RESOLVED', label: 'Resolved' },
];

export default function ThreatCenterPage() {
  const navigate = useNavigate();
  const { selectedBrand, openEvidenceModal, refreshBrands, refreshAlertsCount } = useBrand();

  const [activeTab, setActiveTab] = useState('ALL');
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Bulk and Single Delete States
  const [selectedIds, setSelectedIds] = useState([]);
  const [isBulkDeleteOpen, setIsBulkDeleteOpen] = useState(false);
  const [bulkDeleteLoading, setBulkDeleteLoading] = useState(false);
  const [deletingThreat, setDeletingThreat] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  const fetchThreats = async () => {
    if (!selectedBrand) return;
    setLoading(true);
    try {
      const params = { brand_id: selectedBrand.id, search: search.trim() || undefined };
      if (activeTab === 'social' || activeTab === 'app') {
        params.asset_type = activeTab;
      } else if (activeTab === 'CRITICAL') {
        params.risk_level = 'CRITICAL';
      } else if (activeTab !== 'ALL') {
        params.status = activeTab;
      }

      const res = await getThreats(params);
      setThreats(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThreats();
  }, [selectedBrand, activeTab]);

  // Synchronize selection when threats list updates
  useEffect(() => {
    setSelectedIds(prev => prev.filter(id => threats.some(t => t.id === id)));
  }, [threats]);

  // Selection handlers
  const allSelected = threats.length > 0 && threats.every(t => selectedIds.includes(t.id));
  const someSelected = threats.length > 0 && threats.some(t => selectedIds.includes(t.id));

  const handleToggleSelectAll = () => {
    if (allSelected) {
      const visibleIds = new Set(threats.map(t => t.id));
      setSelectedIds(prev => prev.filter(id => !visibleIds.has(id)));
    } else {
      const combined = new Set([...selectedIds, ...threats.map(t => t.id)]);
      setSelectedIds(Array.from(combined));
    }
  };

  const handleToggleSelect = (id, e) => {
    e.stopPropagation();
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const handleClearSelection = () => {
    setSelectedIds([]);
  };

  // Bulk Delete
  const handleConfirmBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    setBulkDeleteLoading(true);
    try {
      const countToDelete = selectedIds.length;
      await bulkDeleteThreats(selectedIds);
      setStatusMessage({
        type: 'success',
        text: `Successfully deleted ${countToDelete} threat record${countToDelete > 1 ? 's' : ''}.`
      });
      setSelectedIds([]);
      setIsBulkDeleteOpen(false);
      await fetchThreats();
      if (refreshBrands) refreshBrands();
      if (refreshAlertsCount) refreshAlertsCount();
    } catch (err) {
      console.error("Bulk delete failed", err);
      setStatusMessage({
        type: 'error',
        text: err.response?.data?.detail || "Failed to delete selected threat records."
      });
    } finally {
      setBulkDeleteLoading(false);
    }
  };

  // Single Delete
  const handleOpenSingleDelete = (threat, e) => {
    e.stopPropagation();
    setDeletingThreat(threat);
  };

  const handleConfirmSingleDelete = async () => {
    if (!deletingThreat) return;
    setActionLoading(true);
    try {
      await deleteThreat(deletingThreat.id);
      setStatusMessage({
        type: 'success',
        text: `Threat record "${deletingThreat.account_or_app_name}" deleted successfully.`
      });
      setSelectedIds(prev => prev.filter(id => id !== deletingThreat.id));
      setDeletingThreat(null);
      await fetchThreats();
      if (refreshBrands) refreshBrands();
      if (refreshAlertsCount) refreshAlertsCount();
    } catch (err) {
      console.error("Single delete failed", err);
      setStatusMessage({
        type: 'error',
        text: err.response?.data?.detail || "Failed to delete threat record."
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async (id, e) => {
    e.stopPropagation();
    await resolveThreat(id);
    fetchThreats();
    if (refreshBrands) refreshBrands();
    if (refreshAlertsCount) refreshAlertsCount();
  };

  const handleReview = async (id, e) => {
    e.stopPropagation();
    await markThreatReviewed(id);
    fetchThreats();
  };

  const handleLegitimate = async (id, e) => {
    e.stopPropagation();
    if (confirm("Mark this entity as Legitimate? This tunes False Positive Protection for future scans.")) {
      await markThreatLegitimate(id);
      fetchThreats();
      if (refreshBrands) refreshBrands();
    }
  };

  const handleInvestigate = async (threat, e) => {
    e.stopPropagation();
    try {
      const res = await createInvestigation({ threat_id: threat.id });
      navigate(`/investigations/${res.data.id}`);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Flame className="w-5 h-5 text-rose-500" />
            Digital Risk Threat Center
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Centralized triage queue for brand impersonation across social platforms and app stores.
          </p>
        </div>
      </div>

      {/* Status Notification */}
      {statusMessage && (
        <div className={`p-3.5 rounded-xl border flex items-center justify-between text-xs transition-all ${
          statusMessage.type === 'success'
            ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300'
            : 'bg-rose-950/40 border-rose-500/30 text-rose-300'
        }`}>
          <div className="flex items-center gap-2">
            {statusMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            ) : (
              <AlertOctagon className="w-4 h-4 text-rose-400 flex-shrink-0" />
            )}
            <span>{statusMessage.text}</span>
          </div>
          <button
            onClick={() => setStatusMessage(null)}
            className="p-1 hover:text-white rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs border-b border-slate-800">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3.5 py-2 font-semibold border-b-2 transition -mb-[2px] ${
              activeTab === tab.id
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search Input and Record Counter */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
        <div className="relative w-full sm:w-96">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchThreats()}
            placeholder="Search by asset name, platform, handle, URL..."
            className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 text-xs"
          />
        </div>
        <span className="text-[11px] text-slate-500 hidden sm:inline">
          Showing <strong className="text-slate-200">{threats.length}</strong> active threat candidates
        </span>
      </div>

      {/* Selection Action Bar (Appears when items are selected) */}
      {selectedIds.length > 0 && (
        <div className="p-3.5 rounded-xl bg-gradient-to-r from-cyan-950/50 via-slate-900/80 to-rose-950/30 border border-cyan-500/40 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-lg shadow-cyan-950/20 animate-fadeIn">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
            <span className="text-xs text-slate-200">
              <strong className="text-white font-bold text-sm mr-1">{selectedIds.length}</strong>
              {selectedIds.length === 1 ? 'threat record' : 'threat records'} selected across current filter
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleClearSelection}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition border border-slate-700"
            >
              Deselect All
            </button>
            <button
              type="button"
              onClick={() => setIsBulkDeleteOpen(true)}
              className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-rose-950/40 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete Selected ({selectedIds.length})</span>
            </button>
          </div>
        </div>
      )}

      {/* Threats Table */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase font-bold tracking-wider">
                <th className="py-3 px-3 w-10 text-center">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = someSelected && !allSelected;
                    }}
                    onChange={handleToggleSelectAll}
                    aria-label="Select all threats"
                    className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500/20 cursor-pointer accent-cyan-500"
                  />
                </th>
                <th className="py-3 px-3">Entity</th>
                <th className="py-3 px-3">Type</th>
                <th className="py-3 px-3">Platform</th>
                <th className="py-3 px-3">Threat Risk</th>
                <th className="py-3 px-3">Customer Impact</th>
                <th className="py-3 px-3">Confidence</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {threats.length > 0 ? (
                threats.map((threat) => {
                  const isSelected = selectedIds.includes(threat.id);
                  return (
                    <tr
                      key={threat.id}
                      onClick={() => navigate(`/threats/${threat.id}`)}
                      className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                        isSelected ? 'bg-cyan-950/20' : ''
                      }`}
                    >
                      <td
                        className="py-3.5 px-3 text-center"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => handleToggleSelect(threat.id, e)}
                          aria-label={`Select ${threat.account_or_app_name}`}
                          className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500/20 cursor-pointer accent-cyan-500"
                        />
                      </td>

                      <td className="py-3.5 px-3">
                        <div className="flex items-center gap-3">
                          <img
                            src={threat.profile_or_icon_url || 'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=100'}
                            alt=""
                            className="w-8 h-8 rounded-lg object-cover bg-slate-800 border border-slate-700 flex-shrink-0"
                          />
                          <div className="truncate max-w-[200px]">
                            <p className="font-semibold text-slate-200 truncate">{threat.account_or_app_name}</p>
                            <p className="text-[11px] text-slate-500 font-mono truncate">{threat.username_or_package || threat.url}</p>
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                          {threat.threat_type}
                        </span>
                      </td>

                      <td className="py-3.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800/80 text-cyan-300">
                          {threat.platform}
                        </span>
                      </td>

                      <td className="py-3.5 px-3">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`font-black text-xs ${
                              threat.risk_score >= 71
                                ? 'text-rose-400'
                                : threat.risk_score >= 41
                                ? 'text-orange-400'
                                : 'text-amber-400'
                            }`}
                          >
                            {formatScore(threat.risk_score)}/100
                          </span>
                          <span
                            className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                              threat.risk_score >= 71
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                            }`}
                          >
                            {threat.risk_level}
                          </span>
                        </div>
                      </td>

                      <td className="py-3.5 px-3">
                        <span className="text-amber-400 font-bold">{formatScore(threat.customer_impact_score)}/100</span>
                      </td>

                      <td className="py-3.5 px-3 text-cyan-400 font-semibold">
                        {formatScore(threat.confidence)}%
                      </td>

                      <td className="py-3.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            threat.status === 'RESOLVED'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : threat.status === 'LEGITIMATE_FALSE_POSITIVE'
                              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                              : threat.status === 'REVIEWED'
                              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                              : threat.status === 'UNDER_INVESTIGATION'
                              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          }`}
                        >
                          {threat.status}
                        </span>
                      </td>

                      <td className="py-3.5 px-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={(e) => handleInvestigate(threat, e)}
                            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-[10px] font-semibold border border-slate-700 flex items-center gap-1"
                            title="Open AI Threat Investigation"
                          >
                            <SearchCode className="w-3 h-3" />
                            <span>Investigate</span>
                          </button>

                          <button
                            onClick={() => openEvidenceModal(threat.id)}
                            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-400"
                            title="Generate Evidence Package"
                          >
                            <FileText className="w-3.5 h-3.5" />
                          </button>

                          {threat.status !== 'REVIEWED' && threat.status !== 'RESOLVED' && (
                            <button
                              onClick={(e) => handleReview(threat.id, e)}
                              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-semibold"
                            >
                              Review
                            </button>
                          )}

                          {threat.status !== 'RESOLVED' && (
                            <button
                              onClick={(e) => handleResolve(threat.id, e)}
                              className="px-2 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold"
                            >
                              Resolve
                            </button>
                          )}

                          {threat.status !== 'LEGITIMATE_FALSE_POSITIVE' && (
                            <button
                              onClick={(e) => handleLegitimate(threat.id, e)}
                              className="px-2 py-1 rounded hover:bg-slate-800 text-slate-500 hover:text-slate-300 text-[10px]"
                              title="Mark as Legitimate (False Positive Protection)"
                            >
                              Legitimate
                            </button>
                          )}

                          {/* Individual Row Delete Button */}
                          <button
                            onClick={(e) => handleOpenSingleDelete(threat, e)}
                            className="p-1.5 rounded hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 transition"
                            title="Delete Threat Record"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="9" className="py-8 text-center text-slate-500 text-xs">
                    No threat entries found under this tab.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bulk Delete Confirmation Modal */}
      {isBulkDeleteOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-rose-500/40 rounded-2xl p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-start gap-3">
              <div className="p-3 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-400 flex-shrink-0">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-white">Delete Selected Threats?</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  You are about to permanently delete <strong className="text-rose-300">{selectedIds.length}</strong> selected threat records and their associated security alerts from the database.
                </p>
                <div className="p-2.5 rounded-lg bg-rose-950/30 border border-rose-900/50 text-[11px] text-rose-300 font-mono mt-2">
                  Warning: This action is permanent and cannot be undone.
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                disabled={bulkDeleteLoading}
                onClick={() => setIsBulkDeleteOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={bulkDeleteLoading}
                onClick={handleConfirmBulkDelete}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 disabled:opacity-50 transition flex items-center gap-1.5 shadow-lg shadow-rose-900/40"
              >
                {bulkDeleteLoading ? (
                  <>
                    <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>Deleting {selectedIds.length}...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete {selectedIds.length} Records</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Single Threat Delete Confirmation Modal */}
      {deletingThreat && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-rose-500/40 rounded-2xl p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-start gap-3">
              <div className="p-3 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-400 flex-shrink-0">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-white">Delete Threat Record?</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Are you sure you want to permanently delete the threat record for <strong className="text-white">"{deletingThreat.account_or_app_name}"</strong> on <span className="text-cyan-400 font-semibold">{deletingThreat.platform}</span>?
                </p>
                <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800 text-[11px] text-slate-400 space-y-1 mt-2">
                  <div className="truncate"><span className="text-slate-500">Identifier:</span> <span className="text-slate-300 font-mono">{deletingThreat.username_or_package || deletingThreat.url}</span></div>
                  <div><span className="text-slate-500">Risk Score:</span> <span className="text-rose-400 font-bold">{deletingThreat.risk_score}/100 ({deletingThreat.risk_level})</span></div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                disabled={actionLoading}
                onClick={() => setDeletingThreat(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={actionLoading}
                onClick={handleConfirmSingleDelete}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 disabled:opacity-50 transition flex items-center gap-1.5 shadow-lg shadow-rose-900/40"
              >
                {actionLoading ? (
                  <>
                    <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete Record</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
