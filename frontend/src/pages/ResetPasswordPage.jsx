import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import {
  Shield,
  Lock,
  KeyRound,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ArrowRight
} from 'lucide-react';
import { validateResetToken, resetPassword } from '../services/api';

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const token = searchParams.get('token') || '';
  const email = searchParams.get('email') || '';

  const [isVerifying, setIsVerifying] = useState(true);
  const [isTokenValid, setIsTokenValid] = useState(false);
  const [tokenError, setTokenError] = useState('');

  // Form states
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Password strength
  const getPasswordStrength = (pass) => {
    let score = 0;
    if (pass.length >= 8) score += 1;
    if (/[A-Z]/.test(pass)) score += 1;
    if (/[a-z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass) || /[^A-Za-z0-9]/.test(pass)) score += 1;
    return score;
  };
  const strength = getPasswordStrength(newPassword);

  useEffect(() => {
    const verifyToken = async () => {
      if (!token || !email) {
        setIsVerifying(false);
        setIsTokenValid(false);
        setTokenError('Missing password reset token or email address in link.');
        return;
      }

      try {
        const res = await validateResetToken({ token, email });
        if (res.data && res.data.valid) {
          setIsTokenValid(true);
        } else {
          setIsTokenValid(false);
          setTokenError(res.data?.message || 'Password reset token is invalid or expired.');
        }
      } catch (err) {
        setIsTokenValid(false);
        setTokenError(err.response?.data?.detail || 'Unable to validate reset token.');
      } finally {
        setIsVerifying(false);
      }
    };

    verifyToken();
  }, [token, email]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError('');

    if (newPassword !== confirmPassword) {
      setSubmitError('Passwords do not match.');
      return;
    }
    if (newPassword.length < 8) {
      setSubmitError('Password must be at least 8 characters long.');
      return;
    }

    setIsSubmitting(true);
    try {
      await resetPassword({
        token,
        email,
        new_password: newPassword,
        confirm_password: confirmPassword
      });
      setSubmitSuccess(true);
    } catch (err) {
      setSubmitError(err.response?.data?.detail || 'Failed to reset password. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050814] text-slate-100 flex flex-col justify-between selection:bg-cyan-500 selection:text-black">
      {/* Top Header */}
      <header className="px-6 py-5 flex items-center justify-between border-b border-slate-800/60 bg-[#070b19]/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/25 border border-cyan-400/30">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-black tracking-wider text-white">
                BRAND<span className="text-cyan-400">SHIELD</span>
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                AI
              </span>
            </div>
            <p className="text-[10px] text-slate-400 tracking-wider uppercase font-semibold">
              Digital Risk Protection Platform
            </p>
          </div>
        </div>

        <Link
          to="/login"
          className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold transition"
        >
          Back to Sign In
        </Link>
      </header>

      {/* Center Container */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="max-w-md w-full rounded-2xl bg-[#0c1427]/85 backdrop-blur-xl border border-cyan-500/30 shadow-2xl p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Reset Account Password</h2>
              <p className="text-xs text-slate-400">
                Choose a new strong password for your BrandShield account.
              </p>
            </div>
          </div>

          {/* State 1: Verifying token */}
          {isVerifying && (
            <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              <p className="text-xs text-slate-300">Validating cryptographic security token...</p>
            </div>
          )}

          {/* State 2: Invalid or expired token */}
          {!isVerifying && !isTokenValid && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-rose-200 mb-1">Invalid or Expired Link</h4>
                  <p className="text-rose-300/90 leading-relaxed">{tokenError}</p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => navigate('/login')}
                className="w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs border border-slate-700 transition"
              >
                Return to Sign In & Request New Link
              </button>
            </div>
          )}

          {/* State 3: Password Successfully Updated */}
          {!isVerifying && isTokenValid && submitSuccess && (
            <div className="space-y-4 text-center">
              <div className="p-4 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex flex-col items-center gap-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                <h4 className="font-bold text-emerald-200 text-sm">Password Updated Successfully</h4>
                <p className="text-emerald-300/90 leading-relaxed">
                  Your credentials have been securely updated. You can now sign in to your dashboard.
                </p>
              </div>

              <button
                type="button"
                onClick={() => navigate('/login')}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/25 transition"
              >
                <span>Sign In with New Password</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* State 4: Valid Token, Form to Input New Password */}
          {!isVerifying && isTokenValid && !submitSuccess && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
                Resetting password for: <span className="font-semibold text-cyan-300">{email}</span>
              </div>

              {submitError && (
                <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{submitError}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="text-[11px] uppercase font-bold text-slate-400 tracking-wider block">
                  New Password *
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Min 8 chars (uppercase, lowercase, number)"
                    className="w-full pl-9 pr-9 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-400 transition"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-3 text-slate-400 hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] uppercase font-bold text-slate-400 tracking-wider block">
                  Confirm New Password *
                </label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new password"
                  className="w-full px-3 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-400 transition"
                />
              </div>

              {/* Password strength */}
              {newPassword && (
                <div className="space-y-1 pt-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-slate-400">Strength:</span>
                    <span className={`font-bold ${
                      strength <= 1 ? 'text-rose-400' : strength <= 2 ? 'text-amber-400' : strength <= 3 ? 'text-cyan-400' : 'text-emerald-400'
                    }`}>
                      {strength <= 1 ? 'Weak' : strength <= 2 ? 'Moderate' : strength <= 3 ? 'Strong' : 'Very Strong'}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 h-1.5">
                    <div className={`rounded-full ${strength >= 1 ? 'bg-rose-500' : 'bg-slate-800'}`}></div>
                    <div className={`rounded-full ${strength >= 2 ? 'bg-amber-500' : 'bg-slate-800'}`}></div>
                    <div className={`rounded-full ${strength >= 3 ? 'bg-cyan-500' : 'bg-slate-800'}`}></div>
                    <div className={`rounded-full ${strength >= 4 ? 'bg-emerald-500' : 'bg-slate-800'}`}></div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/25 active:scale-[0.99] transition disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Updating Password...</span>
                  </>
                ) : (
                  <>
                    <span>Confirm & Reset Password</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 border-t border-slate-800/60 bg-[#070b19]/60 text-center text-xs text-slate-500">
        <p>© 2026 BrandShield AI. Advanced Digital Risk Protection & Brand Integrity Intelligence Platform.</p>
      </footer>
    </div>
  );
}
