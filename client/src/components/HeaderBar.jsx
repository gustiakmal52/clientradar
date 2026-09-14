import React from 'react';
import { Download, Sparkles, Sliders, Globe } from 'lucide-react';
import { getExportCsvUrl } from '../services/api';

export default function HeaderBar({ onOpenSettings, onOpenUrlAudit, totalLeads, activeSource }) {
  return (
    <header className="px-4 py-3 border-b border-[var(--border)] flex flex-wrap items-center justify-between gap-3 bg-[var(--card)]">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[var(--foreground)] text-[var(--background)] flex items-center justify-center font-mono font-bold text-xs tracking-tighter shadow-sm">
          CR
        </div>
        <div className="flex items-center gap-2">
          <span className="font-semibold tracking-tight text-sm text-[var(--foreground)]">ClientRadar</span>
          <span className="text-[var(--border)]">/</span>
          <span className="font-mono text-xs text-[var(--muted-foreground)]">v1.2.0</span>
          
          {/* Author Badge */}
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <span className="w-1 h-1 rounded-full bg-blue-400"></span> Author: Gustiakmal
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 font-mono text-xs">
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[var(--background)] border border-[var(--border)] text-[var(--muted-foreground)]">
          <span>PIPELINE:</span>
          <span className="font-semibold text-[var(--foreground)]">{totalLeads} Target</span>
        </div>

        {/* Custom Source Status Button */}
        <button
          onClick={onOpenSettings}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs transition ${
            activeSource?.active
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-[var(--background)] hover:bg-[var(--sidebar)] border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
          }`}
          title="Konfigurasi Alamat Aplikasi Target"
        >
          <Sliders className="w-3.5 h-3.5" />
          <span className="hidden md:inline">{activeSource?.active ? 'Target: Custom App' : 'Sumber: Default'}</span>
        </button>

        {/* Live URL Audit */}
        <button
          onClick={onOpenUrlAudit}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[var(--background)] hover:bg-[var(--sidebar)] border border-[var(--border)] text-[var(--foreground)] transition active:scale-95"
          title="Audit Live URL Klien Tertentu"
        >
          <Globe className="w-3.5 h-3.5 text-blue-400" />
          <span className="hidden md:inline">Audit URL Langsung</span>
        </button>

        {/* CSV Export */}
        <a
          href={getExportCsvUrl()}
          download="clientradar_leads.csv"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[var(--background)] hover:bg-[var(--sidebar)] border border-[var(--border)] text-[var(--foreground)] transition active:scale-95"
        >
          <Download className="w-3.5 h-3.5 text-[var(--muted-foreground)]" />
          <span>Export</span>
        </a>
      </div>
    </header>
  );
}
