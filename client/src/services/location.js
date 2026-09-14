/**
 * Auto-detect user's current city & region using client IP lookup.
 * Automatically adapts whether the user is in Banjarmasin, Jakarta, Surabaya, etc.
 */
export async function detectUserLocation() {
  try {
    const res = await fetch('https://ipwho.is/');
    if (!res.ok) throw new Error('Failed to fetch IP location');
    const data = await res.json();
    if (data.success) {
      return {
        city: data.city || 'Indonesia',
        region: data.region || '',
        country: data.country || 'Indonesia',
        ip: data.ip
      };
    }
  } catch (err) {
    console.warn('[Location Detection Warning]: Fallback to timezone inference', err);
  }

  // Smart fallback based on browser Timezone if offline/blocked
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (tz.includes('Makassar') || tz.includes('Banjarmasin')) {
      return { city: 'Banjarmasin', region: 'Kalimantan Selatan', country: 'Indonesia' };
    }
    if (tz.includes('Jakarta')) {
      return { city: 'Jakarta', region: 'DKI Jakarta', country: 'Indonesia' };
    }
    if (tz.includes('Jayapura')) {
      return { city: 'Jayapura', region: 'Papua', country: 'Indonesia' };
    }
  } catch (e) {
    // Ignore
  }

  return { city: 'Banjarmasin', region: 'Indonesia', country: 'Indonesia' };
}
