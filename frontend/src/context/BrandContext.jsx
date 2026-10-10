import React, { createContext, useContext, useState, useEffect } from 'react';
import { getBrands, getAlerts, loadDemoEnvironment } from '../services/api';

const BrandContext = createContext();

export const BrandProvider = ({ children }) => {
  const [brands, setBrands] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unreadAlertsCount, setUnreadAlertsCount] = useState(0);
  
  // Global Modals State
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [scanModalInitialUrl, setScanModalInitialUrl] = useState('');
  const [isAddBrandOpen, setIsAddBrandOpen] = useState(false);
  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState(false);
  const [selectedEvidenceThreatId, setSelectedEvidenceThreatId] = useState(null);

  const fetchBrands = async () => {
    try {
      const res = await getBrands();
      setBrands(res.data);
      if (res.data.length > 0 && !selectedBrand) {
        setSelectedBrand(res.data[0]);
      } else if (res.data.length > 0 && selectedBrand) {
        // Keep current selected updated or fallback to first
        const updated = res.data.find(b => b.id === selectedBrand.id) || res.data[0];
        setSelectedBrand(updated);
      } else if (res.data.length === 0) {
        setSelectedBrand(null);
      }
    } catch (err) {
      console.error("Failed to fetch brands", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlertsCount = async (brandId) => {
    try {
      const res = await getAlerts({ brand_id: brandId, unread_only: true });
      setUnreadAlertsCount(res.data.length);
    } catch (err) {
      console.error("Failed to fetch alerts count", err);
    }
  };

  useEffect(() => {
    fetchBrands();
  }, []);

  useEffect(() => {
    if (selectedBrand) {
      fetchAlertsCount(selectedBrand.id);
    }
  }, [selectedBrand]);

  const handleLoadDemo = async () => {
    try {
      setLoading(true);
      await loadDemoEnvironment();
      await fetchBrands();
      // Reload fresh alerts
      if (selectedBrand) {
        await fetchAlertsCount(selectedBrand.id);
      }
    } catch (err) {
      console.error("Failed to load demo environment", err);
    } finally {
      setLoading(false);
    }
  };

  const openScanModal = (defaultUrl = '') => {
    setScanModalInitialUrl(defaultUrl);
    setIsScanModalOpen(true);
  };

  const openEvidenceModal = (threatId) => {
    setSelectedEvidenceThreatId(threatId);
    setIsEvidenceModalOpen(true);
  };

  return (
    <BrandContext.Provider
      value={{
        brands,
        selectedBrand,
        setSelectedBrand,
        loading,
        refreshBrands: fetchBrands,
        unreadAlertsCount,
        refreshAlertsCount: () => selectedBrand && fetchAlertsCount(selectedBrand.id),
        handleLoadDemo,
        isScanModalOpen,
        setIsScanModalOpen,
        scanModalInitialUrl,
        openScanModal,
        isAddBrandOpen,
        setIsAddBrandOpen,
        isEvidenceModalOpen,
        setIsEvidenceModalOpen,
        selectedEvidenceThreatId,
        openEvidenceModal,
      }}
    >
      {children}
    </BrandContext.Provider>
  );
};

export const useBrand = () => {
  const context = useContext(BrandContext);
  if (!context) {
    throw new Error("useBrand must be used within a BrandProvider");
  }
  return context;
};
