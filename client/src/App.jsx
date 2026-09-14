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
  const [scanHint, setScanHint] = useState(null);
  
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isUrlAuditOpen, setIsUrlAuditOpen] = useState(false);
  const [sourceConfig, setSourceConfig] = useState(null);

  // Auto-detect on first load — tiap rekan yang git clone langsung keisi kotanya (semua wilayah).
  const handleDetectLocation = () => {
    detectUserLocation()
      .then((geo) => {
        if (geo && geo.city) {
          setDetectedCity(geo.city);
          // Jangan timpa kalau user sudah mengetik manual
          setLocation((prev) => (prev.trim() ? prev : geo.city));
        }
      })
      .catch((e) => console.warn('Could not auto-detect location', e));
  };

  useEffect(() => {
    handleDetectLocation();
  }, []);

  // Dibuka kosong — tanpa template/demo. User isi lokasi + keyword sendiri (seluruh Indonesia via OSM).
  useEffect(() => {
    setLeads([]);
    setActiveLead(null);
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

  // Run live scan — wajib lokasi (seluruh Indonesia). Tanpa lokasi -> minta isi dulu.
  const handleExecuteScan = async () => {
    if (!location.trim()) {
      alert('Isi lokasi dulu (misal: Makassar, Jakarta, Bandung, Surabaya, Medan, dll). Seluruh Indonesia didukung.');
      return;
    }
    const kwTrim = keyword.trim();
    const effectiveQuery = kwTrim ? `${kwTrim} di ${location}` : `semua prospek di ${location}`;

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
      setScanHint(null);
      setTelemetryText('Memverifikasi responsivitas, SSL, dan mengekstraksi prospek...');
      const { leads: results, hint, meta } = await scanLeads(keyword, location, filter);
      clearInterval(progressTimer);
      setScanProgress(100);
      if (hint) {
        setTelemetryText(hint);
      } else if (results && results.length > 0) {
        setTelemetryText(`Selesai — ${results.length} prospek ditemukan di ${location}.`);
      } else {
        const detail = meta?.detail || '';
        setTelemetryText(detail ? `Tidak ada hasil. ${detail.slice(0,120)}` : `Tidak ada hasil di ${location} untuk "${kwTrim || 'browse'}". Coba kata: cafe, resto, hotel, klinik atau ganti kota.`);
      }

      if (hint) setScanHint(hint);

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
      setTelemetryText(`Gagal: ${err.message}`);
      setScanHint(err.message);
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
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)] p-2 sm:p-4 flex flex-col justify-between">
      {/* Elevated Container - solid, no blur */}
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all">
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

        {/* Scan hint — untuk provinsi luas seperti Papua yang pusatnya di hutan -> kasih tau pakai kota */}
        {scanHint && !isScanning && (
          <div className="px-4 py-2.5 bg-amber-500/10 border-y border-amber-500/20 text-[11px] text-amber-300 font-mono leading-relaxed flex items-start gap-2">
            <span className="mt-0.5">⚠️</span>
            <span>{scanHint}</span>
            <button onClick={() => setScanHint(null)} className="ml-auto text-amber-400 hover:text-amber-200 shrink-0">✕</button>
          </div>
        )}

        {/* Split View */}
        <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[var(--border)] min-h-[500px]">
          <LeadsTable
            leads={leads}
            activeLead={activeLead}
            onSelectLead={setActiveLead}
            onQuickFilter={handleFilterChange}
            totalCount={leads.length}
            scanHint={scanHint}
            currentLocation={location}
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
      {isSettingsOpen && (
        <SourceConfigModal
          onClose={() => setIsSettingsOpen(false)}
          currentConfig={sourceConfig}
          onConfigSaved={(updated) => setSourceConfig(updated)}
        />
      )}

      {isUrlAuditOpen && (
        <LiveUrlAuditModal onClose={() => setIsUrlAuditOpen(false)} />
      )}
    </div>
  );
}
