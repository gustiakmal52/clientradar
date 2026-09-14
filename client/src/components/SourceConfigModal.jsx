import React, { useState } from 'react';
import { X, Check, Globe, HelpCircle } from 'lucide-react';
import { saveSourceConfig } from '../services/api';

export default function SourceConfigModal({ isOpen, onClose, currentConfig, onConfigSaved }) {
  if (!isOpen) return null;

  const [endpointUrl, setEndpointUrl] = useState(currentConfig?.app_endpoint_url || '');
  const [apiKey, setApiKey] = useState(currentConfig?.api_key || '');
  const [active, setActive] = useState(currentConfig?.active || false);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const updated = await saveSourceConfig({
        app_endpoint_url: endpointUrl,
        api_key: apiKey,
        active: active && Boolean(endpointUrl)
      });
      onConfigSaved(updated);
      onClose();
    } catch (err) {
      alert(`Gagal menyimpan konfigurasi: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl w-full max-w-lg shadow-2xl overflow-hidden font-sans">
        <div className="px-5 py-4 border-b border-[var(--border)] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-blue-400" />
            <h3 className="font-semibold text-sm text-[var(--foreground)]">Konfigurasi Alamat Aplikasi Target</h3>
          </div>
          <button
            onClick={onClose}
            className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] p-1 rounded-md transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-5 space-y-4 text-xs">
          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 leading-relaxed">
            <p className="font-semibold mb-1 flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5" />
              Konektor Sumber Data Kustom
            </p>
            Masukkan URL atau endpoint aplikasi target yang Anda miliki. Sistem ClientRadar akan secara otomatis mengirim query pencarian ke alamat ini dan mengonversinya menjadi daftar prospek terverifikasi.
          </div>

          <div>
            <label className="block text-[var(--foreground)] font-medium mb-1 font-mono">
              Alamat Endpoint Aplikasi (URL / API)
            </label>
            <input
              type="text"
              value={endpointUrl}
              onChange={(e) => setEndpointUrl(e.target.value)}
              placeholder="https://aplikasi-anda.com/api/scrape-leads atau http://localhost:3000"
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg text-xs text-[var(--foreground)] font-mono focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          <div>
            <label className="block text-[var(--foreground)] font-medium mb-1 font-mono">
              API Token / Key (Opsional)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Bearer token jika aplikasi Anda membutuhkan autentikasi..."
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg text-xs text-[var(--foreground)] font-mono focus:outline-none focus:border-blue-500 transition"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="chkActive"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
              className="rounded bg-[var(--background)] border-[var(--border)] text-blue-600 focus:ring-0"
            />
            <label htmlFor="chkActive" className="text-[var(--foreground)] font-medium cursor-pointer">
              Aktifkan konektor aplikasi kustom ini sebagai sumber prioritas
            </label>
          </div>

          <div className="pt-3 border-t border-[var(--border)] flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg bg-[var(--background)] hover:bg-[var(--sidebar)] border border-[var(--border)] text-[var(--foreground)] transition"
            >
              Batal
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-1.5 rounded-lg bg-[var(--foreground)] text-[var(--background)] font-medium transition hover:opacity-90 active:scale-95 disabled:opacity-50"
            >
              {isSaving ? 'Menyimpan...' : 'Simpan Alamat'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
