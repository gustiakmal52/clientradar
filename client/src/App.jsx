import React, { useState, useEffect } from 'react';
import HeaderBar from './components/HeaderBar';
import SearchBar from './components/SearchBar';
import TelemetryBar from './components/TelemetryBar';
import LeadsTable from './components/LeadsTable';
import DossierPanel from './components/DossierPanel';
import SourceConfigModal from './components/SourceConfigModal';
import LiveUrlAuditModal from './components/LiveUrlAuditModal';
import { fetchLeads, scanLeads, getSourceConfig } from './services/api';
import { detectUserLocation } from './services/location';

export default function App() {
  const [leads, setLeads] = useState([]);
  const [activeLead, setActiveLead] = useState(null);
  const [keyword, setKeyword] = useState('');
  const [location, setLocation] = useState('');
  const [detectedCity, setDetectedCity] = useState('');
  const [filter, setFilter] = useState('all');
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [telemetryText, setTelemetryText] = useState('');
  
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isUrlAuditOpen, setIsUrlAuditOpen] = useState(false);
  const [sourceConfig, setSourceConfig] = useState(null);

  // Auto-detect user's city when app loads (Banjarmasin, Jakarta, Surabaya, etc.)
  const handleDetectLocation = () => {
    detectUserLocation()
      .then((geo) => {
        if (geo && geo.city) {
          setDetectedCity(geo.city);
          setLocation(geo.city);
        }
      })
      .catch((e) => console.warn('Could not auto-detect location', e));
  };

  useEffect(() => {
    handleDetectLocation();

    fetchLeads('all')
      .then((data) => {
        setLeads(data || []);
        if (data && data.length > 0) setActiveLead(data[0]);
      })
      .catch((err) => console.error(err));

    getSourceConfig()
      .then((cfg) => setSourceConfig(cfg))
      .catch((err) => console.error(err));
  }, []);

  // Filter effect
  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    fetchLeads(newFilter)
      .then((data) => {
        setLeads(data || []);
        if (data && data.length > 0) {
          setActiveLead(data[0]);
        } else {
          setActiveLead(null);
        }
      })
      .catch((err) => console.error(err));
  };

  // Run live scan
  const handleExecuteScan = async () => {
    if (!keyword.trim() && !sourceConfig?.active) {
      alert('Silakan ketik target bisnis (misal: "Klinik Gigi" atau "Restoran") atau aktifkan sumber aplikasi kustom Anda.');
      return;
    }

    const effectiveQuery = location.trim() ? `${keyword} di ${location}` : keyword;

    setIsScanning(true);
    setScanProgress(15);
    setTelemetryText(`Memindai target: '${effectiveQuery}'...`);

    const progressTimer = setInterval(() => {
      setScanProgress((prev) => {
        if (prev >= 85) return prev;
        return prev + 15;
      });
    }, 200);

    try {
      setTelemetryText('Memverifikasi responsivitas, SSL, dan mengekstraksi prospek...');
      const results = await scanLeads(keyword, location, filter);
      clearInterval(progressTimer);
      setScanProgress(100);
      setTelemetryText('Selesai. Daftar target prospek berhasil diperbarui.');

      setTimeout(() => {
        setLeads(results || []);
        if (results && results.length > 0) {
          setActiveLead(results[0]);
        } else {
          setActiveLead(null);
        }
        setIsScanning(false);
      }, 400);
    } catch (err) {
      clearInterval(progressTimer);
      setIsScanning(false);
      alert(`Gagal memindai: ${err.message}`);
    }
  };

  const handleStatusUpdated = (leadId, newStatus) => {
    setLeads((prev) =>
      prev.map((l) => (l.id === leadId ? { ...l, contact_status: newStatus } : l))
    );
    if (activeLead && activeLead.id === leadId) {
      setActiveLead((prev) => ({ ...prev, contact_status: newStatus }));
    }
  };

  return (
    <div className="min-h-screen bg-transparent text-[var(--foreground)] p-2 sm:p-4 flex flex-col justify-between">
      {/* Elevated Glass Container */}
      <div className="bg-[var(--card)]/90 backdrop-blur-md border border-[var(--border)] rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all">
        {/* Header with Author Gustiakmal */}
        <HeaderBar
          onOpenSettings={() => setIsSettingsOpen(true)}
          onOpenUrlAudit={() => setIsUrlAuditOpen(true)}
          totalLeads={leads.length}
          activeSource={sourceConfig}
        />

        {/* Omnisearch & Filter Bar with Auto-detected City */}
        <SearchBar
          keyword={keyword}
          setKeyword={setKeyword}
          location={location}
          setLocation={setLocation}
          detectedCity={detectedCity}
          filter={filter}
          setFilter={handleFilterChange}
          onExecuteScan={handleExecuteScan}
          isScanning={isScanning}
          onRefreshLocation={handleDetectLocation}
        />

        {/* Telemetry Progress Bar */}
        <TelemetryBar
          isScanning={isScanning}
          progress={scanProgress}
          statusText={telemetryText}
        />

        {/* Split View */}
        <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[var(--border)] min-h-[500px]">
          <LeadsTable
            leads={leads}
            activeLead={activeLead}
            onSelectLead={setActiveLead}
            onQuickFilter={handleFilterChange}
            totalCount={leads.length}
          />
          <DossierPanel
            activeLead={activeLead}
            onStatusUpdated={handleStatusUpdated}
          />
        </div>
      </div>

      {/* Footer Branding */}
      <footer className="mt-3 px-2 py-1 text-center font-mono text-[11px] text-[var(--muted-foreground)] flex items-center justify-between">
        <span>ClientRadar Engine • Built for Freelancers & Software Agencies</span>
        <span className="text-[var(--foreground)] font-medium">Author: Gustiakmal</span>
      </footer>

      {/* Modals */}
      <SourceConfigModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        currentConfig={sourceConfig}
        onConfigSaved={(updated) => setSourceConfig(updated)}
      />

      <LiveUrlAuditModal
        isOpen={isUrlAuditOpen}
        onClose={() => setIsUrlAuditOpen(false)}
      />
    </div>
  );
}
