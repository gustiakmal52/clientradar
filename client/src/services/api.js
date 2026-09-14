const API_BASE = import.meta.env.VITE_API_URL || '/api';

export async function fetchLeads(problemFilter = 'all') {
  const url = `${API_BASE}/leads?problem_type=${problemFilter}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Gagal mengambil data leads');
  return res.json();
}

export async function scanLeads(keyword, location = '', problemFilter = 'all') {
  const res = await fetch(`${API_BASE}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      keyword,
      location,
      problem_filter: problemFilter
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gagal menjalankan scan');
  }
  const data = await res.json();
  // API baru: { leads: [], hint: "..." } ; lama: []
  if (Array.isArray(data)) return { leads: data, hint: null };
  return { leads: data.leads || [], hint: data.hint || null, meta: data.meta || null };
}

export async function auditLiveUrl(url) {
  const res = await fetch(`${API_BASE}/audit-url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  if (!res.ok) throw new Error('Gagal mengaudit URL');
  return res.json();
}

export async function generatePitch(lead, channel = 'wa') {
  const res = await fetch(`${API_BASE}/generate-pitch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lead, channel })
  });
  if (!res.ok) throw new Error('Gagal membuat draf pitch');
  return res.json();
}

export async function updateLeadStatus(leadId, status) {
  const res = await fetch(`${API_BASE}/leads/${leadId}/status?status=${encodeURIComponent(status)}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Gagal memperbarui status lead');
  return res.json();
}

export async function getSourceConfig() {
  const res = await fetch(`${API_BASE}/config/source`);
  if (!res.ok) throw new Error('Gagal mengambil konfigurasi adapter');
  return res.json();
}

export async function saveSourceConfig(config) {
  const res = await fetch(`${API_BASE}/config/source`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  if (!res.ok) throw new Error('Gagal menyimpan konfigurasi adapter');
  return res.json();
}

export function getExportCsvUrl() {
  return `${API_BASE}/export`;
}
