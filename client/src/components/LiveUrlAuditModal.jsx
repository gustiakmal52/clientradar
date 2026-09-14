import React, { useState } from 'react';
import { X, Search, Globe, Shield, Smartphone, Gauge, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { auditLiveUrl } from '../services/api';

export default function LiveUrlAuditModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAudit = async (e) => {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await auditLiveUrl(url);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Gagal memeriksa website.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl w-full max-w-xl shadow-2xl overflow-hidden font-sans max-h-[90vh] flex flex-col">
        <div className="px-5 py-4 border-b border-[var(--border)] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-blue-400" />
            <h3 className="font-semibold text-sm text-[var(--foreground)]">Audit Website Klien Secara Langsung</h3>
          </div>
          <button
            onClick={onClose}
            className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] p-1 rounded-md transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-4 text-xs">
          <form onSubmit={handleAudit} className="flex gap-2">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Masukkan website calon klien (cth: example.com atau http://klinik.id)..."
              className="flex-1 px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg text-xs text-[var(--foreground)] font-mono focus:outline-none focus:border-blue-500 transition"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-[var(--foreground)] text-[var(--background)] rounded-lg font-medium transition hover:opacity-90 active:scale-95 disabled:opacity-50 flex items-center gap-1.5"
            >
              <Search className="w-3.5 h-3.5" />
              <span>{loading ? 'Menguji...' : 'Audit'}</span>
            </button>
          </form>

          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
              {error}
            </div>
          )}

          {result && (
            <div className="space-y-3 pt-2">
              {/* Score Header */}
              <div className="p-4 rounded-xl bg-[var(--sidebar)] border border-[var(--border)] flex items-center justify-between">
                <div>
                  <div className="font-mono text-[10px] text-[var(--muted-foreground)] uppercase">Skor Kesehatan Web</div>
                  <div className="text-xl font-bold text-[var(--foreground)] mt-0.5">{result.url}</div>
                  <div className="flex items-center gap-2 mt-1 text-[11px] text-[var(--muted-foreground)]">
                    <span>HTTP: {result.status_code || 200}</span>
                    <span>•</span>
                    <span>Latensi: {result.response_time_ms} ms</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-black font-mono ${
                    result.overall_score >= 80 ? 'text-emerald-500' : result.overall_score >= 50 ? 'text-amber-500' : 'text-rose-500'
                  }`}>
                    {result.overall_score} / 100
                  </div>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">
                    {result.overall_score < 60 ? 'Peluang Proyek Tinggi' : 'Kondisi Cukup Baik'}
                  </span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)] flex items-center gap-2.5">
                  <Shield className={`w-4 h-4 ${result.is_ssl ? 'text-emerald-500' : 'text-rose-500'}`} />
                  <div>
                    <div className="font-medium text-[var(--foreground)]">SSL / Keamanan</div>
                    <div className="text-[11px] text-[var(--muted-foreground)]">
                      {result.is_ssl ? 'HTTPS Aman' : 'Tidak Aman (HTTP)'}
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)] flex items-center gap-2.5">
                  <Smartphone className={`w-4 h-4 ${result.has_mobile_viewport ? 'text-emerald-500' : 'text-rose-500'}`} />
                  <div>
                    <div className="font-medium text-[var(--foreground)]">Mobile Viewport</div>
                    <div className="text-[11px] text-[var(--muted-foreground)]">
                      {result.has_mobile_viewport ? 'Mobile Responsive' : 'Tampilan HP Rusak'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Tech detected */}
              {result.detected_tech.length > 0 && (
                <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
                  <div className="font-mono text-[10px] text-[var(--muted-foreground)] uppercase mb-1.5">Teknologi Terdeteksi:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {result.detected_tech.map((t, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-[var(--sidebar)] text-[var(--foreground)] border border-[var(--border)] text-[11px] font-mono">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Issues detected */}
              <div className="space-y-1.5">
                <div className="font-mono text-[10px] text-[var(--muted-foreground)] uppercase">Kelemahan yang Ditemukan (Bahan Pitch):</div>
                {result.issues.map((iss, i) => (
                  <div key={i} className="p-2 rounded bg-[var(--background)] border border-[var(--border)] flex items-start gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" />
                    <div>
                      <div className="font-medium text-[var(--foreground)] text-[11px]">{iss.label}</div>
                      <div className="text-[10px] text-[var(--muted-foreground)]">{iss.detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
