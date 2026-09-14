import React from 'react';

export default function TelemetryBar({ isScanning, progress, statusText }) {
  if (!isScanning) return null;

  return (
    <div className="px-4 py-2 bg-blue-500/5 border-b border-blue-500/20 text-xs flex items-center justify-between transition-all">
      <div className="flex items-center gap-2 text-blue-400 font-mono text-[11px]">
        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span>
        <span>{statusText || 'Menghubungi endpoint target & memverifikasi metadata bisnis...'}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-32 bg-[var(--background)] h-1 rounded-full overflow-hidden border border-[var(--border)]">
          <div
            className="bg-blue-500 h-full rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="font-mono text-[10px] text-blue-400">{progress}%</span>
      </div>
    </div>
  );
}
