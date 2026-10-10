import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  loginUser,
  registerUser,
  googleAuth,
  getCurrentUser,
  updateCurrentUserProfile,
  changePassword,
  logoutUser
} from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('brandshield_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('brandshield_token') || null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Initialize and verify authentication on app mount / refresh
  const refreshUser = useCallback(async () => {
    const savedToken = localStorage.getItem('brandshield_token');
    if (!savedToken) {
      setUser(null);
      setToken(null);
      setLoading(false);
      return null;
    }

    try {
      const res = await getCurrentUser();
      if (res && res.data) {
        setUser(res.data);
        localStorage.setItem('brandshield_user', JSON.stringify(res.data));
        return res.data;
      } else {
        throw new Error('Invalid user payload');
      }
    } catch (err) {
      console.warn('Session verification failed or expired:', err.message);
      if (err.response?.status === 401) {
        localStorage.removeItem('brandshield_token');
        localStorage.removeItem('brandshield_user');
        setUser(null);
        setToken(null);
      }
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser().catch(() => {});
  }, [refreshUser]);

  // Handle standard email/password login
  const login = async (email, password) => {
    setAuthError(null);
    try {
      const res = await loginUser({ email, password });
      const { user: authedUser, token: authToken } = res.data;

      localStorage.setItem('brandshield_token', authToken);
      localStorage.setItem('brandshield_user', JSON.stringify(authedUser));

      setToken(authToken);
      setUser(authedUser);
      return authedUser;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Authentication failed. Please verify your credentials.';
      setAuthError(msg);
      throw new Error(msg);
    }
  };

  // Handle user registration
  const register = async (payload) => {
    setAuthError(null);
    try {
      const res = await registerUser(payload);
      const { user: newUser, token: authToken } = res.data;

      if (authToken) {
        localStorage.setItem('brandshield_token', authToken);
        localStorage.setItem('brandshield_user', JSON.stringify(newUser));
        setToken(authToken);
        setUser(newUser);
      }
      return res.data;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Registration failed. Please check your information.';
      setAuthError(msg);
      throw new Error(msg);
    }
  };

  // Handle Google OAuth login/registration
  const googleLogin = useCallback(async (payload) => {
    setAuthError(null);
    try {
      const res = await googleAuth(payload);
      const { user: googleUser, token: authToken } = res.data;

      localStorage.setItem('brandshield_token', authToken);
      localStorage.setItem('brandshield_user', JSON.stringify(googleUser));

      setToken(authToken);
      setUser(googleUser);
      return googleUser;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Google authentication failed.';
      setAuthError(msg);
      throw new Error(msg);
    }
  }, []);

  // Update profile details
  const updateProfile = async (payload) => {
    setAuthError(null);
    try {
      const res = await updateCurrentUserProfile(payload);
      if (res && res.data) {
        setUser(res.data);
        localStorage.setItem('brandshield_user', JSON.stringify(res.data));
        return res.data;
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to update profile.';
      setAuthError(msg);
      throw new Error(msg);
    }
  };

  // Change password securely
  const changeUserPassword = async (payload) => {
    setAuthError(null);
    try {
      const res = await changePassword(payload);
      await refreshUser().catch(() => {});
      return res.data;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to change password.';
      setAuthError(msg);
      throw new Error(msg);
    }
  };

  // Logout
  const logout = async () => {
    try {
      await logoutUser();
    } catch (err) {
      console.warn('Logout notification error:', err);
    } finally {
      localStorage.removeItem('brandshield_token');
      localStorage.removeItem('brandshield_user');
      setUser(null);
      setToken(null);
      setAuthError(null);
    }
  };

  // Direct user update helper (e.g. from local actions)
  const updateActiveUser = (updatedData) => {
    setUser((prev) => {
      const next = { ...prev, ...updatedData };
      localStorage.setItem('brandshield_user', JSON.stringify(next));
      return next;
    });
  };

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    loading,
    authError,
    setAuthError,
    login,
    register,
    googleLogin,
    logout,
    updateActiveUser,
    updateProfile,
    changeUserPassword,
    refreshUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
