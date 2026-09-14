/**
 * Detect the user's current city & region — works for semua wilayah.
 * 1) IP lookup (ipwho.is)  2) fallback ipapi.co  3) browser timezone (tanpa hardcode kota)
 * Dipanggil otomatis saat app load, jadi tiap rekan yang download langsung terisi kotanya.
 */
export async function detectUserLocation() {
  const tryParse = (data) => {
    const city = data.city || data.region || data.timezone || '';
    if (!city) return null;
    return {
      city: String(city).split('/').pop().replace(/_/g, ' '),
      region: data.region || data.regionName || data.timezone || '',
      country: data.country || data.country_name || 'Indonesia',
      ip: data.ip || data.query || undefined,
    };
  };

  // 1) ipwho.is — gratis, tanpa key
  try {
    const res = await fetch('https://ipwho.is/');
    if (res.ok) {
      const data = await res.json();
      if (data.success !== false && (data.city || data.region)) {
        const p = tryParse(data);
        if (p) return p;
      }
    }
  } catch (_) {}

  // 2) ipapi.co — fallback kedua (rate-limit longgar)
  try {
    const res = await fetch('https://ipapi.co/json/');
    if (res.ok) {
      const data = await res.json();
      if (!data.error && (data.city || data.region)) {
        const p = tryParse(data);
        if (p) return p;
      }
    }
  } catch (_) {}

  // 3) Browser timezone — tidak hardcode Banjarmasin/Jakarta, ambil apa adanya
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone; // e.g. Asia/Jakarta, Asia/Makassar
    if (tz && tz.includes('/')) {
      const cityFromTz = tz.split('/').pop().replace(/_/g, ' ');
      if (cityFromTz) return { city: cityFromTz, region: tz, country: 'Indonesia' };
    }
  } catch (_) {}

  return null;
}
