import React, { useState, useEffect } from 'react';
import {
  X,
  Building,
  Upload,
  Share2,
  Smartphone,
  Globe,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  Plus,
  Trash2,
  AlertTriangle,
  ExternalLink,
  Edit2,
  Check,
  RefreshCw,
  Image as ImageIcon
} from 'lucide-react';
import { getBrand, getOfficialAssets, syncBrandWizard, uploadBrandLogo } from '../services/api';

const STEPS = [
  { id: 1, title: 'Brand Info', icon: Building },
  { id: 2, title: 'Logo', icon: Upload },
  { id: 3, title: 'Official Social', icon: Share2 },
  { id: 4, title: 'Official Apps', icon: Smartphone },
  { id: 5, title: 'Domains', icon: Globe },
  { id: 6, title: 'Review', icon: CheckCircle },
];

const SOCIAL_PLATFORMS = [
  'Instagram',
  'Facebook',
  'X',
  'LinkedIn',
  'YouTube',
  'TikTok',
  'Telegram',
  'Discord',
  'Other'
];

const INDUSTRIES = [
  'Other',
  'Banking & Financial Services',
  'Fintech & Payments',
  'E-Commerce & Retail',
  'Sportswear & Apparel',
  'Telecommunications',
  'Healthcare & Pharma',
  'Technology & SaaS'
];

export default function EditBrandWizardModal({ isOpen, onClose, brandId, onBrandUpdated }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [deleteConfirmItem, setDeleteConfirmItem] = useState(null);

  // Step 1: Brand Info
  const [name, setName] = useState('');
  const [website, setWebsite] = useState('');
  const [industry, setIndustry] = useState('Other');
  const [description, setDescription] = useState('');
  const [keywords, setKeywords] = useState('');
  const [aliases, setAliases] = useState('');

  // Step 2: Logo
  const [logoUrl, setLogoUrl] = useState('');

  // Step 3: Official Social Accounts
  const [socialAccounts, setSocialAccounts] = useState([]);

  // Step 4: Official Mobile Apps
  const [mobileApps, setMobileApps] = useState([]);

  // Step 5: Official Domains
  const [domains, setDomains] = useState([]);

  // Load existing brand and official assets when opened
  useEffect(() => {
    if (!isOpen || !brandId) return;

    const loadData = async () => {
      setFetching(true);
      setError('');
      setStep(1);
      try {
        const [bRes, aRes] = await Promise.all([
          getBrand(brandId),
          getOfficialAssets(brandId)
        ]);

        const b = bRes.data;
        const assets = aRes.data || [];

        setName(b.name || '');
        setWebsite(b.website || '');
        setIndustry(b.industry || 'Other');
        setDescription(b.description || '');
        setKeywords(Array.isArray(b.brand_keywords) ? b.brand_keywords.join(', ') : '');
        setAliases(Array.isArray(b.brand_aliases) ? b.brand_aliases.join(', ') : '');
        setLogoUrl(b.logo_url || '');

        // Map official assets into their respective categories
        const socials = assets
          .filter(a => a.asset_type === 'social')
          .map(a => ({
            id: a.id,
            platform: a.platform || 'Instagram',
            identifier: a.identifier || '',
            url: a.url || '',
            name: a.name || `${b.name} ${a.platform}`,
            verification_status: a.verification_status || 'VERIFIED'
          }));

        const apps = assets
          .filter(a => a.asset_type === 'app')
          .map(a => ({
            id: a.id,
            platform: a.platform || 'Google Play',
            name: a.name || `${b.name} App`,
            developer_name: a.developer_name || b.name,
            package_id: a.package_id || '',
            url: a.url || '',
            verification_status: a.verification_status || 'VERIFIED'
          }));

        const doms = assets
          .filter(a => a.asset_type === 'domain')
          .map(a => ({
            id: a.id,
            name: a.name || 'Official Domain',
            url: a.url || '',
            is_active: a.is_active !== false,
            verification_status: a.verification_status || 'VERIFIED'
          }));

        setSocialAccounts(socials);
        setMobileApps(apps);
        setDomains(doms);
      } catch (err) {
        console.error("Failed to load brand details for editing", err);
        setError("Could not load brand profile. Please try again.");
      } finally {
        setFetching(false);
      }
    };

    loadData();
  }, [isOpen, brandId]);

  if (!isOpen) return null;

  // Validation before advancing or saving
  const validateStep = (currentStep) => {
    setError('');
    if (currentStep === 1) {
      if (!name.trim()) {
        setError('Brand name is required.');
        return false;
      }
      if (website.trim() && !/^https?:\/\//i.test(website.trim()) && !/^[\w-]+(\.[\w-]+)+/i.test(website.trim())) {
        setError('Official website must be a valid domain or URL (e.g., https://example.com).');
        return false;
      }
    }

    if (currentStep === 3) {
      // Check for duplicate URLs or handles in social
      const urls = socialAccounts.map(s => s.url.trim().toLowerCase()).filter(Boolean);
      const uniqueUrls = new Set(urls);
      if (urls.length !== uniqueUrls.size) {
        setError('Duplicate social URLs detected. Each official social asset must have a unique URL.');
        return false;
      }
    }

    if (currentStep === 4) {
      // Check for duplicate app packages or URLs
      const pkgs = mobileApps.map(a => (a.package_id || '').trim().toLowerCase()).filter(Boolean);
      const uniquePkgs = new Set(pkgs);
      if (pkgs.length !== uniquePkgs.size) {
        setError('Duplicate application package IDs detected. Each mobile app must have a unique package ID.');
        return false;
      }
    }

    if (currentStep === 5) {
      // Check for duplicate domains
      const domUrls = domains.map(d => d.url.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/$/, '')).filter(Boolean);
      const uniqueDoms = new Set(domUrls);
      if (domUrls.length !== uniqueDoms.size) {
        setError('Duplicate domains detected. Each whitelisted domain must be unique.');
        return false;
      }
    }

    return true;
  };

  const handleNext = () => {
    if (validateStep(step)) {
      if (step < 6) setStep(step + 1);
    }
  };

  const handleBack = () => {
    setError('');
    if (step > 1) setStep(step - 1);
  };

  const handleStepClick = (targetStep) => {
    if (validateStep(step)) {
      setStep(targetStep);
    }
  };

  // Logo upload handler
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setError('Selected image exceeds the 5MB size limit.');
      return;
    }

    setUploadingLogo(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await uploadBrandLogo(formData);
      setLogoUrl(res.data.logo_url);
    } catch (err) {
      console.error("Logo upload failed", err);
      setError(err.response?.data?.detail || 'Failed to upload logo image.');
    } finally {
      setUploadingLogo(false);
      // Reset input value so same file can be re-uploaded if desired
      e.target.value = '';
    }
  };

  // Step 3 Social handlers
  const handleAddSocial = () => {
    setSocialAccounts([
      ...socialAccounts,
      { platform: 'Instagram', identifier: '', url: '', name: '', verification_status: 'VERIFIED' }
    ]);
  };

  const handleRemoveSocial = (index) => {
    setSocialAccounts(socialAccounts.filter((_, i) => i !== index));
    setDeleteConfirmItem(null);
  };

  // Step 4 App handlers
  const handleAddApp = () => {
    setMobileApps([
      ...mobileApps,
      { platform: 'Google Play', name: '', developer_name: name || '', package_id: '', url: '', verification_status: 'VERIFIED' }
    ]);
  };

  const handleRemoveApp = (index) => {
    setMobileApps(mobileApps.filter((_, i) => i !== index));
    setDeleteConfirmItem(null);
  };

  // Step 5 Domain handlers
  const handleAddDomain = () => {
    setDomains([
      ...domains,
      { name: 'Secondary Web Portal', url: '', is_active: true, verification_status: 'VERIFIED' }
    ]);
  };

  const handleRemoveDomain = (index) => {
    setDomains(domains.filter((_, i) => i !== index));
    setDeleteConfirmItem(null);
  };

  // Final Save Changes
  const handleSaveChanges = async () => {
    if (!validateStep(1)) {
      setStep(1);
      return;
    }
    if (!validateStep(3)) {
      setStep(3);
      return;
    }
    if (!validateStep(4)) {
      setStep(4);
      return;
    }
    if (!validateStep(5)) {
      setStep(5);
      return;
    }

    setLoading(true);
    setError('');
    try {
      const kwList = keywords.split(',').map((k) => k.trim()).filter(Boolean);
      const aliasList = aliases.split(',').map((a) => a.trim()).filter(Boolean);

      // Clean website
      let cleanWebsite = website.trim();
      if (cleanWebsite && !/^https?:\/\//i.test(cleanWebsite)) {
        cleanWebsite = `https://${cleanWebsite}`;
      }

      // Filter valid social accounts
      const validSocials = socialAccounts
        .filter(s => s.url && s.url.trim())
        .map(s => ({
          id: s.id || null,
          platform: s.platform,
          name: s.name?.trim() || `${name.trim()} ${s.platform}`,
          identifier: s.identifier?.trim() || s.url.trim(),
          url: s.url.trim(),
          verification_status: 'VERIFIED'
        }));

      // Filter valid mobile apps
      const validApps = mobileApps
        .filter(a => a.url && a.url.trim())
        .map(a => ({
          id: a.id || null,
          platform: a.platform,
          name: a.name?.trim() || `${name.trim()} App`,
          developer_name: a.developer_name?.trim() || name.trim(),
          package_id: a.package_id?.trim() || null,
          url: a.url.trim(),
          verification_status: 'VERIFIED'
        }));

      // Filter valid domains
      const validDomains = domains
        .filter(d => d.url && d.url.trim())
        .map(d => ({
          id: d.id || null,
          platform: 'Domain',
          name: d.name?.trim() || 'Official Domain',
          url: d.url.trim(),
          is_active: d.is_active !== false,
          verification_status: 'VERIFIED'
        }));

      const syncPayload = {
        name: name.trim(),
        website: cleanWebsite || null,
        industry,
        description: description.trim() || null,
        logo_url: logoUrl.trim() || null,
        brand_keywords: kwList,
        brand_aliases: aliasList,
        social_accounts: validSocials,
        mobile_apps: validApps,
        domains: validDomains
      };

      const res = await syncBrandWizard(brandId, syncPayload);
      if (onBrandUpdated) {
        onBrandUpdated(res.data.brand);
      }
      onClose();
    } catch (err) {
      console.error("Failed to save brand wizard updates", err);
      setError(err.response?.data?.detail || 'Failed to save changes. Please verify required fields.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0b101e] border border-slate-700/80 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-4 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shadow-sm">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white">Edit Brand Profile & Official Registry</h3>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  Step {step} of 6
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Updating verified identity & exclusion whitelist for <strong className="text-slate-200">{name || 'Brand'}</strong>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Cancel and Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stepper Progress Bar (Clickable steps) */}
        <div className="px-6 py-2.5 bg-slate-950 border-b border-slate-800/80 overflow-x-auto">
          <div className="flex items-center justify-between min-w-[500px]">
            {STEPS.map((s) => {
              const isPast = step > s.id;
              const isCurrent = step === s.id;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => handleStepClick(s.id)}
                  className="flex items-center gap-1.5 text-xs group cursor-pointer focus:outline-none"
                >
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                      isCurrent
                        ? 'bg-cyan-500 text-slate-950 font-black shadow-md shadow-cyan-500/40 ring-2 ring-cyan-400/30'
                        : isPast
                        ? 'bg-emerald-500 text-white'
                        : 'bg-slate-800 text-slate-400 group-hover:bg-slate-700 group-hover:text-slate-200'
                    }`}
                  >
                    {isPast ? <Check className="w-3.5 h-3.5" /> : s.id}
                  </div>
                  <span
                    className={`font-medium text-[11px] whitespace-nowrap transition-colors ${
                      isCurrent
                        ? 'text-cyan-300 font-bold'
                        : isPast
                        ? 'text-slate-300'
                        : 'text-slate-500 group-hover:text-slate-300'
                    }`}
                  >
                    {s.title}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Modal Body / Step Content */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {fetching ? (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              <p className="text-xs text-slate-400">Loading brand profile & official assets...</p>
            </div>
          ) : (
            <>
              {error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2 animate-fadeIn">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-400" />
                  <span>{error}</span>
                </div>
              )}

              {/* STEP 1: Brand Info */}
              {step === 1 && (
                <div className="space-y-4 animate-fadeIn">
                  <div>
                    <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 1: General Brand Information</h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">Primary ground-truth identity used across all risk detection algorithms.</p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">Company / Brand Name *</label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="e.g. Blackberrys"
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">Industry / Category</label>
                      <select
                        value={industry}
                        onChange={(e) => setIndustry(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                      >
                        {INDUSTRIES.map((ind) => (
                          <option key={ind} value={ind}>{ind}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold text-slate-300 block mb-1">Official Canonical Website</label>
                    <input
                      type="text"
                      value={website}
                      onChange={(e) => setWebsite(e.target.value)}
                      placeholder="https://www.blackberrys.com"
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-semibold text-slate-300 block mb-1">Description</label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      rows={3}
                      placeholder="Describe the company's verified business operations and core trademarked products..."
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">Brand Keywords (comma separated)</label>
                      <input
                        type="text"
                        value={keywords}
                        onChange={(e) => setKeywords(e.target.value)}
                        placeholder="menswear, suits, clothing, formal"
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                      />
                      <span className="text-[10px] text-slate-500 mt-1 block">Used by keyword detection engine to flag fraud intent.</span>
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300 block mb-1">Brand Aliases (comma separated)</label>
                      <input
                        type="text"
                        value={aliases}
                        onChange={(e) => setAliases(e.target.value)}
                        placeholder="Blackberrys Menswear, Blackberrys India"
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                      />
                      <span className="text-[10px] text-slate-500 mt-1 block">Alternative trade names and acronyms.</span>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 2: Logo */}
              {step === 2 && (
                <div className="space-y-4 animate-fadeIn">
                  <div>
                    <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 2: Brand Logo & Visual Trademark</h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      BrandShield AI computes a 64-bit perceptual hash (dHash) to detect logo theft, copied graphics, and look-alike brand avatars.
                    </p>
                  </div>

                  {/* Dual Input: URL or File Upload */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                      <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                        <Upload className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Upload Logo File (Persistent)</span>
                      </label>
                      <p className="text-[10px] text-slate-400 leading-relaxed">
                        Upload a PNG, JPG, WEBP, or SVG file (up to 5MB). The file is saved persistently on the server.
                      </p>
                      <label className="relative inline-flex items-center justify-center px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-cyan-300 cursor-pointer transition w-full">
                        {uploadingLogo ? (
                          <span className="flex items-center gap-2">
                            <span className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></span>
                            <span>Uploading logo...</span>
                          </span>
                        ) : (
                          <span className="flex items-center gap-2">
                            <Upload className="w-4 h-4" />
                            <span>Choose Image File</span>
                          </span>
                        )}
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/webp,image/svg+xml"
                          onChange={handleFileUpload}
                          disabled={uploadingLogo}
                          className="sr-only"
                        />
                      </label>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                      <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                        <Globe className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Or Provide Logo Image URL</span>
                      </label>
                      <p className="text-[10px] text-slate-400 leading-relaxed">
                        Enter a direct HTTPS link to the official trademark image.
                      </p>
                      <input
                        type="text"
                        value={logoUrl}
                        onChange={(e) => setLogoUrl(e.target.value)}
                        placeholder="https://example.com/logo.png"
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                      />
                    </div>
                  </div>

                  {/* Logo Preview Card */}
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-xl overflow-hidden bg-slate-950 flex items-center justify-center border border-slate-700 flex-shrink-0">
                        {logoUrl ? (
                          <img
                            src={logoUrl}
                            alt="Logo Preview"
                            onError={(e) => {
                              e.target.onerror = null;
                              e.target.src = 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100';
                            }}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <ImageIcon className="w-7 h-7 text-slate-600" />
                        )}
                      </div>
                      <div>
                        <h5 className="text-xs font-bold text-white">Active Trademark Logo</h5>
                        <p className="text-[11px] text-slate-400 truncate max-w-sm font-mono mt-0.5">
                          {logoUrl || 'No logo assigned yet'}
                        </p>
                        <span className="inline-block mt-1 text-[10px] text-cyan-400 font-medium">
                          {logoUrl ? '✓ Ready for perceptual hashing' : 'A logo is recommended for visual trademark defense'}
                        </span>
                      </div>
                    </div>

                    {logoUrl && (
                      <button
                        type="button"
                        onClick={() => setLogoUrl('')}
                        className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/20 text-xs font-medium transition"
                      >
                        Remove Logo
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* STEP 3: Official Social */}
              {step === 3 && (
                <div className="space-y-4 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 3: Official Social Media Accounts</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        These accounts are automatically whitelisted with <strong>0 Risk</strong>. Replaced or removed accounts will lose exclusion privileges immediately.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleAddSocial}
                      className="px-3 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-xs font-semibold flex items-center gap-1.5 border border-cyan-500/30 transition shadow-sm"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Social</span>
                    </button>
                  </div>

                  {socialAccounts.length === 0 ? (
                    <div className="p-8 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/40 space-y-2">
                      <Share2 className="w-8 h-8 text-slate-600 mx-auto" />
                      <p className="text-xs text-slate-400">No official social accounts registered yet.</p>
                      <button
                        type="button"
                        onClick={handleAddSocial}
                        className="text-xs text-cyan-400 hover:text-cyan-300 underline font-medium"
                      >
                        Add your first official social account
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      {socialAccounts.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center bg-slate-900/70 p-3 rounded-xl border border-slate-800 hover:border-slate-700 transition"
                        >
                          <select
                            value={item.platform}
                            onChange={(e) => {
                              const updated = [...socialAccounts];
                              updated[idx].platform = e.target.value;
                              setSocialAccounts(updated);
                            }}
                            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white sm:w-32 focus:outline-none focus:border-cyan-500"
                          >
                            {SOCIAL_PLATFORMS.map((p) => (
                              <option key={p} value={p}>{p}</option>
                            ))}
                          </select>

                          <input
                            type="text"
                            placeholder="Handle (@name)"
                            value={item.identifier}
                            onChange={(e) => {
                              const updated = [...socialAccounts];
                              updated[idx].identifier = e.target.value;
                              setSocialAccounts(updated);
                            }}
                            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white sm:w-36 focus:outline-none focus:border-cyan-500 font-mono"
                          />

                          <input
                            type="text"
                            placeholder="Official URL (https://...)"
                            value={item.url}
                            onChange={(e) => {
                              const updated = [...socialAccounts];
                              updated[idx].url = e.target.value;
                              setSocialAccounts(updated);
                            }}
                            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white flex-1 focus:outline-none focus:border-cyan-500 font-mono"
                          />

                          <div className="flex items-center justify-between sm:justify-end gap-2 flex-shrink-0">
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              VERIFIED
                            </span>
                            <button
                              type="button"
                              onClick={() => setDeleteConfirmItem({ type: 'social', index: idx, name: item.identifier || item.url || 'this account' })}
                              className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
                              title="Delete Social Asset"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* STEP 4: Official Apps */}
              {step === 4 && (
                <div className="space-y-4 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 4: Official Mobile Applications</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        BrandShield AI verifies authorized store packages and developer signatures against these ground-truth listings.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleAddApp}
                      className="px-3 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-xs font-semibold flex items-center gap-1.5 border border-cyan-500/30 transition shadow-sm"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add App</span>
                    </button>
                  </div>

                  {mobileApps.length === 0 ? (
                    <div className="p-8 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/40 space-y-2">
                      <Smartphone className="w-8 h-8 text-slate-600 mx-auto" />
                      <p className="text-xs text-slate-400">No official mobile apps registered yet.</p>
                      <button
                        type="button"
                        onClick={handleAddApp}
                        className="text-xs text-cyan-400 hover:text-cyan-300 underline font-medium"
                      >
                        Register an official Google Play or Apple App Store listing
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {mobileApps.map((item, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-900/70 p-3.5 rounded-xl border border-slate-800 hover:border-slate-700 transition space-y-2.5"
                        >
                          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                            <select
                              value={item.platform}
                              onChange={(e) => {
                                const updated = [...mobileApps];
                                updated[idx].platform = e.target.value;
                                setMobileApps(updated);
                              }}
                              className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white sm:w-40 focus:outline-none focus:border-cyan-500"
                            >
                              <option>Google Play</option>
                              <option>Apple App Store</option>
                            </select>
                            <input
                              type="text"
                              placeholder="App Title (e.g. Blackberrys Official Store)"
                              value={item.name}
                              onChange={(e) => {
                                const updated = [...mobileApps];
                                updated[idx].name = e.target.value;
                                setMobileApps(updated);
                              }}
                              className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white flex-1 focus:outline-none focus:border-cyan-500"
                            />
                            <div className="flex items-center justify-between sm:justify-end gap-2 flex-shrink-0">
                              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                VERIFIED
                              </span>
                              <button
                                type="button"
                                onClick={() => setDeleteConfirmItem({ type: 'app', index: idx, name: item.name || 'this app' })}
                                className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
                                title="Delete App Asset"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                            <input
                              type="text"
                              placeholder="Package ID (com.example.app)"
                              value={item.package_id}
                              onChange={(e) => {
                                const updated = [...mobileApps];
                                updated[idx].package_id = e.target.value;
                                setMobileApps(updated);
                              }}
                              className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                            />
                            <input
                              type="text"
                              placeholder="Authorized Developer Name"
                              value={item.developer_name}
                              onChange={(e) => {
                                const updated = [...mobileApps];
                                updated[idx].developer_name = e.target.value;
                                setMobileApps(updated);
                              }}
                              className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                            />
                            <input
                              type="text"
                              placeholder="Store URL (https://...)"
                              value={item.url}
                              onChange={(e) => {
                                const updated = [...mobileApps];
                                updated[idx].url = e.target.value;
                                setMobileApps(updated);
                              }}
                              className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* STEP 5: Domains */}
              {step === 5 && (
                <div className="space-y-4 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 5: Trusted Official Domains</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Whitelisted digital web portals, payment checkouts, and customer service domains.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleAddDomain}
                      className="px-3 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-xs font-semibold flex items-center gap-1.5 border border-cyan-500/30 transition shadow-sm"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add Domain</span>
                    </button>
                  </div>

                  {domains.length === 0 ? (
                    <div className="p-8 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/40 space-y-2">
                      <Globe className="w-8 h-8 text-slate-600 mx-auto" />
                      <p className="text-xs text-slate-400">No additional official domains configured.</p>
                      <button
                        type="button"
                        onClick={handleAddDomain}
                        className="text-xs text-cyan-400 hover:text-cyan-300 underline font-medium"
                      >
                        Add secondary domain or customer portal
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      {domains.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center bg-slate-900/70 p-3 rounded-xl border border-slate-800 hover:border-slate-700 transition"
                        >
                          <input
                            type="text"
                            placeholder="Portal Name (e.g. Helpdesk)"
                            value={item.name}
                            onChange={(e) => {
                              const updated = [...domains];
                              updated[idx].name = e.target.value;
                              setDomains(updated);
                            }}
                            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white sm:w-48 focus:outline-none focus:border-cyan-500"
                          />

                          <input
                            type="text"
                            placeholder="Domain / URL (e.g. https://support.brand.com)"
                            value={item.url}
                            onChange={(e) => {
                              const updated = [...domains];
                              updated[idx].url = e.target.value;
                              setDomains(updated);
                            }}
                            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white flex-1 focus:outline-none focus:border-cyan-500 font-mono"
                          />

                          <div className="flex items-center justify-between sm:justify-end gap-2 flex-shrink-0">
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              WHITELISTED
                            </span>
                            <button
                              type="button"
                              onClick={() => setDeleteConfirmItem({ type: 'domain', index: idx, name: item.name || item.url || 'this domain' })}
                              className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition"
                              title="Delete Domain Asset"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* STEP 6: Review & Finalize */}
              {step === 6 && (
                <div className="space-y-4 animate-fadeIn text-xs">
                  <div>
                    <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 6: Review & Finalize Updates</h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Confirm all pending changes before saving to the central BrandShield AI risk engine and MongoDB database.
                    </p>
                  </div>

                  {/* Brand Overview Card */}
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl overflow-hidden bg-slate-950 border border-slate-700 flex items-center justify-center flex-shrink-0">
                          {logoUrl ? (
                            <img src={logoUrl} alt="Logo" className="w-full h-full object-cover" />
                          ) : (
                            <Building className="w-6 h-6 text-slate-500" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h5 className="text-sm font-bold text-white">{name}</h5>
                            <span className="px-2 py-0.2 rounded text-[10px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                              {industry}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 font-mono mt-0.5">{website || 'No website set'}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setStep(1)}
                        className="text-[11px] text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
                      >
                        <Edit2 className="w-3 h-3" />
                        <span>Edit Info</span>
                      </button>
                    </div>

                    {description && (
                      <p className="text-[11px] text-slate-400 line-clamp-2 border-t border-slate-800 pt-2">
                        {description}
                      </p>
                    )}

                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-[11px]">
                      <div>
                        <span className="text-slate-500 block text-[10px]">Social Accounts</span>
                        <strong className="text-white">{socialAccounts.length} Verified</strong>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Mobile Apps</span>
                        <strong className="text-white">{mobileApps.length} Verified</strong>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Domains</span>
                        <strong className="text-white">{domains.length} Whitelisted</strong>
                      </div>
                    </div>
                  </div>

                  {/* Detailed Asset Breakdown */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {/* Social List */}
                    <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-slate-300 flex items-center gap-1.5">
                          <Share2 className="w-3.5 h-3.5 text-cyan-400" />
                          <span>Social Assets ({socialAccounts.length})</span>
                        </span>
                        <button onClick={() => setStep(3)} className="text-[10px] text-cyan-400 hover:underline">Edit</button>
                      </div>
                      <div className="space-y-1.5 max-h-32 overflow-y-auto">
                        {socialAccounts.length > 0 ? (
                          socialAccounts.map((s, i) => (
                            <div key={i} className="text-[10px] bg-slate-950/60 p-1.5 rounded border border-slate-800/80 truncate">
                              <span className="font-semibold text-cyan-300">{s.platform}:</span>{' '}
                              <span className="text-slate-300 font-mono">{s.identifier || s.url}</span>
                            </div>
                          ))
                        ) : (
                          <p className="text-[10px] text-slate-500 italic">None registered</p>
                        )}
                      </div>
                    </div>

                    {/* Apps List */}
                    <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-slate-300 flex items-center gap-1.5">
                          <Smartphone className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Mobile Apps ({mobileApps.length})</span>
                        </span>
                        <button onClick={() => setStep(4)} className="text-[10px] text-cyan-400 hover:underline">Edit</button>
                      </div>
                      <div className="space-y-1.5 max-h-32 overflow-y-auto">
                        {mobileApps.length > 0 ? (
                          mobileApps.map((a, i) => (
                            <div key={i} className="text-[10px] bg-slate-950/60 p-1.5 rounded border border-slate-800/80 truncate">
                              <span className="font-semibold text-emerald-300">{a.platform}:</span>{' '}
                              <span className="text-slate-300 font-mono">{a.name}</span>
                            </div>
                          ))
                        ) : (
                          <p className="text-[10px] text-slate-500 italic">None registered</p>
                        )}
                      </div>
                    </div>

                    {/* Domains List */}
                    <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-slate-300 flex items-center gap-1.5">
                          <Globe className="w-3.5 h-3.5 text-purple-400" />
                          <span>Domains ({domains.length})</span>
                        </span>
                        <button onClick={() => setStep(5)} className="text-[10px] text-cyan-400 hover:underline">Edit</button>
                      </div>
                      <div className="space-y-1.5 max-h-32 overflow-y-auto">
                        {domains.length > 0 ? (
                          domains.map((d, i) => (
                            <div key={i} className="text-[10px] bg-slate-950/60 p-1.5 rounded border border-slate-800/80 truncate">
                              <span className="text-slate-300 font-mono">{d.url}</span>
                            </div>
                          ))
                        ) : (
                          <p className="text-[10px] text-slate-500 italic">None registered</p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-[11px] flex items-center gap-2.5">
                    <ShieldCheck className="w-5 h-5 flex-shrink-0 text-cyan-400" />
                    <span>
                      Dynamic Registry Guarantee: Replaced, edited, or deleted assets will automatically update the exclusion rule engine. Subsequent scans and threat detections will use these latest saved values.
                    </span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="p-4 px-6 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleBack}
              disabled={step === 1 || fetching || loading}
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-30 border border-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            {step < 6 ? (
              <button
                type="button"
                onClick={handleNext}
                disabled={fetching || loading}
                className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition"
              >
                <span>Next: {STEPS[step]?.title || 'Step'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSaveChanges}
                disabled={loading || fetching}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 text-xs font-black flex items-center gap-1.5 shadow-lg shadow-cyan-500/30 transition disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                    <span>Saving Changes...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Save Changes</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal for Assets */}
      {deleteConfirmItem && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-sm bg-slate-900 border border-rose-500/40 rounded-2xl p-5 shadow-2xl space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-400">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Remove Official Asset?</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Are you sure you want to remove <strong className="text-rose-300">{deleteConfirmItem.name}</strong> from the official asset registry?
                </p>
              </div>
            </div>
            <div className="p-2.5 rounded-lg bg-rose-950/30 border border-rose-900/50 text-[10px] text-rose-300">
              Notice: Once saved, this asset will no longer receive exclusion protection and will be treated as an unverified entity in future monitoring scans.
            </div>
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setDeleteConfirmItem(null)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  if (deleteConfirmItem.type === 'social') handleRemoveSocial(deleteConfirmItem.index);
                  else if (deleteConfirmItem.type === 'app') handleRemoveApp(deleteConfirmItem.index);
                  else if (deleteConfirmItem.type === 'domain') handleRemoveDomain(deleteConfirmItem.index);
                }}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 shadow-md shadow-rose-950/40"
              >
                Remove Asset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
