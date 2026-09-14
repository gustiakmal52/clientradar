import React from 'react';
import { Search, Zap, MapPin, RefreshCw } from 'lucide-react';

export default function SearchBar({
  keyword,
  setKeyword,
  location,
  setLocation,
  detectedCity,
  filter,
  setFilter,
  onExecuteScan,
  isScanning,
  onRefreshLocation
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onExecuteScan();
  };

  return (
    <section className="px-4 py-3 bg-[var(--sidebar)]/50 border-b border-[var(--border)]">
      <form onSubmit={handleSubmit} className="flex flex-col lg:flex-row gap-2.5 items-stretch lg:items-center">
        {/* Business Category / Target Input */}
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[var(--muted-foreground)]">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Target bisnis (cth: 'Klinik Gigi', 'Boutique Hotel', 'Cafe Roastery')..."
            className="w-full pl-9 pr-4 py-1.5 bg-[var(--background)] border border-[var(--border)] rounded-lg text-xs text-[var(--foreground)] placeholder-[var(--placeholder)] focus:outline-none focus:border-[var(--foreground)]/40 transition font-mono"
          />
        </div>

        {/* Dynamic Auto-Detected City Input */}
        <div className="w-full lg:w-60 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-blue-400">
            <MapPin className="w-3.5 h-3.5" />
          </div>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Kota target..."
            title="Lokasi ini otomatis mendeteksi kota Anda (misal Banjarmasin/Jakarta)"
            className="w-full pl-8 pr-8 py-1.5 bg-[var(--background)] border border-[var(--border)] rounded-lg text-xs text-[var(--foreground)] font-mono focus:outline-none focus:border-[var(--foreground)]/40 transition"
          />
          <button
            type="button"
            onClick={onRefreshLocation}
            title="Deteksi ulang kota saat ini"
            className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-[var(--muted-foreground)] hover:text-blue-400 transition"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>

        {/* Problem Filter */}
        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="py-1.5 px-3 bg-[var(--background)] border border-[var(--border)] rounded-lg text-xs text-[var(--foreground)] focus:outline-none focus:border-[var(--foreground)]/40 transition"
          >
            <option value="all">Semua Masalah Web</option>
            <option value="missing_web">🚫 Belum Ada Web</option>
            <option value="unresponsive_mobile">📱 Mobile Rusak / Lelet</option>
            <option value="no_booking_flow">💬 Tanpa Booking Flow</option>
            <option value="outdated_tech">⚠️ Stack Usang / Subdomain</option>
          </select>

          {/* Scan Button */}
          <button
            type="submit"
            disabled={isScanning}
            className="px-3.5 py-1.5 bg-[var(--foreground)] hover:opacity-90 text-[var(--background)] rounded-lg font-medium text-xs flex items-center gap-2 transition active:scale-95 whitespace-nowrap shadow-sm disabled:opacity-50"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>{isScanning ? 'Memindai...' : 'Jalankan Radar'}</span>
          </button>
        </div>
      </form>

      {/* Auto-detected City Badge Notification */}
      {detectedCity && (
        <div className="mt-2 flex items-center gap-1.5 text-[11px] font-mono text-[var(--muted-foreground)]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          <span>Lokasi Anda terdeteksi otomatis:</span>
          <button
            type="button"
            onClick={() => setLocation(detectedCity)}
            className="text-emerald-400 font-semibold hover:underline cursor-pointer"
          >
            {detectedCity}
          </button>
          <span className="text-[10px] text-[var(--muted-foreground)]">(Klik untuk terapkan / ganti bebas)</span>
        </div>
      )}
    </section>
  );
}
