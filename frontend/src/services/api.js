// import axios from 'axios';

// // Keep API calls same-origin so local, container, and hosted deployments use
// // the active site's protocol and hostname instead of a baked-in localhost URL.
// const API_BASE = import.meta.env.VITE_API_BASE_URL?.trim() || '/api';

// const api = axios.create({
//   baseURL: API_BASE,
//   headers: {
//     'Content-Type': 'application/json',
//   },
//   timeout: 15000,
// });

// // Attach Authorization header if JWT token exists in localStorage
// api.interceptors.request.use(
//   (config) => {
//     const token = localStorage.getItem('brandshield_token');
//     if (token) {
//       config.headers['Authorization'] = `Bearer ${token}`;
//     }
//     return config;
//   },
//   (error) => Promise.reject(error)
// );

// // Response interceptor: on 401 Unauthorized, redirect to login if session expired
// api.interceptors.response.use(
//   (response) => response,
//   (error) => {
//     if (error.response && error.response.status === 401) {
//       const url = error.config?.url || '';
//       const isAuthCall = url.includes('/auth/login') || url.includes('/auth/register');
//       if (!isAuthCall && localStorage.getItem('brandshield_token')) {
//         localStorage.removeItem('brandshield_token');
//         localStorage.removeItem('brandshield_user');
//         if (window.location.pathname !== '/login') {
//           window.location.href = '/login';
//         }
//       }
//     }
//     return Promise.reject(error);
//   }
// );

// // Brands
// export const getBrands = (includeArchived = false) => api.get(`/brands?include_archived=${includeArchived}`);
// export const getBrand = (id) => api.get(`/brands/${id}`);
// export const createBrand = (data) => api.post('/brands', data);
// export const updateBrand = (id, data) => api.put(`/brands/${id}`, data);
// export const archiveBrand = (id) => api.delete(`/brands/${id}?cascade=false`);
// export const deleteBrand = (id, cascade = true) => api.delete(`/brands/${id}?cascade=${cascade}`);
// export const getOfficialAssets = (brandId) => api.get(`/brands/${brandId}/official-assets`);
// export const addOfficialAsset = (brandId, data) => api.post(`/brands/${brandId}/official-assets`, data);
// export const updateOfficialAsset = (brandId, assetId, data) => api.put(`/brands/${brandId}/official-assets/${assetId}`, data);
// export const deleteOfficialAsset = (brandId, assetId) => api.delete(`/brands/${brandId}/official-assets/${assetId}`);
// export const syncBrandWizard = (brandId, data) => api.put(`/brands/${brandId}/wizard`, data);
// export const uploadBrandLogo = (formData) => api.post('/brands/upload-logo', formData, {
//   headers: { 'Content-Type': 'multipart/form-data' }
// }).then((response) => {
//   const apiOrigin = new URL(API_BASE, window.location.origin).origin;
//   if (apiOrigin !== window.location.origin && response.data.relative_url) {
//     response.data.logo_url = new URL(response.data.relative_url, apiOrigin).toString();
//   }
//   return response;
// });

// // Social Monitoring
// export const scanSocial = (data) => api.post('/social/scan', data);
// export const getSocialThreats = (params) => api.get('/social/threats', { params });
// export const updateSocialThreat = (id, data) => api.put(`/social/threats/${id}`, data);
// export const deleteSocialThreat = (id) => api.delete(`/social/threats/${id}`);

// // App Monitoring
// export const scanApp = (data) => api.post('/apps/scan', data);
// export const getAppThreats = (params) => api.get('/apps/threats', { params });
// export const updateAppThreat = (id, data) => api.put(`/apps/threats/${id}`, data);
// export const deleteAppThreat = (id) => api.delete(`/apps/threats/${id}`);

// // Universal Scan Link
// export const scanUniversalLink = (data) => api.post('/scan-link', data);

// // Threats
// export const getThreats = (params) => api.get('/threats', { params });
// export const getThreat = (id) => api.get(`/threats/${id}`);
// export const updateThreat = (id, data) => api.put(`/threats/${id}`, data);
// export const deleteThreat = (id) => api.delete(`/threats/${id}`);
// export const bulkDeleteThreats = (ids) => api.post('/threats/bulk-delete', { ids });
// export const markThreatReviewed = (id) => api.post(`/threats/${id}/mark-reviewed`);
// export const resolveThreat = (id) => api.post(`/threats/${id}/resolve`);
// export const markThreatLegitimate = (id) => api.post(`/threats/${id}/mark-legitimate`);

// // Investigations
// export const getInvestigations = (brandId) => api.get('/investigations', { params: { brand_id: brandId } });
// export const getInvestigation = (id) => api.get(`/investigations/${id}`);
// export const createInvestigation = (data) => api.post('/investigations', data);

// // Campaigns
// export const getCampaigns = (brandId) => api.get('/campaigns', { params: { brand_id: brandId } });
// export const getCampaign = (id) => api.get(`/campaigns/${id}`);
// export const recorrelateCampaigns = (brandId) => api.post(`/campaigns/recorrelate/${brandId}`);

// // Analytics
// export const getAnalytics = (params) => api.get('/analytics', { params });

// // Alerts
// export const getAlerts = (params) => api.get('/alerts', { params });
// export const markAlertRead = (id) => api.post(`/alerts/${id}/read`);
// export const markAllAlertsRead = (brandId) => api.post('/alerts/mark-all-read', null, { params: { brand_id: brandId } });

// // Evidence
// export const generateEvidence = (threatId) => api.post(`/evidence/${threatId}/generate`);
// export const getEvidence = (threatId) => api.get(`/evidence/${threatId}`);

// // Demo
// export const loadDemoEnvironment = () => api.post('/demo/load');

// // Instagram Risk Analyzer
// export const analyzeInstagramProfile = (data) => api.post('/instagram/analyze', data);
// export const getInstagramHistory = (brandId) => api.get('/instagram/history', { params: { brand_id: brandId } });
// export const createInvestigationFromInstagram = (data) => api.post('/instagram/investigate', data);

// // AI Brand Profile & Website Authenticity
// export const verifyBrandProfile = (data) => api.post('/authenticity/verify-brand', data);
// export const analyzeWebsiteAuthenticity = (data) => api.post('/authenticity/analyze-website', data);
// export const verifyImageAuthenticity = (data) => api.post('/authenticity/verify-image', data);
// export const overrideAuthenticityVerdict = (data) => api.post('/authenticity/override-verdict', data);
// export const getAuthenticityAlerts = (params) => api.get('/authenticity/alerts', { params });
// export const escalateAuthenticityInvestigation = (data) => api.post('/authenticity/investigate', data);
// export const getBrandTrustScore = (brandName) => api.get('/authenticity/trust-score', { params: { brand_name: brandName } });

// // Multi-Platform Social Account Verification
// export const verifyAccount = (data) => api.post('/verification/verify-account', data);
// export const getScanHistory = (params) => api.get('/verification/scan-history', { params });
// export const deleteScanHistoryItem = (id) => api.delete(`/verification/scan-history/${id}`);

// // Duplicate & Impersonation Detection
// export const scanDuplicates = (data) => api.post('/duplicate-detection/scan', data);
// export const getDuplicateHistory = (params) => api.get('/duplicate-detection/history', { params });

// // Dedicated Social Analyzers
// export const analyzeFacebookAccount = (data) => api.post('/facebook/analyze', data);
// export const analyzeXAccount = (data) => api.post('/x/analyze', data);
// export const analyzeLinkedInAccount = (data) => api.post('/linkedin/analyze', data);

// // Compliance & Risk Reports
// export const getReportsSummary = (params) => api.get('/reports/summary', { params });
// export const exportAuditReport = (params) => api.get('/reports/export', { params });

// // User Profile & Legacy Helpers
// export const getUserProfile = () => api.get('/user/profile');
// export const updateUserProfile = (data) => api.put('/user/profile', data);
// export const createUserAccount = (data) => api.post('/user/create-account', data);
// export const forgotPassword = (data) => api.post('/user/forgot-password', data);

// // Enterprise Authentication & User Management (BrandShield AI)
// export const loginUser = (data) => api.post('/auth/login', data);
// export const registerUser = (data) => api.post('/auth/register', data);
// export const googleAuth = (data) => api.post('/auth/google', data);
// export const getCurrentUser = () => api.get('/auth/me');
// export const getCurrentUserProfile = () => api.get('/users/me');
// export const updateCurrentUserProfile = (data) => api.patch('/users/me', data);
// export const changePassword = (data) => api.post('/auth/change-password', data);
// export const logoutUser = () => api.post('/auth/logout');
// export const requestPasswordReset = (data) => api.post('/auth/forgot-password', data);
// export const validateResetToken = (data) => api.post('/auth/validate-reset-token', data);
// export const resetPassword = (data) => api.post('/auth/reset-password', data);
// export const verifyEmail = (token, email) => api.get('/auth/verify-email', { params: { token, email } });

// export default api;




import axios from 'axios';

// API configuration
// Local frontend: http://localhost:5173
// Local backend:  http://127.0.0.1:8000
// Production:     Configure VITE_API_BASE_URL in your deployment settings.

const configuredApiBase = import.meta.env.VITE_API_BASE_URL?.trim();

const isLocalHost =
  typeof window !== 'undefined' &&
  ['localhost', '127.0.0.1'].includes(window.location.hostname);

const API_BASE =
  configuredApiBase ||
  (isLocalHost ? 'http://127.0.0.1:8000/api' : '/api');

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Attach JWT authorization token when available.
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('brandshield_token');

    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Handle expired sessions.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || '';

      const isAuthCall =
        url.includes('/auth/login') ||
        url.includes('/auth/register') ||
        url.includes('/auth/google');

      if (
        !isAuthCall &&
        localStorage.getItem('brandshield_token')
      ) {
        localStorage.removeItem('brandshield_token');
        localStorage.removeItem('brandshield_user');

        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

// Brands
export const getBrands = (includeArchived = false) =>
  api.get(`/brands?include_archived=${includeArchived}`);

export const getBrand = (id) => api.get(`/brands/${id}`);
export const createBrand = (data) => api.post('/brands', data);
export const updateBrand = (id, data) => api.put(`/brands/${id}`, data);

export const archiveBrand = (id) =>
  api.delete(`/brands/${id}?cascade=false`);

export const deleteBrand = (id, cascade = true) =>
  api.delete(`/brands/${id}?cascade=${cascade}`);

export const getOfficialAssets = (brandId) =>
  api.get(`/brands/${brandId}/official-assets`);

export const addOfficialAsset = (brandId, data) =>
  api.post(`/brands/${brandId}/official-assets`, data);

export const updateOfficialAsset = (brandId, assetId, data) =>
  api.put(`/brands/${brandId}/official-assets/${assetId}`, data);

export const deleteOfficialAsset = (brandId, assetId) =>
  api.delete(`/brands/${brandId}/official-assets/${assetId}`);

export const syncBrandWizard = (brandId, data) =>
  api.put(`/brands/${brandId}/wizard`, data);

export const uploadBrandLogo = (formData) =>
  api.post('/brands/upload-logo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((response) => {
    const apiOrigin = new URL(API_BASE, window.location.origin).origin;

    if (
      apiOrigin !== window.location.origin &&
      response.data.relative_url
    ) {
      response.data.logo_url = new URL(
        response.data.relative_url,
        apiOrigin
      ).toString();
    }

    return response;
  });

// Social Monitoring
export const scanSocial = (data) => api.post('/social/scan', data);
export const getSocialThreats = (params) =>
  api.get('/social/threats', { params });

export const updateSocialThreat = (id, data) =>
  api.put(`/social/threats/${id}`, data);

export const deleteSocialThreat = (id) =>
  api.delete(`/social/threats/${id}`);

// App Monitoring
export const scanApp = (data) => api.post('/apps/scan', data);
export const getAppThreats = (params) =>
  api.get('/apps/threats', { params });

export const updateAppThreat = (id, data) =>
  api.put(`/apps/threats/${id}`, data);

export const deleteAppThreat = (id) =>
  api.delete(`/apps/threats/${id}`);

// Universal Scan Link
export const scanUniversalLink = (data) =>
  api.post('/scan-link', data);

// Threats
export const getThreats = (params) => api.get('/threats', { params });
export const getThreat = (id) => api.get(`/threats/${id}`);

export const updateThreat = (id, data) =>
  api.put(`/threats/${id}`, data);

export const deleteThreat = (id) => api.delete(`/threats/${id}`);

export const bulkDeleteThreats = (ids) =>
  api.post('/threats/bulk-delete', { ids });

export const markThreatReviewed = (id) =>
  api.post(`/threats/${id}/mark-reviewed`);

export const resolveThreat = (id) =>
  api.post(`/threats/${id}/resolve`);

export const markThreatLegitimate = (id) =>
  api.post(`/threats/${id}/mark-legitimate`);

// Investigations
export const getInvestigations = (brandId) =>
  api.get('/investigations', { params: { brand_id: brandId } });

export const getInvestigation = (id) =>
  api.get(`/investigations/${id}`);

export const createInvestigation = (data) =>
  api.post('/investigations', data);

// Campaigns
export const getCampaigns = (brandId) =>
  api.get('/campaigns', { params: { brand_id: brandId } });

export const getCampaign = (id) => api.get(`/campaigns/${id}`);

export const recorrelateCampaigns = (brandId) =>
  api.post(`/campaigns/recorrelate/${brandId}`);

// Analytics
export const getAnalytics = (params) =>
  api.get('/analytics', { params });

// Alerts
export const getAlerts = (params) => api.get('/alerts', { params });

export const markAlertRead = (id) =>
  api.post(`/alerts/${id}/read`);

export const markAllAlertsRead = (brandId) =>
  api.post('/alerts/mark-all-read', null, {
    params: { brand_id: brandId },
  });

// Evidence
export const generateEvidence = (threatId) =>
  api.post(`/evidence/${threatId}/generate`);

export const getEvidence = (threatId) =>
  api.get(`/evidence/${threatId}`);

// Demo
export const loadDemoEnvironment = () =>
  api.post('/demo/load');

// Instagram Risk Analyzer
export const analyzeInstagramProfile = (data) =>
  api.post('/instagram/analyze', data);

export const getInstagramHistory = (brandId) =>
  api.get('/instagram/history', {
    params: { brand_id: brandId },
  });

export const createInvestigationFromInstagram = (data) =>
  api.post('/instagram/investigate', data);

// AI Brand Profile & Website Authenticity
export const verifyBrandProfile = (data) =>
  api.post('/authenticity/verify-brand', data);

export const analyzeWebsiteAuthenticity = (data) =>
  api.post('/authenticity/analyze-website', data);

export const verifyImageAuthenticity = (data) =>
  api.post('/authenticity/verify-image', data);

export const overrideAuthenticityVerdict = (data) =>
  api.post('/authenticity/override-verdict', data);

export const getAuthenticityAlerts = (params) =>
  api.get('/authenticity/alerts', { params });

export const escalateAuthenticityInvestigation = (data) =>
  api.post('/authenticity/investigate', data);

export const getBrandTrustScore = (brandName) =>
  api.get('/authenticity/trust-score', {
    params: { brand_name: brandName },
  });

// Multi-Platform Social Account Verification
export const verifyAccount = (data) =>
  api.post('/verification/verify-account', data);

export const getScanHistory = (params) =>
  api.get('/verification/scan-history', { params });

export const deleteScanHistoryItem = (id) =>
  api.delete(`/verification/scan-history/${id}`);

// Duplicate & Impersonation Detection
export const scanDuplicates = (data) =>
  api.post('/duplicate-detection/scan', data);

export const getDuplicateHistory = (params) =>
  api.get('/duplicate-detection/history', params ? { params } : undefined);

// Dedicated Social Analyzers
export const analyzeFacebookAccount = (data) =>
  api.post('/facebook/analyze', data);

export const analyzeXAccount = (data) =>
  api.post('/x/analyze', data);

export const analyzeLinkedInAccount = (data) =>
  api.post('/linkedin/analyze', data);

// Compliance & Risk Reports
export const getReportsSummary = (params) =>
  api.get('/reports/summary', { params });

export const exportAuditReport = (params) =>
  api.get('/reports/export', { params });

// User Profile & Legacy Helpers
export const getUserProfile = () =>
  api.get('/user/profile');

export const updateUserProfile = (data) =>
  api.put('/user/profile', data);

export const createUserAccount = (data) =>
  api.post('/user/create-account', data);

export const forgotPassword = (data) =>
  api.post('/user/forgot-password', data);

// Enterprise Authentication & User Management
export const loginUser = (data) =>
  api.post('/auth/login', data);

export const registerUser = (data) =>
  api.post('/auth/register', data);

export const googleAuth = (data) =>
  api.post('/auth/google', data);

export const getCurrentUser = () =>
  api.get('/auth/me');

export const getCurrentUserProfile = () =>
  api.get('/users/me');

export const updateCurrentUserProfile = (data) =>
  api.patch('/users/me', data);

export const changePassword = (data) =>
  api.post('/auth/change-password', data);

export const logoutUser = () =>
  api.post('/auth/logout');

export const requestPasswordReset = (data) =>
  api.post('/auth/forgot-password', data);

export const validateResetToken = (data) =>
  api.post('/auth/validate-reset-token', data);

export const resetPassword = (data) =>
  api.post('/auth/reset-password', data);

export const verifyEmail = (token, email) =>
  api.get('/auth/verify-email', {
    params: { token, email },
  });

export default api;