import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Building2,
  Globe,
  Share2,
  Smartphone,
  ShieldCheck,
  Plus,
  Trash2,
  Edit,
  ArrowLeft,
  ExternalLink,
  CheckCircle2,
  Link2,
  AlertCircle,
  AlertTriangle,
  X
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import {
  getBrand,
  updateBrand,
  deleteBrand,
  getOfficialAssets,
  addOfficialAsset,
  updateOfficialAsset,
  deleteOfficialAsset
} from '../services/api';
import EditBrandWizardModal from '../components/EditBrandWizardModal';

export default function BrandDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { brands, setSelectedBrand, openScanModal, refreshBrands } = useBrand();

  const [brand, setBrand] = useState(null);
  const [officialAssets, setOfficialAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState('');

  // Add Asset Modal state
  const [isAddAssetOpen, setIsAddAssetOpen] = useState(false);
  const [assetType, setAssetType] = useState('social');
  const [assetPlatform, setAssetPlatform] = useState('Instagram');
  const [assetName, setAssetName] = useState('');
  const [assetUrl, setAssetUrl] = useState('');
  const [assetIdentifier, setAssetIdentifier] = useState('');
  const [assetDev, setAssetDev] = useState('');

  // Edit Brand Modal State
  const [isEditBrandOpen, setIsEditBrandOpen] = useState(false);
  const [editBrandForm, setEditBrandForm] = useState({
    name: '',
    industry: '',
    website: '',
    logo_url: '',
    description: '',
    brand_keywords: '',
    brand_aliases: ''
  });
  const [editBrandLoading, setEditBrandLoading] = useState(false);

  // Delete Brand Dialog State
  const [isDeleteBrandOpen, setIsDeleteBrandOpen] = useState(false);
  const [deleteBrandLoading, setDeleteBrandLoading] = useState(false);

  // Edit Asset Modal State
  const [editingAsset, setEditingAsset] = useState(null);
  const [editAssetForm, setEditAssetForm] = useState({
    name: '',
    platform: '',
    url: '',
    identifier: '',
    developer_name: '',
    verification_status: 'VERIFIED'
  });
  const [editAssetLoading, setEditAssetLoading] = useState(false);

  const fetchBrandData = async () => {
    setLoading(true);
    try {
      let bData = null;
      try {
        const bRes = await getBrand(id);
        bData = bRes.data;
      } catch (e) {
        console.warn("Could not fetch brand from API, attempting context fallback", e);
        bData = (brands || []).find((b) => b.id === id || b._id === id);
      }

      if (bData) {
        setBrand(bData);
        setSelectedBrand(bData);
        setEditBrandForm({
          name: bData.name || '',
          industry: bData.industry || 'Other',
          website: bData.website || '',
          logo_url: bData.logo_url || '',
          description: bData.description || '',
          brand_keywords: Array.isArray(bData.brand_keywords) ? bData.brand_keywords.join(', ') : '',
          brand_aliases: Array.isArray(bData.brand_aliases) ? bData.brand_aliases.join(', ') : ''
        });

        try {
          const aRes = await getOfficialAssets(id);
          setOfficialAssets(aRes.data || []);
        } catch (assetErr) {
          console.warn("Could not load official assets", assetErr);
          setOfficialAssets([]);
        }
      } else {
        setBrand(null);
      }
    } catch (err) {
      console.error(err);
      setBrand(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBrandData();
  }, [id]);

  const handleEditBrandSubmit = async (e) => {
    e.preventDefault();
    setEditBrandLoading(true);
    try {
      const kwList = editBrandForm.brand_keywords.split(',').map((k) => k.trim()).filter(Boolean);
      const aliasList = editBrandForm.brand_aliases.split(',').map((a) => a.trim()).filter(Boolean);

      const res = await updateBrand(id, {
        name: editBrandForm.name.trim(),
        industry: editBrandForm.industry.trim(),
        website: editBrandForm.website.trim(),
        logo_url: editBrandForm.logo_url.trim(),
        description: editBrandForm.description.trim(),
        brand_keywords: kwList,
        brand_aliases: aliasList
      });

      setBrand(res.data);
      setSelectedBrand(res.data);
      setIsEditBrandOpen(false);
      setToastMessage('Brand details updated successfully.');
      setTimeout(() => setToastMessage(''), 3000);
      refreshBrands();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update brand profile.');
    } finally {
      setEditBrandLoading(false);
    }
  };

  const handleDeleteBrandConfirm = async () => {
    setDeleteBrandLoading(true);
    try {
      await deleteBrand(id, true);
      await refreshBrands();
      navigate('/brands');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete brand profile.');
      setDeleteBrandLoading(false);
    }
  };

  const handleAddAssetSubmit = async (e) => {
    e.preventDefault();
    try {
      await addOfficialAsset(id, {
        brand_id: id,
        name: assetName || `${brand?.name} Official Asset`,
        asset_type: assetType,
        platform: assetPlatform,
        url: assetUrl,
        identifier: assetIdentifier || assetUrl,
        developer_name: assetDev || brand?.name,
        verification_status: 'VERIFIED'
      });
      setIsAddAssetOpen(false);
      setAssetName('');
      setAssetUrl('');
      setAssetIdentifier('');
      setAssetDev('');
      fetchBrandData();
      refreshBrands();
    } catch (err) {
      console.error(err);
    }
  };

  const openEditAssetModal = (asset) => {
    setEditingAsset(asset);
    setEditAssetForm({
      name: asset.name || '',
      platform: asset.platform || '',
      url: asset.url || '',
      identifier: asset.identifier || '',
      developer_name: asset.developer_name || '',
      verification_status: asset.verification_status || 'VERIFIED'
    });
  };

  const handleEditAssetSubmit = async (e) => {
    e.preventDefault();
    if (!editingAsset) return;
    setEditAssetLoading(true);
    try {
      await updateOfficialAsset(id, editingAsset.id, {
        name: editAssetForm.name,
        platform: editAssetForm.platform,
        url: editAssetForm.url,
        identifier: editAssetForm.identifier,
        developer_name: editAssetForm.developer_name,
        verification_status: editAssetForm.verification_status
      });
      setEditingAsset(null);
      setToastMessage('Official asset updated.');
      setTimeout(() => setToastMessage(''), 3000);
      fetchBrandData();
      refreshBrands();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update asset.');
    } finally {
      setEditAssetLoading(false);
    }
  };

  const handleDeleteAsset = async (assetId) => {
    if (confirm("Remove this asset from verified registry?")) {
      await deleteOfficialAsset(id, assetId);
      fetchBrandData();
      refreshBrands();
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading brand profile...</div>;
  }

  if (!brand) {
    return <div className="p-8 text-center text-rose-400">Brand not found.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-fade-in shadow-lg">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Back button */}
      <button
        onClick={() => navigate('/brands')}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Brands</span>
      </button>

      {/* Brand Hero Card */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xl">
        <div className="flex items-center gap-4">
          <img
            src={brand.logo_url || 'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=200'}
            alt={brand.name}
            className="w-16 h-16 rounded-2xl object-cover bg-slate-800 border border-slate-700 shadow-md"
          />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white">{brand.name}</h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                DRP Monitored
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-slate-400">
              <span className="font-medium text-slate-300">{brand.industry}</span>
              {brand.website && (
                <>
                  <span className="text-slate-600">•</span>
                  <a href={brand.website} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline flex items-center gap-1">
                    <Globe className="w-3 h-3" />
                    <span>{brand.website}</span>
                  </a>
                </>
              )}
              {brand.official_instagram_username && (
                <>
                  <span className="text-slate-600">•</span>
                  <a
                    href={brand.official_instagram_url || `https://instagram.com/${brand.official_instagram_username}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-pink-400 hover:underline flex items-center gap-1"
                  >
                    <Share2 className="w-3 h-3" />
                    <span>@{brand.official_instagram_username}</span>
                  </a>
                </>
              )}
            </div>
            {brand.description && (
              <p className="text-xs text-slate-300 mt-2 max-w-xl leading-relaxed">{brand.description}</p>
            )}
          </div>
        </div>

        {/* Hero Actions */}
        <div className="flex items-center gap-2 w-full md:w-auto flex-wrap">
          <button
            onClick={() => setIsEditBrandOpen(true)}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 transition active:scale-95"
            title="Edit Brand Details"
          >
            <Edit className="w-3.5 h-3.5 text-cyan-400" />
            <span>Edit Brand</span>
          </button>

          <button
            onClick={() => setIsAddAssetOpen(true)}
            className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-2 shadow-md shadow-cyan-500/20 active:scale-95 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Add Official Asset</span>
          </button>

          <button
            onClick={() => setIsDeleteBrandOpen(true)}
            className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-slate-700 text-xs font-semibold transition"
            title="Delete Brand Profile"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Official Exclusion Rule Guarantee Banner */}
      <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-6 h-6 text-cyan-400 flex-shrink-0" />
          <div className="text-xs">
            <h4 className="font-bold text-cyan-300">Official Asset Registry (Exclusion Rule Engine)</h4>
            <p className="text-slate-300 text-[11px]">
              Every asset registered below is automatically guaranteed <strong>SAFE (0 Risk)</strong>. If scanned by mistake or audited by SOC analysts, it will never trigger impersonation alerts.
            </p>
          </div>
        </div>
        <button
          onClick={() => openScanModal(officialAssets[0]?.url || 'https://instagram.com/abcbank')}
          className="px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 text-xs font-semibold border border-cyan-500/30 whitespace-nowrap hidden sm:flex items-center gap-1.5"
        >
          <Link2 className="w-3.5 h-3.5" />
          <span>Verify Exclusion Scan</span>
        </button>
      </div>

      {/* Official Assets List */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Registered Legitimate Assets ({officialAssets.length})
            </h3>
            <p className="text-[11px] text-slate-400">
              Whitelisted social handles, genuine mobile applications, and authentic domains.
            </p>
          </div>
          <button
            onClick={() => setIsAddAssetOpen(true)}
            className="text-xs text-cyan-400 hover:underline flex items-center gap-1 font-semibold"
          >
            <Plus className="w-3 h-3" />
            <span>Add Asset</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {officialAssets.map((asset) => (
            <div
              key={asset.id}
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-start justify-between gap-3 group hover:border-slate-700 transition"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-slate-800 text-cyan-400 mt-0.5">
                  {asset.asset_type === 'social' ? (
                    <Share2 className="w-4 h-4" />
                  ) : asset.asset_type === 'app' ? (
                    <Smartphone className="w-4 h-4" />
                  ) : (
                    <Globe className="w-4 h-4" />
                  )}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-semibold text-xs text-white">{asset.name}</span>
                    <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      VERIFIED
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono">
                    {asset.identifier || asset.developer_name || asset.url}
                  </p>
                  <a
                    href={asset.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] text-cyan-400 hover:underline flex items-center gap-1 mt-0.5"
                  >
                    <span className="truncate max-w-[150px]">{asset.url}</span>
                    <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" />
                  </a>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => openEditAssetModal(asset)}
                  className="p-1 rounded text-slate-500 hover:text-cyan-400"
                  title="Edit official asset"
                >
                  <Edit className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleDeleteAsset(asset.id)}
                  className="p-1 rounded text-slate-500 hover:text-rose-400"
                  title="Delete official asset"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 6-STEP EDIT BRAND WIZARD MODAL */}
      <EditBrandWizardModal
        isOpen={isEditBrandOpen}
        onClose={() => setIsEditBrandOpen(false)}
        brandId={id}
        onBrandUpdated={(updatedBrand) => {
          if (updatedBrand) {
            setBrand(updatedBrand);
            setSelectedBrand(updatedBrand);
          }
          fetchBrandData();
          refreshBrands();
          setToastMessage('Brand profile & official assets updated successfully.');
          setTimeout(() => setToastMessage(''), 3000);
        }}
      />

      {/* DELETE BRAND CONFIRMATION DIALOG */}
      {isDeleteBrandOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0b101e] border border-rose-500/30 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400 flex-shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Delete Brand Profile</h3>
                <p className="text-xs text-slate-400">Permanently removes brand and monitored assets.</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to permanently delete <strong className="text-white">{brand.name}</strong>?
              All associated official assets, threats, and alert logs will be removed.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsDeleteBrandOpen(false)}
                disabled={deleteBrandLoading}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteBrandConfirm}
                disabled={deleteBrandLoading}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition flex items-center gap-1.5"
              >
                {deleteBrandLoading ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EDIT OFFICIAL ASSET MODAL */}
      {editingAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0b101e] border border-slate-700/80 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Edit Official Asset</h3>
              <button onClick={() => setEditingAsset(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleEditAssetSubmit} className="space-y-3 text-xs">
              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Asset Name</label>
                <input
                  type="text"
                  required
                  value={editAssetForm.name}
                  onChange={(e) => setEditAssetForm({ ...editAssetForm, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Platform / Store</label>
                <input
                  type="text"
                  value={editAssetForm.platform}
                  onChange={(e) => setEditAssetForm({ ...editAssetForm, platform: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Asset URL *</label>
                <input
                  type="text"
                  required
                  value={editAssetForm.url}
                  onChange={(e) => setEditAssetForm({ ...editAssetForm, url: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Identifier / Developer Name</label>
                <input
                  type="text"
                  value={editAssetForm.identifier}
                  onChange={(e) => setEditAssetForm({ ...editAssetForm, identifier: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingAsset(null)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editAssetLoading}
                  className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold"
                >
                  {editAssetLoading ? 'Saving...' : 'Update Asset'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Asset Modal */}
      {isAddAssetOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="bg-[#0b101e] border border-slate-700/80 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white">Add Official Asset to Registry</h3>
            <form onSubmit={handleAddAssetSubmit} className="space-y-3 text-xs">
              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Asset Category</label>
                <select
                  value={assetType}
                  onChange={(e) => setAssetType(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                >
                  <option value="social">Social Media Account</option>
                  <option value="app">Mobile Application</option>
                  <option value="domain">Official Domain</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Platform / Store</label>
                <input
                  type="text"
                  value={assetPlatform}
                  onChange={(e) => setAssetPlatform(e.target.value)}
                  placeholder="Instagram, X, Google Play, Apple App Store..."
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Asset Name</label>
                <input
                  type="text"
                  value={assetName}
                  onChange={(e) => setAssetName(e.target.value)}
                  placeholder="e.g. ABC Bank Official Support"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Asset URL *</label>
                <input
                  type="text"
                  required
                  value={assetUrl}
                  onChange={(e) => setAssetUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                  Identifier / Handle / Developer Name
                </label>
                <input
                  type="text"
                  value={assetIdentifier}
                  onChange={(e) => setAssetIdentifier(e.target.value)}
                  placeholder="@abcbank or ABC Technologies Ltd"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsAddAssetOpen(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold"
                >
                  Add to Registry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
