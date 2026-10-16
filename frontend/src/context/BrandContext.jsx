import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from 'react';
import { getBrands, getAlerts, loadDemoEnvironment } from '../services/api';
import { useAuth } from './AuthContext';

const BrandContext = createContext();

export const BrandProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const accountId = isAuthenticated
    ? String(user?.id || user?._id || '')
    : '';

  return (
    <BrandSessionProvider key={accountId} accountId={accountId}>
      {children}
    </BrandSessionProvider>
  );
};

const BrandSessionProvider = ({ children, accountId }) => {
  const activeAccountRef = useRef(accountId);
  const loadedAccountRef = useRef('');
  const [brands, setBrands] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [loading, setLoading] = useState(Boolean(accountId));
  const [unreadAlertsCount, setUnreadAlertsCount] = useState(0);
  
  // Global Modals State
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [scanModalInitialUrl, setScanModalInitialUrl] = useState('');
  const [isAddBrandOpen, setIsAddBrandOpen] = useState(false);
  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState(false);
  const [selectedEvidenceThreatId, setSelectedEvidenceThreatId] = useState(null);

  const fetchBrands = useCallback(async () => {
    const requestAccountId = activeAccountRef.current;
    if (!requestAccountId) {
      setBrands([]);
      setSelectedBrand(null);
      setUnreadAlertsCount(0);
      setLoading(false);
      return;
    }

    try {
      const res = await getBrands();
      if (activeAccountRef.current !== requestAccountId) {
        return;
      }

      const nextBrands = res.data;
      loadedAccountRef.current = requestAccountId;
      setBrands(nextBrands);
      setSelectedBrand((current) => (
        nextBrands.find((brand) => brand.id === current?.id)
        || nextBrands[0]
        || null
      ));
    } catch (err) {
      if (activeAccountRef.current === requestAccountId) {
        console.error('Failed to fetch brands', err);
      }
    } finally {
      if (activeAccountRef.current === requestAccountId) {
        setLoading(false);
      }
    }
  }, []);

  const fetchAlertsCount = useCallback(async (brandId) => {
    const requestAccountId = activeAccountRef.current;
    if (
      !requestAccountId
      || loadedAccountRef.current !== requestAccountId
      || !brandId
    ) {
      setUnreadAlertsCount(0);
      return;
    }

    try {
      const res = await getAlerts({ brand_id: brandId, unread_only: true });
      if (activeAccountRef.current === requestAccountId) {
        setUnreadAlertsCount(res.data.length);
      }
    } catch (err) {
      if (activeAccountRef.current === requestAccountId) {
        console.error('Failed to fetch alerts count', err);
      }
    }
  }, []);

  useEffect(() => {
    if (accountId) {
      fetchBrands();
    }
  }, [accountId, fetchBrands]);

  useEffect(() => {
    if (selectedBrand) {
      fetchAlertsCount(selectedBrand.id);
    } else {
      setUnreadAlertsCount(0);
    }
  }, [selectedBrand, fetchAlertsCount]);

  const handleLoadDemo = async () => {
    const requestAccountId = activeAccountRef.current;
    if (!requestAccountId) {
      return;
    }

    try {
      setLoading(true);
      await loadDemoEnvironment();
      if (activeAccountRef.current !== requestAccountId) {
        return;
      }
      await fetchBrands();
      // Reload fresh alerts
      if (
        activeAccountRef.current === requestAccountId
        && selectedBrand
      ) {
        await fetchAlertsCount(selectedBrand.id);
      }
    } catch (err) {
      console.error("Failed to load demo environment", err);
    } finally {
      if (activeAccountRef.current === requestAccountId) {
        setLoading(false);
      }
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
