import React, { useState } from 'react';
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
  Sparkles
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { createBrand, addOfficialAsset } from '../services/api';

const STEPS = [
  { id: 1, title: 'Brand Info', icon: Building },
  { id: 2, title: 'Logo', icon: Upload },
  { id: 3, title: 'Official Social', icon: Share2 },
  { id: 4, title: 'Official Apps', icon: Smartphone },
  { id: 5, title: 'Domains', icon: Globe },
  { id: 6, title: 'Review', icon: CheckCircle },
];

export default function AddBrandWizardModal() {
  const { isAddBrandOpen, setIsAddBrandOpen, refreshBrands, setSelectedBrand } = useBrand();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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

  if (!isAddBrandOpen) return null;

  const handleNext = () => {
    setError('');
    if (step === 1 && !name.trim()) {
      setError('Company/Brand name is required.');
      return;
    }
    if (step < 6) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    setError('');
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleAddSocial = () => {
    setSocialAccounts([...socialAccounts, { platform: 'X', identifier: '', url: '' }]);
  };

  const handleRemoveSocial = (index) => {
    setSocialAccounts(socialAccounts.filter((_, i) => i !== index));
  };

  const handleAddApp = () => {
    setMobileApps([...mobileApps, { platform: 'Apple App Store', name: '', developer_name: '', url: '' }]);
  };

  const handleRemoveApp = (index) => {
    setMobileApps(mobileApps.filter((_, i) => i !== index));
  };

  const handleAddDomain = () => {
    setDomains([...domains, { url: '', name: 'Secondary Domain' }]);
  };

  const handleRemoveDomain = (index) => {
    setDomains(domains.filter((_, i) => i !== index));
  };

  const resetForm = () => {
    setStep(1);
    setError('');
    setName('');
    setWebsite('');
    setIndustry('Other');
    setDescription('');
    setKeywords('');
    setAliases('');
    setLogoUrl('');
    setSocialAccounts([]);
    setMobileApps([]);
    setDomains([]);
  };

  const handleClose = () => {
    resetForm();
    setIsAddBrandOpen(false);
  };

  const handleFinish = async () => {
    setLoading(true);
    setError('');
    try {
      const kwList = keywords.split(',').map((k) => k.trim()).filter(Boolean);
      const aliasList = aliases.split(',').map((a) => a.trim()).filter(Boolean);

      // Extract Instagram account if present
      const igAccount = socialAccounts.find(s => (s.platform || '').toLowerCase().includes('instagram'));
      let igUser = '';
      let igUrl = '';
      if (igAccount) {
        igUrl = igAccount.url || '';
        igUser = (igAccount.identifier || '').replace(/^@/, '');
        if (!igUser && igUrl) {
          igUser = igUrl.replace(/^https?:\/\/(www\.)?instagram\.com\//, '').split('/')[0].split('?')[0];
        }
      }

      // 1. Create Brand in MongoDB with official ground truth fields
      const brandRes = await createBrand({
        name: name.trim(),
        website: website.trim(),
        industry,
        description: description.trim(),
        logo_url: logoUrl.trim(),
        brand_keywords: kwList,
        brand_aliases: aliasList,
        official_instagram_username: igUser || undefined,
        official_instagram_url: igUrl || (igUser ? `https://instagram.com/${igUser}` : undefined),
        official_bio: description.trim() || undefined,
        official_instagram_logo: logoUrl.trim() || undefined,
        official_social_links: socialAccounts.map(s => s.url).filter(Boolean),
        official_app_links: mobileApps.map(a => a.url).filter(Boolean)
      });

      const newBrand = brandRes.data;

      // 2. Add Official Social Accounts
      for (const soc of socialAccounts) {
        if (soc.url) {
          await addOfficialAsset(newBrand.id, {
            brand_id: newBrand.id,
            name: `${newBrand.name} ${soc.platform}`,
            asset_type: 'social',
            platform: soc.platform,
            url: soc.url,
            identifier: soc.identifier || soc.url,
            verification_status: 'VERIFIED'
          });
        }
      }

      // 3. Add Official Apps
      for (const app of mobileApps) {
        if (app.url) {
          await addOfficialAsset(newBrand.id, {
            brand_id: newBrand.id,
            name: app.name || `${newBrand.name} App`,
            asset_type: 'app',
            platform: app.platform,
            url: app.url,
            developer_name: app.developer_name || newBrand.name,
            verification_status: 'VERIFIED'
          });
        }
      }

      // 4. Add Official Domains
      for (const dom of domains) {
        if (dom.url) {
          await addOfficialAsset(newBrand.id, {
            brand_id: newBrand.id,
            name: dom.name || 'Official Domain',
            asset_type: 'domain',
            platform: 'Domain',
            url: dom.url,
            verification_status: 'VERIFIED'
          });
        }
      }

      await refreshBrands();
      setSelectedBrand(newBrand);
      resetForm();
      setIsAddBrandOpen(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create brand. Please check fields.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0b101e] border border-slate-700/80 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-4 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Add Brand Onboarding Wizard</h3>
              <p className="text-[11px] text-slate-400">Configure legitimate brand profile & official asset registry</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stepper Progress Bar */}
        <div className="px-6 py-3 bg-slate-950 border-b border-slate-800/80">
          <div className="flex items-center justify-between">
            {STEPS.map((s, idx) => {
              const Icon = s.icon;
              const isPast = step > s.id;
              const isCurrent = step === s.id;
              return (
                <div key={s.id} className="flex items-center gap-1.5 text-xs">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                      isPast
                        ? 'bg-emerald-500 text-white'
                        : isCurrent
                        ? 'bg-cyan-500 text-slate-950 font-black shadow-md shadow-cyan-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {isPast ? <CheckCircle className="w-3.5 h-3.5" /> : s.id}
                  </div>
                  <span
                    className={`hidden sm:inline font-medium text-[11px] ${
                      isCurrent ? 'text-cyan-300 font-semibold' : isPast ? 'text-slate-300' : 'text-slate-500'
                    }`}
                  >
                    {s.title}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          )}

          {/* STEP 1: Brand Info */}
          {step === 1 && (
            <div className="space-y-3 animate-fade-in">
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 1: General Brand Information</h4>
              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Company / Brand Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Apex Global Bank"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">Official Website</label>
                  <input
                    type="text"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://apexbank.example"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">Industry</label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option>Other</option>
                    <option>Banking & Financial Services</option>
                    <option>Fintech & Payments</option>
                    <option>E-Commerce & Retail</option>
                    <option>Sportswear & Apparel</option>
                    <option>Telecommunications</option>
                    <option>Healthcare & Pharma</option>
                    <option>Technology & SaaS</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="Brief description of the brand identity and verified business operations..."
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">Brand Keywords (comma separated)</label>
                  <input
                    type="text"
                    value={keywords}
                    onChange={(e) => setKeywords(e.target.value)}
                    placeholder="bank, loans, wealth, support"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">Brand Aliases / Alternate Names</label>
                  <input
                    type="text"
                    value={aliases}
                    onChange={(e) => setAliases(e.target.value)}
                    placeholder="ApexBank, Apex Financial"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Logo */}
          {step === 2 && (
            <div className="space-y-4 animate-fade-in">
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 2: Brand Logo & Visual Trademark</h4>
              <p className="text-[11px] text-slate-400">
                BrandShield AI uses this logo for perceptual image hashing (dHash) to detect logo theft and look-alike brand graphics.
              </p>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Official Logo Image URL</label>
                <input
                  type="text"
                  value={logoUrl}
                  onChange={(e) => setLogoUrl(e.target.value)}
                  placeholder="https://example.com/logo.png"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <div className="w-16 h-16 rounded-xl overflow-hidden bg-slate-800 flex items-center justify-center border border-slate-700">
                  {logoUrl ? (
                    <img src={logoUrl} alt="Preview" className="w-full h-full object-cover" />
                  ) : (
                    <Upload className="w-6 h-6 text-slate-500" />
                  )}
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-200">Active Logo Preview</p>
                  <p className="text-[11px] text-slate-400">Dimensions: Standardized to 64-bit perceptual hash on ingestion.</p>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Official Social Accounts */}
          {step === 3 && (
            <div className="space-y-3 animate-fade-in">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 3: Official Social Accounts</h4>
                  <p className="text-[11px] text-slate-400">These accounts are whitelisted and excluded from threat detection.</p>
                </div>
                <button
                  type="button"
                  onClick={handleAddSocial}
                  className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-semibold flex items-center gap-1 border border-slate-700"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Social</span>
                </button>
              </div>

              <div className="space-y-2">
                {socialAccounts.map((item, idx) => (
                  <div key={idx} className="flex gap-2 items-center bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                    <select
                      value={item.platform}
                      onChange={(e) => {
                        const updated = [...socialAccounts];
                        updated[idx].platform = e.target.value;
                        setSocialAccounts(updated);
                      }}
                      className="px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white w-32 focus:outline-none"
                    >
                      <option>Instagram</option>
                      <option>Facebook</option>
                      <option>X</option>
                      <option>LinkedIn</option>
                      <option>YouTube</option>
                      <option>TikTok</option>
                    </select>
                    <input
                      type="text"
                      placeholder="Handle (@handle)"
                      value={item.identifier}
                      onChange={(e) => {
                        const updated = [...socialAccounts];
                        updated[idx].identifier = e.target.value;
                        setSocialAccounts(updated);
                      }}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white w-36 focus:outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Official URL"
                      value={item.url}
                      onChange={(e) => {
                        const updated = [...socialAccounts];
                        updated[idx].url = e.target.value;
                        setSocialAccounts(updated);
                      }}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white flex-1 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveSocial(idx)}
                      className="p-1.5 text-slate-500 hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 4: Official Mobile Apps */}
          {step === 4 && (
            <div className="space-y-3 animate-fade-in">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 4: Official Mobile Applications</h4>
                  <p className="text-[11px] text-slate-400">Used by the engine to verify authorized developers and package IDs.</p>
                </div>
                <button
                  type="button"
                  onClick={handleAddApp}
                  className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-semibold flex items-center gap-1 border border-slate-700"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add App</span>
                </button>
              </div>

              <div className="space-y-2">
                {mobileApps.map((item, idx) => (
                  <div key={idx} className="space-y-2 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-2">
                      <select
                        value={item.platform}
                        onChange={(e) => {
                          const updated = [...mobileApps];
                          updated[idx].platform = e.target.value;
                          setMobileApps(updated);
                        }}
                        className="px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white w-40 focus:outline-none"
                      >
                        <option>Google Play</option>
                        <option>Apple App Store</option>
                      </select>
                      <input
                        type="text"
                        placeholder="App Name"
                        value={item.name}
                        onChange={(e) => {
                          const updated = [...mobileApps];
                          updated[idx].name = e.target.value;
                          setMobileApps(updated);
                        }}
                        className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white flex-1 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveApp(idx)}
                        className="p-1.5 text-slate-500 hover:text-rose-400 transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="Authorized Developer (e.g. ABC Technologies)"
                        value={item.developer_name}
                        onChange={(e) => {
                          const updated = [...mobileApps];
                          updated[idx].developer_name = e.target.value;
                          setMobileApps(updated);
                        }}
                        className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white focus:outline-none"
                      />
                      <input
                        type="text"
                        placeholder="Store URL"
                        value={item.url}
                        onChange={(e) => {
                          const updated = [...mobileApps];
                          updated[idx].url = e.target.value;
                          setMobileApps(updated);
                        }}
                        className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white focus:outline-none"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 5: Official Domains */}
          {step === 5 && (
            <div className="space-y-3 animate-fade-in">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 5: Trusted Official Domains</h4>
                  <p className="text-[11px] text-slate-400">Whitelisted web domains and portals.</p>
                </div>
                <button
                  type="button"
                  onClick={handleAddDomain}
                  className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-semibold flex items-center gap-1 border border-slate-700"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Domain</span>
                </button>
              </div>

              <div className="space-y-2">
                {domains.map((dom, idx) => (
                  <div key={idx} className="flex gap-2 items-center bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                    <input
                      type="text"
                      placeholder="Label (e.g. Primary Portal)"
                      value={dom.name}
                      onChange={(e) => {
                        const updated = [...domains];
                        updated[idx].name = e.target.value;
                        setDomains(updated);
                      }}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white w-44 focus:outline-none"
                    />
                    <input
                      type="text"
                      placeholder="https://..."
                      value={dom.url}
                      onChange={(e) => {
                        const updated = [...domains];
                        updated[idx].url = e.target.value;
                        setDomains(updated);
                      }}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white flex-1 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveDomain(idx)}
                      className="p-1.5 text-slate-500 hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 6: Review & Confirmation */}
          {step === 6 && (
            <div className="space-y-4 animate-fade-in text-xs">
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Step 6: Review & Finalize Onboarding</h4>
              
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                <div className="flex items-center gap-3">
                  <img src={logoUrl} alt="Logo" className="w-12 h-12 rounded-lg object-cover bg-slate-800 border border-slate-700" />
                  <div>
                    <h5 className="text-sm font-bold text-white">{name}</h5>
                    <p className="text-[11px] text-slate-400">{industry} • {website}</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-[11px]">
                  <div>
                    <span className="text-slate-500 block">Social Accounts:</span>
                    <span className="font-semibold text-slate-200">{socialAccounts.length} Verified</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Mobile Apps:</span>
                    <span className="font-semibold text-slate-200">{mobileApps.length} Verified</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Official Domains:</span>
                    <span className="font-semibold text-slate-200">{domains.length} Whitelisted</span>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-[11px] flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 flex-shrink-0 text-cyan-400" />
                <span>
                  All assets configured above will automatically receive <strong>0 Threat Risk</strong> under the Official Asset Exclusion Rule.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="p-4 px-6 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
          <button
            type="button"
            onClick={handleBack}
            disabled={step === 1}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back</span>
          </button>

          {step < 6 ? (
            <button
              type="button"
              onClick={handleNext}
              className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition active:scale-95"
            >
              <span>Continue</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleFinish}
              disabled={loading}
              className="px-5 py-1.5 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-emerald-500/20 transition active:scale-95"
            >
              {loading ? (
                <span>Registering & Initiating Monitoring...</span>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Start Monitoring</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
