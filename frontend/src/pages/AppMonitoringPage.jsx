import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Smartphone,
  Search,
  Filter,
  Plus,
  Flame,
  FileText,
  Star,
  Download,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Edit,
  Trash2,
  X,
  ExternalLink,
  ShieldAlert,
  RefreshCw
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import {
  getAppThreats,
  scanApp,
  updateAppThreat,
  deleteAppThreat,
  resolveThreat
} from '../services/api';
import { formatScore } from '../utils/formatters';

const STORES = ['ALL', 'Google Play', 'Apple App Store'];
const RISK_LEVELS = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

export default function AppMonitoringPage() {
  const navigate = useNavigate();
  const { selectedBrand, openEvidenceModal, refreshBrands } = useBrand();

  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStore, setSelectedStore] = useState('ALL');
  const [selectedRisk, setSelectedRisk] = useState('ALL');
  const [search, setSearch] = useState('');
  const [toastMessage, setToastMessage] = useState('');

  // Scan App Modal State
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [scanForm, setScanForm] = useState({
    store: 'Google Play',
    url: '',
    package_id: '',
    app_name: '',
    developer: '',
    description: ''
  });
  const [scanLoading, setScanLoading] = useState(false);
  const [scanError, setScanError] = useState('');

  // Edit App Modal State
  const [editingThreat, setEditingThreat] = useState(null);
  const [editForm, setEditForm] = useState({
    account_or_app_name: '',
    developer_name: '',
    username_or_package: '',
    platform: 'Google Play',
    bio_or_description: '',
    status: 'NEW',
    analyst_assigned: ''
  });
  const [editLoading, setEditLoading] = useState(false);

  // Delete Dialog State
  const [deletingThreat, setDeletingThreat] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const fetchAppThreats = async () => {
    if (!selectedBrand) return;
    setLoading(true);
    try {
      const res = await getAppThreats({
        brand_id: selectedBrand.id,
        store: selectedStore !== 'ALL' ? selectedStore : undefined,
        risk_level: selectedRisk !== 'ALL' ? selectedRisk : undefined,
        search: search.trim() || undefined
      });
      setThreats(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppThreats();
  }, [selectedBrand, selectedStore, selectedRisk]);

  const handleResolve = async (id, e) => {
    e.stopPropagation();
    try {
      await resolveThreat(id);
      setToastMessage('Mobile app threat marked as resolved.');
      setTimeout(() => setToastMessage(''), 3000);
      fetchAppThreats();
      refreshBrands();
    } catch (err) {
      console.error(err);
    }
  };

  const handleScanSubmit = async (e) => {
    e.preventDefault();
    if (!scanForm.url.trim() && !scanForm.package_id.trim()) {
      setScanError('Please enter an App URL or Package ID.');
      return;
    }
    if (!selectedBrand) {
      setScanError('No active brand selected.');
      return;
    }

    setScanLoading(true);
    setScanError('');
    try {
      const payloadUrl = scanForm.url.trim() || `https://play.google.com/store/apps/details?id=${scanForm.package_id.trim()}`;
      const res = await scanApp({
        brand_id: selectedBrand.id,
        url: payloadUrl,
        store: scanForm.store,
        package_id: scanForm.package_id.trim() || undefined,
        app_name: scanForm.app_name.trim() || undefined,
        developer: scanForm.developer.trim() || undefined,
        description: scanForm.description.trim() || undefined
      });

      setIsScanOpen(false);
      setScanForm({
        store: 'Google Play',
        url: '',
        package_id: '',
        app_name: '',
        developer: '',
        description: ''
      });
      setToastMessage(res.data?.message || 'Application scanned successfully.');
      setTimeout(() => setToastMessage(''), 3500);
      await fetchAppThreats();
      refreshBrands();
    } catch (err) {
      setScanError(err.response?.data?.detail || 'Scan failed. Check URL or parameters.');
    } finally {
      setScanLoading(false);
    }
  };

  const openEditModal = (threat, e) => {
    e.stopPropagation();
    setEditingThreat(threat);
    setEditForm({
      account_or_app_name: threat.account_or_app_name || '',
      developer_name: threat.developer_name || '',
      username_or_package: threat.username_or_package || '',
      platform: threat.platform || 'Google Play',
      bio_or_description: threat.bio_or_description || '',
      status: threat.status || 'NEW',
      analyst_assigned: threat.analyst_assigned || 'SecOps App Reviewer'
    });
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editingThreat) return;
    setEditLoading(true);
    try {
      await updateAppThreat(editingThreat.id, editForm);
      setEditingThreat(null);
      setToastMessage('Application record updated successfully.');
      setTimeout(() => setToastMessage(''), 3000);
      fetchAppThreats();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update application record.');
    } finally {
      setEditLoading(false);
    }
  };

  const openDeleteDialog = (threat, e) => {
    e.stopPropagation();
    setDeletingThreat(threat);
  };

  const handleDeleteConfirm = async () => {
    if (!deletingThreat) return;
    setDeleteLoading(true);
    try {
      await deleteAppThreat(deletingThreat.id);
      setDeletingThreat(null);
      setToastMessage('Mobile app record deleted.');
      setTimeout(() => setToastMessage(''), 3000);
      fetchAppThreats();
      refreshBrands();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete app record.');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-fade-in shadow-lg">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-purple-400" />
            Mobile App Store Monitoring
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Detect rogue mobile applications, developer mismatch spoofing, and rogue APK packages.
          </p>
        </div>

        <button
          onClick={() => {
            setIsScanOpen(true);
            setScanError('');
          }}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-400 hover:to-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-md shadow-purple-500/20 active:scale-95 transition"
        >
          <Plus className="w-4 h-4" />
          <span>Scan Mobile App</span>
        </button>
      </div>

      {/* Store Filter Tabs & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1.5 w-full sm:w-auto">
          {STORES.map((s) => (
            <button
              key={s}
              onClick={() => setSelectedStore(s)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                selectedStore === s
                  ? 'bg-purple-500 text-white shadow-sm'
                  : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search app name, developer, package..."
              className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 text-xs"
            />
          </div>

          <select
            value={selectedRisk}
            onChange={(e) => setSelectedRisk(e.target.value)}
            className="px-2.5 py-1 bg-slate-950 border border-slate-800 rounded-md text-white text-xs"
          >
            {RISK_LEVELS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* App Threats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {threats.length > 0 ? (
          threats.map((threat) => (
            <div
              key={threat.id}
              onClick={() => navigate(`/threats/${threat.id}`)}
              className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-purple-500/50 cursor-pointer transition-all hover:shadow-xl hover:shadow-purple-950/20 flex flex-col justify-between space-y-4 group"
            >
              <div className="space-y-3">
                {/* Header row */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <img
                      src={threat.profile_or_icon_url || 'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=100'}
                      alt=""
                      className="w-12 h-12 rounded-xl object-cover bg-slate-800 border border-slate-700"
                    />
                    <div>
                      <h3 className="font-bold text-sm text-white group-hover:text-purple-300 transition-colors">
                        {threat.account_or_app_name}
                      </h3>
                      <p className="text-[11px] text-slate-400 font-mono truncate max-w-[170px]">{threat.username_or_package}</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-purple-300 border border-slate-700">
                    {threat.platform}
                  </span>
                </div>

                {/* Developer Mismatch Alert Tag */}
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-400">Developer Entity:</span>
                  <span className="font-semibold text-rose-400 truncate max-w-[140px]">
                    {threat.developer_name || 'Unauthorized Dev'}
                  </span>
                </div>

                {/* Score Indicators: Threat Risk & Customer Impact */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800">
                    <span className="text-[9px] font-bold uppercase text-slate-400 block">Threat Risk</span>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span
                        className={`text-base font-black ${
                          threat.risk_score >= 71 ? 'text-rose-400' : 'text-orange-400'
                        }`}
                      >
                        {formatScore(threat.risk_score)}/100
                      </span>
                      <span className="text-[9px] font-bold text-rose-400 uppercase">
                        {threat.risk_level}
                      </span>
                    </div>
                  </div>

                  <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800">
                    <span className="text-[9px] font-bold uppercase text-slate-400 block">Customer Impact</span>
                    <div className="text-base font-black text-amber-400 mt-0.5">
                      {formatScore(threat.customer_impact_score)}/100
                    </div>
                  </div>
                </div>

                {/* Why Flagged */}
                <p className="text-[11px] text-slate-400 line-clamp-2">
                  <strong className="text-slate-300">Finding:</strong> {threat.why_flagged}
                </p>
              </div>

              {/* Footer Actions */}
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs" onClick={(e) => e.stopPropagation()}>
                <span className="text-[10px] text-slate-500 font-mono">
                  {new Date(threat.detected_time).toLocaleDateString()}
                </span>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={(e) => openEditModal(threat, e)}
                    className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-purple-400 transition"
                    title="Edit Record Details"
                  >
                    <Edit className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={(e) => openDeleteDialog(threat, e)}
                    className="p-1.5 rounded hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 transition"
                    title="Delete Record"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => openEvidenceModal(threat.id)}
                    className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-400"
                    title="Generate Evidence Package"
                  >
                    <FileText className="w-3.5 h-3.5" />
                  </button>

                  {threat.status !== 'RESOLVED' && (
                    <button
                      onClick={(e) => handleResolve(threat.id, e)}
                      className="px-2 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold"
                    >
                      Resolve
                    </button>
                  )}

                  <button
                    onClick={() => navigate(`/threats/${threat.id}`)}
                    className="px-2.5 py-1 rounded bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 text-[10px] font-semibold border border-purple-500/30 flex items-center gap-1"
                  >
                    <span>Inspect</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full py-12 text-center text-slate-500 text-xs">
            No mobile applications match the current filters.
          </div>
        )}
      </div>

      {/* SCAN MOBILE APP MODAL */}
      {isScanOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0b101e] border border-slate-700/80 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-bold text-white">Scan Mobile Application</h3>
              </div>
              <button onClick={() => setIsScanOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            {scanError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{scanError}</span>
              </div>
            )}

            <form onSubmit={handleScanSubmit} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    App Store
                  </label>
                  <select
                    value={scanForm.store}
                    onChange={(e) => setScanForm({ ...scanForm, store: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                  >
                    <option value="Google Play">Google Play</option>
                    <option value="Apple App Store">Apple App Store</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Package / Bundle ID (e.g. com.brand.app)
                  </label>
                  <input
                    type="text"
                    value={scanForm.package_id}
                    onChange={(e) => setScanForm({ ...scanForm, package_id: e.target.value })}
                    placeholder="com.bank.online"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono focus:outline-none focus:border-purple-400"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                  App Store URL
                </label>
                <input
                  type="text"
                  value={scanForm.url}
                  onChange={(e) => setScanForm({ ...scanForm, url: e.target.value })}
                  placeholder="https://play.google.com/store/apps/details?id=..."
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Application Name
                  </label>
                  <input
                    type="text"
                    value={scanForm.app_name}
                    onChange={(e) => setScanForm({ ...scanForm, app_name: e.target.value })}
                    placeholder="e.g. Quick Support App"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                  />
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Developer Name
                  </label>
                  <input
                    type="text"
                    value={scanForm.developer}
                    onChange={(e) => setScanForm({ ...scanForm, developer: e.target.value })}
                    placeholder="e.g. Unknown Rogue Dev"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                  App Description / Permissions Note (Optional)
                </label>
                <textarea
                  rows={2}
                  value={scanForm.description}
                  onChange={(e) => setScanForm({ ...scanForm, description: e.target.value })}
                  placeholder="Enter credentials or PIN to receive cashback..."
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsScanOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={scanLoading}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-400 hover:to-indigo-500 text-white font-bold transition flex items-center gap-1.5 disabled:opacity-50"
                >
                  {scanLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <span>Execute App Scan</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT APP THREAT MODAL */}
      {editingThreat && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0b101e] border border-slate-700/80 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Edit className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-bold text-white">Edit Mobile Application Record</h3>
              </div>
              <button onClick={() => setEditingThreat(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Application Name
                  </label>
                  <input
                    type="text"
                    required
                    value={editForm.account_or_app_name}
                    onChange={(e) => setEditForm({ ...editForm, account_or_app_name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Package / Bundle ID
                  </label>
                  <input
                    type="text"
                    required
                    value={editForm.username_or_package}
                    onChange={(e) => setEditForm({ ...editForm, username_or_package: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono focus:outline-none focus:border-purple-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Developer Entity Name
                  </label>
                  <input
                    type="text"
                    value={editForm.developer_name}
                    onChange={(e) => setEditForm({ ...editForm, developer_name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                  />
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Store
                  </label>
                  <select
                    value={editForm.platform}
                    onChange={(e) => setEditForm({ ...editForm, platform: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                  >
                    <option value="Google Play">Google Play</option>
                    <option value="Apple App Store">Apple App Store</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Status
                  </label>
                  <select
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                  >
                    <option value="NEW">NEW</option>
                    <option value="UNDER_INVESTIGATION">UNDER_INVESTIGATION</option>
                    <option value="REVIEWED">REVIEWED</option>
                    <option value="RESOLVED">RESOLVED</option>
                    <option value="LEGITIMATE_FALSE_POSITIVE">LEGITIMATE_FALSE_POSITIVE</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Analyst Assigned
                  </label>
                  <input
                    type="text"
                    value={editForm.analyst_assigned}
                    onChange={(e) => setEditForm({ ...editForm, analyst_assigned: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  value={editForm.bio_or_description}
                  onChange={(e) => setEditForm({ ...editForm, bio_or_description: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-purple-400"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingThreat(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editLoading}
                  className="px-5 py-2 rounded-xl bg-purple-500 hover:bg-purple-400 text-white font-bold transition disabled:opacity-50"
                >
                  {editLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION DIALOG */}
      {deletingThreat && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0b101e] border border-rose-500/30 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400 flex-shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Delete Mobile App Record</h3>
                <p className="text-xs text-slate-400">Permanently removes application telemetry.</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to delete the record for{' '}
              <strong className="text-white">{deletingThreat.account_or_app_name}</strong> (
              <span className="font-mono text-purple-400">{deletingThreat.username_or_package}</span>)?
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDeletingThreat(null)}
                disabled={deleteLoading}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                disabled={deleteLoading}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-50"
              >
                {deleteLoading ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
