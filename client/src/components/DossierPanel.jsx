import React, { useState, useEffect } from 'react';
import { Copy, Check, Send, Inbox } from 'lucide-react';
import { generatePitch, updateLeadStatus } from '../services/api';

export default function DossierPanel({ activeLead, onStatusUpdated }) {
  const [channel, setChannel] = useState('wa');
  const [pitchText, setPitchText] = useState('');
  const [directLink, setDirectLink] = useState('');
  const [copied, setCopied] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (!activeLead) {
      setPitchText('');
      setDirectLink('');
      return;
    }
    let isMounted = true;
    setPitchText('');
    setDirectLink('');
    setIsGenerating(true);

    generatePitch(activeLead, channel)
      .then((res) => {
        if (isMounted) {
          setPitchText(res.text);
          setDirectLink(res.direct_link || '');
          setIsGenerating(false);
        }
      })
      .catch((err) => {
        console.error(err);
        if (isMounted) setIsGenerating(false);
      });

    return () => {
      isMounted = false;
    };
  }, [activeLead, channel]);

  if (!activeLead) {
    return (
      <div className="lg:col-span-5 p-8 flex flex-col items-center justify-center text-center text-[var(--muted-foreground)] font-mono text-xs space-y-2 min-h-[420px] bg-[var(--card)]">
        <div className="w-10 h-10 rounded-xl bg-[var(--sidebar)] border border-[var(--border)] flex items-center justify-center text-[var(--muted-foreground)]">
          <Inbox className="w-5 h-5" />
        </div>
        <div className="font-semibold text-[var(--foreground)] text-xs">Intelligence Dossier Kosong</div>
        <p className="max-w-xs text-[11px] text-[var(--muted-foreground)] leading-relaxed">
          Pilih salah satu target bisnis di tabel sebelah kiri untuk menganalisis masalah teknis dan melihat draf penawaran klien.
        </p>
      </div>
    );
  }

  const handleCopy = () => {
    if (!pitchText || isGenerating) return;
    navigator.clipboard.writeText(pitchText);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const handleCycleStatus = async () => {
    const states = ['Baru', 'Terkirim', 'Respon Positif', 'Deal'];
    const currentIdx = states.indexOf(activeLead.contact_status);
    const nextState = states[(currentIdx + 1) % states.length];
    try {
      await updateLeadStatus(activeLead.id, nextState);
      onStatusUpdated(activeLead.id, nextState);
    } catch (e) {
      console.error(e);
    }
  };

  const getUrgencyTag = (level) => {
    if (level === 'PRIORITAS TINGGI') {
      return (
        <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-medium bg-rose-500/10 text-rose-500 border border-rose-500/20">
          PRIORITAS TINGGI
        </span>
      );
    }
    if (level === 'POTENSIAL') {
      return (
        <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-medium bg-amber-500/10 text-amber-500 border border-amber-500/20">
          POTENSIAL
        </span>
      );
    }
    return (
      <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
        MENENGAH
      </span>
    );
  };

  return (
    <div className="lg:col-span-5 flex flex-col bg-[var(--card)]">
      {/* Dossier Header */}
      <div className="p-4 border-b border-[var(--border)] flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] uppercase tracking-wider text-[var(--muted-foreground)]">
              Target Dossier
            </span>
            {getUrgencyTag(activeLead.opportunity_level)}
          </div>
          <h3 className="font-bold text-base text-[var(--foreground)] mt-0.5 tracking-tight">
            {activeLead.name}
          </h3>
          <p className="text-xs text-[var(--muted-foreground)]">
            {activeLead.category} • {activeLead.location}
          </p>
        </div>
        <div className="text-right font-mono">
          <span className="text-[10px] text-[var(--muted-foreground)] block">Skor Peluang</span>
          <span className="text-sm font-bold text-emerald-500">
            {activeLead.opportunity_score} / 100
          </span>
        </div>
      </div>

      {/* Diagnostics List */}
      <div className="p-4 border-b border-[var(--border)] space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-mono uppercase text-[11px] text-[var(--muted-foreground)]">
            Hasil Verifikasi Sistem:
          </span>
          <span className="font-mono text-[11px] text-[var(--muted-foreground)]">
            ID: #{activeLead.id}
          </span>
        </div>

        <div className="space-y-2 text-xs">
          {activeLead.diagnostics.map((diag, idx) => {
            let dotColor = 'bg-rose-500';
            if (diag.status === 'warning') dotColor = 'bg-amber-500';
            if (diag.status === 'verified') dotColor = 'bg-emerald-500';

            return (
              <div
                key={idx}
                className="p-2.5 rounded-md bg-[var(--background)] border border-[var(--border)] flex items-start gap-2.5"
              >
                <span className={`w-1.5 h-1.5 rounded-full ${dotColor} mt-1.5 shrink-0`} />
                <div>
                  <div className="font-medium text-[var(--foreground)] text-[12px]">
                    {diag.label}
                  </div>
                  <div className="text-[11px] text-[var(--muted-foreground)] mt-0.5">
                    {diag.detail}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Recommended Solution Card */}
        <div className="p-3 rounded-lg bg-[var(--sidebar)] border border-[var(--border)] space-y-1 text-xs">
          <div className="text-[10px] font-mono uppercase text-[var(--muted-foreground)] tracking-wider">
            Rekomendasi Penawaran Developer:
          </div>
          <div className="font-semibold text-[var(--foreground)]">{activeLead.solution_text}</div>
          <div className="flex items-center justify-between pt-1 border-t border-[var(--border)] font-mono text-[11px] text-[var(--muted-foreground)]">
            <span>Benchmark Tarif:</span>
            <span className="text-emerald-500 font-semibold">
              {activeLead.est_min_val} — {activeLead.est_max_val}
            </span>
          </div>
        </div>
      </div>

      {/* Outreach Engine */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-[11px] uppercase tracking-wider text-[var(--muted-foreground)]">
                Draft Penawaran:
              </span>
              <span className="text-[10px] px-1.5 rounded bg-[var(--sidebar)] text-[var(--muted-foreground)] border border-[var(--border)] font-mono">
                Anti-Spam
              </span>
            </div>

            <div className="flex rounded-md p-0.5 bg-[var(--background)] border border-[var(--border)] text-[11px]">
              <button
                onClick={() => setChannel('wa')}
                className={`px-2 py-0.5 rounded font-medium transition ${
                  channel === 'wa'
                    ? 'bg-[var(--card)] text-[var(--foreground)] shadow-xs'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                WhatsApp
              </button>
              <button
                onClick={() => setChannel('email')}
                className={`px-2 py-0.5 rounded font-medium transition ${
                  channel === 'email'
                    ? 'bg-[var(--card)] text-[var(--foreground)] shadow-xs'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                Email
              </button>
              <button
                onClick={() => setChannel('dm')}
                className={`px-2 py-0.5 rounded font-medium transition ${
                  channel === 'dm'
                    ? 'bg-[var(--card)] text-[var(--foreground)] shadow-xs'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                Instagram
              </button>
            </div>
          </div>

          <div className="relative group">
            <textarea
              rows={6}
              readOnly
              value={isGenerating ? 'Menghasilkan draf personalisasi...' : pitchText}
              className="w-full p-3 bg-[var(--background)] border border-[var(--border)] rounded-lg text-xs leading-relaxed text-[var(--foreground)] font-mono focus:outline-none resize-none"
            />
            <button
              onClick={handleCopy}
              disabled={!pitchText || isGenerating}
              className="absolute top-2.5 right-2.5 px-2 py-1 rounded bg-[var(--card)] hover:bg-[var(--sidebar)] border border-[var(--border)] text-[11px] text-[var(--foreground)] font-medium flex items-center gap-1 shadow-xs transition active:scale-95 disabled:opacity-50"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3 text-[var(--muted-foreground)]" />}
              <span>{copied ? 'Tersalin ✓' : 'Salin Draf'}</span>
            </button>
          </div>
        </div>

        {/* Action CTAs */}
        <div className="flex items-center gap-2 pt-2">
          {directLink && !isGenerating ? (
            <a
              href={directLink}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 py-2 px-3 rounded-lg bg-[var(--foreground)] text-[var(--background)] hover:opacity-90 font-medium text-xs transition flex items-center justify-center gap-2 shadow-sm text-center"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Kirim via WhatsApp Langsung</span>
            </a>
          ) : (
            <button
              onClick={handleCopy}
              disabled={!pitchText || isGenerating}
              className="flex-1 py-2 px-3 rounded-lg bg-[var(--foreground)] text-[var(--background)] hover:opacity-90 font-medium text-xs transition flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>Salin Teks untuk Dikirim</span>
            </button>
          )}

          <button
            onClick={handleCycleStatus}
            className="px-3 py-2 rounded-lg bg-[var(--background)] hover:bg-[var(--sidebar)] border border-[var(--border)] text-xs text-[var(--foreground)] font-mono transition whitespace-nowrap"
          >
            Status: {activeLead.contact_status}
          </button>
        </div>
      </div>
    </div>
  );
}
