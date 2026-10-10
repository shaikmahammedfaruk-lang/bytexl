import React, { useState, useEffect } from 'react';
import {
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  KeyRound,
  Shield,
  ShieldCheck,
  Building2,
  Clock,
  Phone,
  Briefcase,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  LogOut,
  Sparkles,
  Edit3,
  Calendar,
  Layers,
  X,
  Check,
  Globe
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const {
    user,
    loading: authLoading,
    refreshUser,
    updateProfile,
    changeUserPassword,
    logout
  } = useAuth();
  const navigate = useNavigate();

  const [pageLoading, setPageLoading] = useState(true);
  const [fetchError, setFetchError] = useState('');

  // Edit Mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    full_name: '',
    username: '',
    email: '',
    phone: '',
    organization: '',
    department: '',
    avatar_url: ''
  });
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState('');
  const [saveError, setSaveError] = useState('');

  // Change Password Modal state
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // Password strength calculation
  const getPasswordStrength = (pass) => {
    let score = 0;
    if (pass.length >= 8) score += 1;
    if (/[A-Z]/.test(pass)) score += 1;
    if (/[a-z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass) || /[^A-Za-z0-9]/.test(pass)) score += 1;
    return score;
  };
  const pwStrength = getPasswordStrength(newPassword);

  // Fetch the latest profile data on component mount
  useEffect(() => {
    let isMounted = true;
    const fetchLatest = async () => {
      setPageLoading(true);
      setFetchError('');
      try {
        const freshUser = await refreshUser();
        if (isMounted && freshUser) {
          syncForm(freshUser);
        }
      } catch (err) {
        if (isMounted) {
          setFetchError(err.response?.data?.detail || 'Unable to load profile data.');
        }
      } finally {
        if (isMounted) setPageLoading(false);
      }
    };

    fetchLatest();
    return () => {
      isMounted = false;
    };
  }, [refreshUser]);

  // Synchronize editForm with active user
  const syncForm = (userData) => {
    if (!userData) return;
    setEditForm({
      full_name: userData.full_name || '',
      username: userData.username || '',
      email: userData.email || '',
      phone: userData.phone || '',
      organization: userData.organization || '',
      department: userData.department || '',
      avatar_url: userData.avatar_url || ''
    });
  };

  useEffect(() => {
    if (user) {
      syncForm(user);
    }
  }, [user]);

  // Handle Edit Profile submission
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSaveError('');
    setSaveSuccess('');
    setSaveLoading(true);

    try {
      await updateProfile({
        full_name: editForm.full_name,
        username: editForm.username,
        email: editForm.email,
        phone: editForm.phone,
        organization: editForm.organization,
        department: editForm.department,
        avatar_url: editForm.avatar_url
      });
      setIsEditing(false);
      setSaveSuccess('Profile credentials successfully updated and synchronized.');
      setTimeout(() => setSaveSuccess(''), 4500);
    } catch (err) {
      setSaveError(err.message || 'Failed to update profile.');
    } finally {
      setSaveLoading(false);
    }
  };

  // Handle Change Password submission
  const handleChangePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (newPassword !== confirmPassword) {
      setPasswordError('New password and confirmation do not match.');
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters long.');
      return;
    }

    setPasswordLoading(true);
    try {
      await changeUserPassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
      });
      setPasswordSuccess('Password successfully updated! Your credentials have been secured.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => {
        setPasswordSuccess('');
        setShowPasswordModal(false);
      }, 2500);
    } catch (err) {
      setPasswordError(err.message || 'Failed to update password.');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  // Timestamp formatting helper
  const formatTimestamp = (isoString) => {
    if (!isoString) return 'Not recorded';
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return 'Not recorded';
      return d.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Not recorded';
    }
  };

  // Initials for avatar fallback
  const displayName = user?.full_name || user?.username || 'Analyst';
  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase() || 'SA';

  // 1. Loading Skeleton State
  if (pageLoading && !user) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto animate-pulse">
        <div className="h-10 bg-slate-900/80 rounded-xl w-1/3"></div>
        <div className="h-32 bg-slate-900/80 rounded-2xl"></div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-96 bg-slate-900/80 rounded-2xl"></div>
          <div className="h-96 bg-slate-900/80 rounded-2xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <User className="w-5 h-5 text-cyan-400" />
            User Account & Profile
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Active security operations credentials, authenticated identity, and session access control.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isEditing ? (
            <button
              onClick={() => {
                syncForm(user);
                setIsEditing(true);
              }}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition active:scale-95 flex items-center gap-1.5 shadow-sm"
            >
              <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
              <span>Edit Credentials</span>
            </button>
          ) : (
            <button
              onClick={() => {
                syncForm(user);
                setIsEditing(false);
              }}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs font-semibold transition"
            >
              Cancel
            </button>
          )}

          <button
            onClick={() => {
              setPasswordError('');
              setPasswordSuccess('');
              setShowPasswordModal(true);
            }}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold transition active:scale-95 flex items-center gap-1.5 shadow-md shadow-cyan-500/20"
          >
            <KeyRound className="w-3.5 h-3.5" />
            <span>Change Password</span>
          </button>
        </div>
      </div>

      {/* Global Notifications */}
      {fetchError && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{fetchError}</span>
        </div>
      )}
      {saveSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>{saveSuccess}</span>
        </div>
      )}
      {saveError && (
        <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{saveError}</span>
        </div>
      )}

      {/* Profile Identity Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#0b1328] via-[#0d1630] to-[#0a1020] border border-cyan-500/30 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          {/* Avatar Image or Initials */}
          <div className="relative flex-shrink-0">
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={displayName}
                className="w-16 h-16 rounded-2xl object-cover border-2 border-cyan-400/40 shadow-lg shadow-cyan-500/25"
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center text-white text-xl font-black shadow-lg shadow-cyan-500/25 border-2 border-cyan-400/40">
                {initials}
              </div>
            )}
            <span className="absolute -bottom-1 -right-1 flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500 border-2 border-[#0b1328]"></span>
            </span>
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-lg font-bold text-white tracking-wide">
                {user?.full_name || 'Not set'}
              </h2>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                {user?.role || 'SOC Analyst'}
              </span>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                {user?.is_active !== false ? 'Active Account' : 'Suspended'}
              </span>
              {user?.provider === 'google' && (
                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-blue-500/15 text-blue-300 border border-blue-500/30 flex items-center gap-1">
                  Google Auth
                </span>
              )}
            </div>

            <p className="text-xs text-slate-400 mt-1 flex items-center gap-3 flex-wrap">
              <span className="flex items-center gap-1 text-slate-300 font-mono">
                @{user?.username || 'Not set'}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3 text-slate-400" />
                {user?.email || 'Not set'}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Building2 className="w-3 h-3 text-slate-400" />
                {user?.organization || 'Not set'}
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleLogout}
            className="px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-700/80 text-xs font-semibold transition flex items-center gap-1.5"
            title="Terminate Active Session"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Details & Security Policy */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Columns: Credentials & Dynamic Details / Edit Form */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5 shadow-lg">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  {isEditing ? 'Edit Profile & Credentials' : 'Account Credentials & Information'}
                </h3>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                ID: {user?.id ? user.id.substring(0, 12) + '...' : 'Live'}
              </span>
            </div>

            {!isEditing ? (
              /* VIEW MODE: Database-Backed Credentials & Fields */
              <div className="space-y-4 text-xs">
                {/* Username Tile */}
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">
                      Username / Handle
                    </span>
                    <span className="font-mono text-cyan-300 font-semibold text-sm">
                      {user?.username ? `@${user.username}` : 'Not set'}
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] font-mono">
                    AUTHENTICATED HANDLE
                  </span>
                </div>

                {/* Email Address Tile */}
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">
                      Registered Email Address
                    </span>
                    <span className="text-slate-200 font-semibold text-sm flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      {user?.email || 'Not set'}
                    </span>
                  </div>
                  {user?.email_verified ? (
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-bold border border-emerald-500/20">
                      VERIFIED
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 text-[10px] font-bold border border-amber-500/20">
                      UNVERIFIED
                    </span>
                  )}
                </div>

                {/* Password Tile: Secure Interface (No Plaintext Password Stored or Exposed) */}
                <div className="p-3.5 rounded-xl bg-slate-950 border border-cyan-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-0.5">
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">
                      Account Password
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-400 font-semibold text-sm tracking-widest">
                        ••••••••••••••••
                      </span>
                      <span className="text-[11px] text-slate-500">
                        (Bcrypt 256-Bit Encrypted)
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      setPasswordError('');
                      setPasswordSuccess('');
                      setShowPasswordModal(true);
                    }}
                    className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 transition active:scale-95"
                  >
                    <KeyRound className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Change Password</span>
                  </button>
                </div>

                {/* Secondary Details: Full Name, Role, Organization, Department, Phone */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">
                      Full Name
                    </span>
                    <span className="text-slate-200 font-semibold">
                      {user?.full_name || 'Not set'}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">
                      Assigned Role
                    </span>
                    <span className="text-slate-200 font-semibold">
                      {user?.role || 'SOC Analyst'}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">
                      Organization
                    </span>
                    <span className="text-slate-200 font-semibold">
                      {user?.organization || 'Not set'}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">
                      Department
                    </span>
                    <span className="text-slate-200 font-semibold">
                      {user?.department || 'Not set'}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">
                      Contact Phone
                    </span>
                    <span className="text-slate-200 font-semibold">
                      {user?.phone || 'Not set'}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                    <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">
                      Avatar URL
                    </span>
                    <span className="text-slate-200 font-semibold truncate block">
                      {user?.avatar_url || 'Not set (using initials)'}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              /* EDIT MODE: Functional Form Updating Real Database Record */
              <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={editForm.full_name}
                      onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                      placeholder="e.g. Alex Morgan"
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                      Username / Handle *
                    </label>
                    <input
                      type="text"
                      required
                      value={editForm.username}
                      onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                      placeholder="e.g. alex_drp"
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white font-mono text-xs focus:outline-none focus:border-cyan-400"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                      Registered Email Address *
                    </label>
                    <input
                      type="email"
                      required
                      value={editForm.email}
                      onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                      placeholder="e.g. alex@brandshield.ai"
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                      Contact Phone
                    </label>
                    <input
                      type="text"
                      value={editForm.phone}
                      onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                      placeholder="e.g. +1 (555) 019-2834"
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-400"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                      Organization
                    </label>
                    <input
                      type="text"
                      value={editForm.organization}
                      onChange={(e) => setEditForm({ ...editForm, organization: e.target.value })}
                      placeholder="e.g. Global SOC Ops"
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-400"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                      Department
                    </label>
                    <input
                      type="text"
                      value={editForm.department}
                      onChange={(e) => setEditForm({ ...editForm, department: e.target.value })}
                      placeholder="e.g. Cyber Digital Risk Protection"
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-400"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                    Profile Photo / Avatar Image URL
                  </label>
                  <input
                    type="url"
                    value={editForm.avatar_url}
                    onChange={(e) => setEditForm({ ...editForm, avatar_url: e.target.value })}
                    placeholder="https://example.com/photo.jpg"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-400"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    Leave blank to display an avatar generated from your initials.
                  </p>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      syncForm(user);
                      setIsEditing(false);
                    }}
                    className="px-4 py-2 rounded-xl bg-slate-800 text-slate-400 text-xs font-semibold hover:bg-slate-700 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saveLoading}
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold shadow-md shadow-cyan-500/20 active:scale-95 transition flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {saveLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                    <span>Save Changes</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Right Column: Security Status, Audit Metadata & Session Information */}
        <div className="space-y-6">
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Shield className="w-4 h-4 text-cyan-400" />
              Security & Access Policy
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Auth Provider:</span>
                <span className="text-slate-300 font-semibold">
                  {user?.provider === 'google' ? 'Google OAuth 2.0' : 'Email & Password'}
                </span>
              </div>

              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">2FA Protection:</span>
                {user?.two_factor_enabled ? (
                  <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-bold text-[10px] border border-emerald-500/30">
                    CONFIGURED
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold text-[10px] border border-slate-700">
                    Not Configured
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Session Protocol:</span>
                <span className="text-slate-300 font-mono text-[11px]">JWT / HMAC-SHA256</span>
              </div>

              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Account Created:</span>
                <span className="text-slate-300 font-mono text-[11px]">
                  {formatTimestamp(user?.created_at)}
                </span>
              </div>

              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Last Login:</span>
                <span className="text-slate-300 font-mono text-[11px]">
                  {formatTimestamp(user?.last_login)}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-400">Password Changed:</span>
                <span className="text-cyan-400 font-mono text-[11px]">
                  {formatTimestamp(user?.password_changed_at)}
                </span>
              </div>
            </div>
          </div>

          {/* DRP Platform Guard Banner */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-cyan-950/40 to-slate-900 border border-cyan-500/20 text-xs space-y-2">
            <div className="flex items-center gap-2 text-cyan-300 font-bold">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              BrandShield Identity Isolation
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Every authenticated action is strictly isolated to your verified enterprise user token.
              Profile modifications are timestamped and synchronized directly with the database.
            </p>
          </div>
        </div>
      </div>

      {/* CHANGE PASSWORD MODAL */}
      {showPasswordModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative w-full max-w-md max-h-[90vh] overflow-y-auto rounded-2xl bg-[#0c1427] border border-cyan-500/30 shadow-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                  <KeyRound className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Change Account Password</h3>
                  <p className="text-[11px] text-slate-400">Secure cryptographic credentials update</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowPasswordModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {passwordSuccess && (
              <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{passwordSuccess}</span>
              </div>
            )}
            {passwordError && (
              <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{passwordError}</span>
              </div>
            )}

            <form onSubmit={handleChangePasswordSubmit} className="space-y-4 text-xs">
              {user?.provider !== 'google' && (
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                    Current Password *
                  </label>
                  <div className="relative">
                    <input
                      type={showCurrentPassword ? 'text' : 'password'}
                      required
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Enter current password"
                      className="w-full px-3 py-2 pr-10 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-400"
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-2.5 text-slate-400 hover:text-white"
                    >
                      {showCurrentPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              )}

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                  New Password *
                </label>
                <div className="relative">
                  <input
                    type={showNewPassword ? 'text' : 'password'}
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Min 8 chars (uppercase, lowercase, number/symbol)"
                    className="w-full px-3 py-2 pr-10 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-3 top-2.5 text-slate-400 hover:text-white"
                  >
                    {showNewPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                  Confirm New Password *
                </label>
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new password"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-cyan-400"
                />
              </div>

              {/* Password strength meter */}
              {newPassword && (
                <div className="space-y-1 pt-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-slate-400">Strength:</span>
                    <span className={`font-bold ${
                      pwStrength <= 1 ? 'text-rose-400' : pwStrength <= 2 ? 'text-amber-400' : pwStrength <= 3 ? 'text-cyan-400' : 'text-emerald-400'
                    }`}>
                      {pwStrength <= 1 ? 'Weak' : pwStrength <= 2 ? 'Moderate' : pwStrength <= 3 ? 'Strong' : 'Very Strong'}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 h-1.5">
                    <div className={`rounded-full ${pwStrength >= 1 ? 'bg-rose-500' : 'bg-slate-800'}`}></div>
                    <div className={`rounded-full ${pwStrength >= 2 ? 'bg-amber-500' : 'bg-slate-800'}`}></div>
                    <div className={`rounded-full ${pwStrength >= 3 ? 'bg-cyan-500' : 'bg-slate-800'}`}></div>
                    <div className={`rounded-full ${pwStrength >= 4 ? 'bg-emerald-500' : 'bg-slate-800'}`}></div>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPasswordModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-400 hover:bg-slate-700 text-xs font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={passwordLoading}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-cyan-500/20 disabled:opacity-50"
                >
                  {passwordLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>Update Password</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
