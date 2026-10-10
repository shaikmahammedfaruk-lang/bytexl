import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { BrandProvider } from './context/BrandContext';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ScanModal from './components/ScanModal';
import AddBrandWizardModal from './components/AddBrandWizardModal';
import EvidenceModal from './components/EvidenceModal';

import LoginPage from './pages/LoginPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import DashboardPage from './pages/DashboardPage';
import BrandsPage from './pages/BrandsPage';
import BrandDetailPage from './pages/BrandDetailPage';
import SocialMonitoringPage from './pages/SocialMonitoringPage';
import AppMonitoringPage from './pages/AppMonitoringPage';
import ThreatCenterPage from './pages/ThreatCenterPage';
import ThreatDetailPage from './pages/ThreatDetailPage';
import InvestigationsPage from './pages/InvestigationsPage';
import InvestigationDetailPage from './pages/InvestigationDetailPage';
import CampaignsPage from './pages/CampaignsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AlertsPage from './pages/AlertsPage';
import SettingsPage from './pages/SettingsPage';
import ProfilePage from './pages/ProfilePage';
import InstagramAnalyzerPage from './pages/InstagramAnalyzerPage';
import BrandAuthenticityPage from './pages/BrandAuthenticityPage';
import FacebookAnalyzerPage from './pages/FacebookAnalyzerPage';
import XAnalyzerPage from './pages/XAnalyzerPage';
import LinkedInAnalyzerPage from './pages/LinkedInAnalyzerPage';
import MultiPlatformVerificationPage from './pages/MultiPlatformVerificationPage';
import DuplicateDetectionPage from './pages/DuplicateDetectionPage';
import ScanHistoryPage from './pages/ScanHistoryPage';
import ReportsPage from './pages/ReportsPage';

import ErrorBoundary from './components/ErrorBoundary';

function AppLayout() {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-[#070a12] text-slate-100 overflow-hidden font-sans">
      {/* Dark Enterprise Sidebar (Desktop docked + Mobile slide-out drawer) */}
      <Sidebar
        mobileOpen={mobileSidebarOpen}
        onClose={() => setMobileSidebarOpen(false)}
      />

      {/* Main Content Layout */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Global Topbar Header with Mobile Hamburger Menu */}
        <Header
          onToggleMobileSidebar={() => setMobileSidebarOpen((prev) => !prev)}
          mobileSidebarOpen={mobileSidebarOpen}
        />

        {/* Scrollable Page Body with Responsive Padding */}
        <main className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-6 lg:p-8">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/brands" element={<BrandsPage />} />
              <Route path="/brands/:id" element={<BrandDetailPage />} />
              <Route path="/social-monitoring" element={<SocialMonitoringPage />} />
              <Route path="/instagram-analyzer" element={<InstagramAnalyzerPage />} />
              <Route path="/facebook-analyzer" element={<FacebookAnalyzerPage />} />
              <Route path="/x-analyzer" element={<XAnalyzerPage />} />
              <Route path="/linkedin-analyzer" element={<LinkedInAnalyzerPage />} />
              <Route path="/multi-platform-verification" element={<MultiPlatformVerificationPage />} />
              <Route path="/duplicate-detection" element={<DuplicateDetectionPage />} />
              <Route path="/scan-history" element={<ScanHistoryPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/authenticity-verification" element={<BrandAuthenticityPage />} />
              <Route path="/app-monitoring" element={<AppMonitoringPage />} />
              <Route path="/threat-center" element={<ThreatCenterPage />} />
              <Route path="/threats/:id" element={<ThreatDetailPage />} />
              <Route path="/investigations" element={<InvestigationsPage />} />
              <Route path="/investigations/:id" element={<InvestigationDetailPage />} />
              <Route path="/campaigns" element={<CampaignsPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>

      {/* Global Modals Mounted for Global Accessibility */}
      <ScanModal />
      <AddBrandWizardModal />
      <EvidenceModal />
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <BrandProvider>
            <Routes>
              {/* Public Enterprise Authentication Routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />

              {/* Protected SOC Dashboard & Operations */}
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </BrandProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
