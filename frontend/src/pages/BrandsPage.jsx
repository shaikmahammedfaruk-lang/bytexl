import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  PlusCircle,
  ShieldCheck,
  ArrowRight,
  Archive,
  Search,
  Edit,
  Trash2,
  AlertTriangle,
  X,
  CheckCircle2,
  Globe,
  Tag
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { updateBrand, deleteBrand } from '../services/api';
import EditBrandWizardModal from '../components/EditBrandWizardModal';

export default function BrandsPage() {
  const navigate = useNavigate();
  const { brands, refreshBrands, setSelectedBrand, setIsAddBrandOpen } = useBrand();
  const [search, setSearch] = useState('');

  // Edit Brand Modal State
  const [editingBrand, setEditingBrand] = useState(null);
  const [editForm, setEditForm] = useState({
    name: '',
    industry: '',
    website: '',
    logo_url: '',
    description: '',
    brand_keywords: '',
    brand_aliases: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalError, setModalError] = useState('');

  // Delete Brand Confirmation Dialog State
  const [deletingBrand, setDeletingBrand] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const filteredBrands = brands.filter(
    (b) =>
      b.name.toLowerCase().includes(search.toLowerCase()) ||
      b.industry?.toLowerCase().includes(search.toLowerCase())
  );

  const openEditModal = (brand, e) => {
    e.stopPropagation();
    setEditingBrand(brand);
    setEditForm({
      name: brand.name || '',
      industry: brand.industry || 'Other',
      website: brand.website || '',
      logo_url: brand.logo_url || '',
      description: brand.description || '',
      brand_keywords: Array.isArray(brand.brand_keywords) ? brand.brand_keywords.join(', ') : '',
      brand_aliases: Array.isArray(brand.brand_aliases) ? brand.brand_aliases.join(', ') : ''
    });
    setModalError('');
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editForm.name.trim()) {
      setModalError('Brand name is required.');
      return;
    }

    setIsSubmitting(true);
    setModalError('');
    try {
      const kwList = editForm.brand_keywords.split(',').map((k) => k.trim()).filter(Boolean);
      const aliasList = editForm.brand_aliases.split(',').map((a) => a.trim()).filter(Boolean);

      await updateBrand(editingBrand.id, {
        name: editForm.name.trim(),
        industry: editForm.industry.trim(),
        website: editForm.website.trim(),
        logo_url: editForm.logo_url.trim(),
        description: editForm.description.trim(),
        brand_keywords: kwList,
        brand_aliases: aliasList
      });

      setEditingBrand(null);
      setToastMessage(`Brand '${editForm.name}' updated successfully.`);
      setTimeout(() => setToastMessage(''), 3500);
      await refreshBrands();
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to update brand profile.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openDeleteDialog = (brand, e) => {
    e.stopPropagation();
    setDeletingBrand(brand);
  };

  const handleConfirmDelete = async () => {
    if (!deletingBrand) return;
    setDeleteLoading(true);
    try {
      await deleteBrand(deletingBrand.id, true);
      const deletedName = deletingBrand.name;
      setDeletingBrand(null);
      setToastMessage(`Brand profile '${deletedName}' and dependent records deleted.`);
      setTimeout(() => setToastMessage(''), 3500);
      await refreshBrands();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete brand.');
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

      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Building2 className="w-5 h-5 text-cyan-400" />
            Monitored Brand Profiles
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Define legitimate assets, official registries, and whitelisted infrastructure.
          </p>
        </div>
        <button
          onClick={() => setIsAddBrandOpen(true)}
          className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-2 shadow-md shadow-cyan-500/20 active:scale-95 transition"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Add New Brand</span>
        </button>
      </div>

      {/* Official Exclusion Callout Banner */}
      <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/20 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs space-y-0.5">
          <h4 className="font-bold text-emerald-300">Official Asset Exclusion Protocol</h4>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            All social profiles, apps, and domains registered under a brand profile are verified and treated as <strong>Trusted Assets</strong> with 0 Threat Risk.
            The detection engine evaluates these assets before flagging candidate threats to guarantee <strong>Zero False Positives</strong> for official handles.
          </p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <p className="text-xs text-slate-400">
          {filteredBrands.length} of {brands.length} brand profiles
        </p>
        <label className="relative block w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search brand profiles..."
            aria-label="Search brand profiles"
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </label>
      </div>

      {/* Brands Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredBrands.map((brand) => (
          <div
            key={brand.id}
            onClick={() => {
              setSelectedBrand(brand);
              navigate(`/brands/${brand.id}`);
            }}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/50 cursor-pointer transition-all hover:shadow-xl hover:shadow-cyan-950/20 group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {brand.logo_url ? (
                    <img
                      src={brand.logo_url}
                      alt={`${brand.name} logo`}
                      className="w-12 h-12 rounded-xl object-cover bg-slate-800 border border-slate-700"
                    />
                  ) : (
                    <div
                      aria-hidden="true"
                      className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-sm font-bold text-cyan-300"
                    >
                      {brand.name.slice(0, 2).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <h3 className="font-bold text-sm text-white group-hover:text-cyan-300 transition-colors">
                      {brand.name}
                    </h3>
                    <p className="text-[11px] text-slate-400">{brand.industry}</p>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  Active
                </span>
              </div>

              <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                {brand.description || "Official brand identity monitored by BrandShield AI."}
              </p>

              {/* Verified Assets and Threats counts */}
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80 text-xs">
                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">Official Assets:</span>
                  <span className="font-bold text-emerald-400">{brand.official_assets_count || 0}</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">Active Threats:</span>
                  <span className="font-bold text-rose-400">{brand.active_threats_count || 0}</span>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs mt-3">
              <span className="text-cyan-400 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                <span>Manage Profile & Assets</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </span>

              {/* Action Buttons: Edit & Delete */}
              <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={(e) => openEditModal(brand, e)}
                  className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-cyan-300 transition"
                  title="Edit Brand Profile"
                  aria-label="Edit Brand Profile"
                >
                  <Edit className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={(e) => openDeleteDialog(brand, e)}
                  className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 transition"
                  title="Delete Brand Profile"
                  aria-label="Delete Brand Profile"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredBrands.length === 0 && (
        <div className="py-10 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/40">
          <Building2 className="w-8 h-8 text-slate-500 mx-auto mb-3" />
          <h2 className="text-sm font-semibold text-white">
            {brands.length === 0 ? 'No brand profiles yet' : 'No matching brands'}
          </h2>
          <p className="text-xs text-slate-400 mt-1 mb-4">
            {brands.length === 0
              ? 'Add a brand to begin monitoring its official assets.'
              : 'Try another name or industry, or add a new brand profile.'}
          </p>
          <button
            onClick={() => setIsAddBrandOpen(true)}
            className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold inline-flex items-center gap-2 transition"
          >
            <PlusCircle className="w-4 h-4" />
            Add New Brand
          </button>
        </div>
      )}

      {/* 6-STEP EDIT BRAND WIZARD MODAL */}
      <EditBrandWizardModal
        isOpen={Boolean(editingBrand)}
        onClose={() => setEditingBrand(null)}
        brandId={editingBrand?.id}
        onBrandUpdated={() => {
          setEditingBrand(null);
          refreshBrands();
        }}
      />

      {/* DELETE CONFIRMATION DIALOG */}
      {deletingBrand && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0b101e] border border-rose-500/30 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400 flex-shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Delete Brand Profile</h3>
                <p className="text-xs text-slate-400">This action permanently deletes monitored assets.</p>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2">
              <p className="text-slate-300">
                Are you sure you want to permanently delete <strong className="text-white">{deletingBrand.name}</strong>?
              </p>
              <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-300">
                ⚠️ This brand has <strong>{deletingBrand.official_assets_count || 0} official assets</strong> and{' '}
                <strong>{deletingBrand.active_threats_count || 0} active threats</strong>. Deleting this brand will cascade
                and remove all associated asset registries and threat records.
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDeletingBrand(null)}
                disabled={deleteLoading}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={deleteLoading}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-50"
              >
                {deleteLoading ? (
                  <span>Deleting...</span>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Confirm Delete</span>
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
