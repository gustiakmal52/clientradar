import React from 'react';
import { Search } from 'lucide-react';

export default function LeadsTable({
  leads,
  activeLead,
  onSelectLead,
  onQuickFilter,
  totalCount
}) {
  const getProblemBadge = (type) => {
    switch (type) {
      case 'missing_web':
        return (
          <span className="inline-flex items-center gap-1 font-mono text-[10px] text-rose-500">
            <span className="w-1 h-1 rounded-full bg-rose-500"></span> Belum Ada Web
          </span>
        );
      case 'unresponsive_mobile':
        return (
          <span className="inline-flex items-center gap-1 font-mono text-[10px] text-amber-500">
            <span className="w-1 h-1 rounded-full bg-amber-500"></span> Mobile Rusak / Lelet
          </span>
        );
      case 'no_booking_flow':
        return (
          <span className="inline-flex items-center gap-1 font-mono text-[10px] text-indigo-400">
            <span className="w-1 h-1 rounded-full bg-indigo-400"></span> Tanpa Booking Flow
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 font-mono text-[10px] text-zinc-400">
            <span className="w-1 h-1 rounded-full bg-zinc-400"></span> Subdomain / Stack Jadul
          </span>
        );
    }
  };

  const getStatusColor = (status) => {
    if (status === 'Terkirim') return 'text-amber-500';
    if (status === 'Respon Positif' || status === 'Deal') return 'text-emerald-500';
    return 'text-[var(--muted-foreground)]';
  };

  return (
    <div className="lg:col-span-7 flex flex-col justify-between">
      {/* Table Headers */}
      <div>
        <div className="px-4 py-2.5 bg-[var(--sidebar)]/30 border-b border-[var(--border)] flex items-center justify-between text-[11px] font-mono text-[var(--muted-foreground)] uppercase tracking-wider">
          <div className="w-5/12">Bisnis & Profil</div>
          <div className="w-4/12">Diagnosis Digital</div>
          <div className="w-3/12 text-right">Potensi Deal</div>
        </div>

        {/* Rows */}
        <div className="divide-y divide-[var(--border)] max-h-[560px] overflow-y-auto min-h-[380px] flex flex-col justify-center">
          {leads.length === 0 ? (
            <div className="p-8 text-center text-[var(--muted-foreground)] font-mono text-xs flex flex-col items-center justify-center space-y-2">
              <div className="w-9 h-9 rounded-lg bg-[var(--sidebar)] border border-[var(--border)] flex items-center justify-center text-[var(--muted-foreground)]">
                <Search className="w-4 h-4" />
              </div>
              <div className="font-semibold text-[var(--foreground)] text-xs">Belum Ada Target Prospek</div>
              <p className="max-w-xs text-[11px] text-[var(--muted-foreground)] leading-relaxed">
                Ketik target pencarian di atas atau hubungkan endpoint aplikasi Anda melalui tombol pengaturan di kanan atas.
              </p>
            </div>
          ) : (
            leads.map((lead) => {
              const isSelected = activeLead && activeLead.id === lead.id;
              const activeClass = isSelected
                ? 'bg-[var(--sidebar)] border-l-2 border-l-[var(--foreground)]'
                : 'hover:bg-[var(--sidebar)]/40';

              return (
                <div
                  key={lead.id}
                  onClick={() => onSelectLead(lead)}
                  className={`px-4 py-3 flex items-center justify-between cursor-pointer transition ${activeClass}`}
                >
                  {/* Left: Business Info */}
                  <div className="w-5/12 pr-2">
                    <div className="font-semibold text-[var(--foreground)] tracking-tight text-xs truncate">
                      {lead.name}
                    </div>
                    <div className="text-[11px] text-[var(--muted-foreground)] flex items-center gap-1.5 mt-0.5">
                      <span>★ {lead.rating}</span>
                      <span>•</span>
                      <span className="truncate">{lead.location}</span>
                    </div>
                  </div>

                  {/* Middle: Diagnostics Tag */}
                  <div className="w-4/12 pr-2">
                    <div>{getProblemBadge(lead.problem_type)}</div>
                    <div className={`text-[10px] font-mono mt-0.5 ${getStatusColor(lead.contact_status)}`}>
                      • {lead.contact_status}
                    </div>
                  </div>

                  {/* Right: Est Value */}
                  <div className="w-3/12 text-right font-mono">
                    <span className="text-xs font-semibold text-[var(--foreground)]">{lead.est_min_val}</span>
                    <span className="block text-[10px] text-[var(--muted-foreground)]">
                      {lead.opportunity_score}% fit
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Table Footer */}
      <div className="p-3 bg-[var(--sidebar)]/20 border-t border-[var(--border)] flex items-center justify-between text-xs text-[var(--muted-foreground)]">
        <div className="flex items-center gap-1 font-mono text-[11px]">
          <span>Total Prospek:</span>
          <span className="text-[var(--foreground)] font-semibold">{leads.length}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px]">
          <span className="text-[var(--muted-foreground)]">Filter Cepat:</span>
          <button
            onClick={() => onQuickFilter('missing_web')}
            className="px-2 py-0.5 rounded bg-[var(--background)] hover:bg-[var(--sidebar)] border border-[var(--border)] text-[var(--foreground)] font-mono text-[10px] transition"
          >
            #NoWeb
          </button>
          <button
            onClick={() => onQuickFilter('unresponsive_mobile')}
            className="px-2 py-0.5 rounded bg-[var(--background)] hover:bg-[var(--sidebar)] border border-[var(--border)] text-[var(--foreground)] font-mono text-[10px] transition"
          >
            #MobileBroken
          </button>
          <button
            onClick={() => onQuickFilter('all')}
            className="px-2 py-0.5 rounded bg-[var(--background)] hover:bg-[var(--sidebar)] border border-[var(--border)] text-[var(--muted-foreground)] font-mono text-[10px] transition"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}
