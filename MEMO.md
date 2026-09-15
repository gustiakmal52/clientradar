# MEMO — ClientRadar v1.3.0

**Tanggal:** 2026-09-15
**Author:** Gustiakmal

## Ringkasan
Fix seluruh Indonesia + auto-detect lokasi backend. Medan, provinsi, dan scan nasional sekarang berfungsi.

## Security Hardening (audit red team, 2026-09-15)

Temuan audit + perbaikan yang sudah diverifikasi live:

| Temuan | Severity | Fix | Verifikasi |
|---|---|---|---|
| SSRF `/api/audit-url` (fetch internal/cloud metadata) | P2 | SSRF guard `security.py` — blokir loopback/private/link-local + validasi tiap hop redirect + size cap 2MB | `http://127.0.0.1:8000` → "Target Tidak Diizinkan" |
| SSRF via custom source endpoint | P2 | `validate_ssrf_url()` di `custom.py` | endpoint localhost → 502 "Endpoint tidak diizinkan" |
| CORS wildcard `*` | P2 | Allowlist `localhost:5173` + `127.0.0.1:5173` | evil origin → tanpa ACAO; localhost → ACAO ada |
| Config tampering tanpa auth | P2 | Dimitigasi via CORS allowlist + rate limit (5/60s) | — |
| CSV formula injection (CWE-1236) | P3 | `_csv_safe()` prefix `'` untuk sel `=+-@` | unit test + PoC |
| No rate limiting (API4:2023) | P3 | `RateLimiter` in-memory: scan 3/60s, audit 10/60s, config 5/60s, status 20/60s | 11x audit cepat → 429 |
| Rating/ulasan palsu (md5 hash) | Integritas | Diagnostic "estimasi internal" + pitch tidak lagi klaim "Rating X★ Google Maps" | — |
| Info leak exception detail | Low | Error audit digenerikkan | — |
| Overpass QL injection surface | Low | `_sanitize_osm_keyword()` strip `"`/`\` + limit 40 char | unit test |
| Version mismatch 1.2.0 vs 1.3.0 | Low | `main.py` version → 1.3.0 | openapi.json |

File baru: `server/app/services/security.py` (SSRF guard + RateLimiter).
Test: 15 unit test PASSED (bertambah 7: SSRF guard, CSV safe, rate limiter, audit block, OSM sanitize).

## Bug yang Diperbaiki

### 1. Medan timeout (radius terlalu besar)
- **Sebelum:** radius 6000 (metro default) → Overpass timeout di kedua mirror → 0 leads
- **Sesudah:** radius chain 4000 → 2500, fallback otomatis → 8 leads dalam 3.1s
- **Root cause:** `directory.py:300` lama: `radius = 6000` untuk metro
- **Evidence:** test Medan cafe: `0 leads → 8 leads`

### 2. "Indonesia" geocode salah → "PT Siemens Indonesia"
- **Sebelum:** input "Indonesia" → geocode "PT Siemens Indonesia" di Jakarta → timeout
- **Sesudah:** deteksi "indonesia" → loop 20 kota terbesar → 24 leads dalam 60s
- **Root cause:** `directory.py:107` lama: `q = "Indonesia, Indonesia"` → Nominatim salah
- **Fix:** `_location_kind()` classify nasional → `_fetch_osm_national()` loop kota

### 3. Provinsi luas → 0 leads
- **Sebelum:** provinsi luas → geocode titik tengah hutan → 0 leads → hint saja
- **Sesudah:** provinsi → loop 5 kota terbesar → 20 leads dalam 35s
- **Fix:** `_fetch_osm_province()` loop kota per provinsi

### 4. Dead code `_fetch_osm_by_area`
- **Sebelum:** area query Overpass → 0 elements (tidak andal)
- **Sesudah:** dihapus total, diganti loop kota

### 5. Pesan error menyesatkan
- **Sebelum:** "radius 8km" padahal timeout, radius 6km
- **Sesudah:** hint akurat: timeout → "Overpass API lambat", 0 hasil → saran kota lain

## Fitur Baru

### Auto-detect lokasi backend
- Endpoint: `GET /api/geo/locate`
- Response: `GeoLocateResponse {city, region, country, ip}`
- Chain: ipwho.is → ipapi.co → None
- Frontend updated: coba backend endpoint dulu (`/api/geo/locate`), fallback IP services

## Struktur `_location_kind()`
```
"indonesia" / "ri" / "nusantara" → national → _fetch_osm_national (20 kota, 60s budget, 40 leads max)
"sumatera utara" / ... → province  → _fetch_osm_province (5 kota, 30s budget, 40 leads max)
"medan" / ...          → city      → _fetch_osm_city (radius 4000→2500, 2 mirrors)
```

## Data Test (2026-09-15, live)
| Lokasi | Keyword | Leads | Waktu |
|---|---|---|---|
| Medan | cafe | 8 | 3.1s |
| Indonesia | cafe | 24 | 60.5s |
| Indonesia | (all) | 8 | 61.7s |
| Sumatera Utara | cafe | 20 | 35.3s |
| Jakarta | cafe | 8 | 0.0s (cache) |

## File yang Diubah
- `server/app/services/scraper/directory.py` — rewrite: loop kota nasional/provinsi, radius chain, _location_kind()
- `server/app/models/schema.py` — tambah GeoLocateResponse
- `server/app/main.py` — tambah endpoint /api/geo/locate, versi → 1.3.0
- `client/src/services/location.js` — tambah fallback /api/geo/locate sebelum IP services

## Testing
- 8 unit test: PASSED (termasuk test Papua hint)
- Live test Medan/Indonesia/Sumut: BERHASIL
- `py_compile`: OK
