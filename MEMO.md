# MEMO — ClientRadar v1.2.0

**Tanggal:** 2026-09-14  
**Author:** Gustiakmal  
**Commit:** `c26ca6a` + `3871003`

## Ringkasan
Real-data OSM seluruh Indonesia — dibuka **kosong tanpa template demo**. Sebelumnya `directory.py` berisi 6 mock Bandung (`DEFAULT_DATABASE`, `CITY_AREAS`, `_localize`) yang ngeloop di semua kota (`Dago, Makassar` dll). Sekarang dihapus total (`grep -c DEFAULT_DATABASE=0`).

## Keputusan Teknis
- **Sumber:** Nominatim (`q={kota}, Indonesia`, `countrycodes=id`) + Overpass `around:10000/6000/3000` + cache 600s, 2 mirror.
- **Seluruh Indonesia:** geocode per kota/kabupaten — bukan provinsi. Provinsi luas (`Papua bbox 5.09×7.49 deg`) centre di hutan → `return []` + `hint: Coba kota Jayapura/Manokwari`.
- **Metro padat:** Jakarta radius 6000 + single filter biar tidak 504 (bukti: `around:6000 200 8` vs `3000 timeout`).
- **Empty jujur:** `if not loc: return []` — tanpa lokasi atau 0 hasil/timeout → `[]` + hint, tanpa mock Bandung.
- **Frontend:** `App.jsx` dibuka `setLeads([])`, wajib isi lokasi, banner amber `scanHint`, `LeadsTable` empty state bedakan hint vs belum scan. `location.js` auto-detect `ipwho.is → ipapi.co → timezone`.
- **API:** `POST /api/scan` → `ScanResponse {leads, hint, meta}` (`api.js` kompatibel array lama).
- **Keamanan:** `allow_credentials False`, `valid_endpoint http/https`, Bearer `Authorization`, `is_ssl` dari `res.url.scheme`.

## Verifikasi
- `py_compile OK` — `Ran 8 tests OK` (`test_app.py` mock Papua hint)
- `vite build 1892 modules 57kB gzip OK`
- Live `127.0.0.1:8000/5173 health OK` — `Banjarmasin 12 real osm_node`, `Makassar 12`, `Jakarta 8` (`Tator, Cafe Al Tahrir`), `Jayapura 4`, `Papua hint Jayapura`

## Git
- `19 files, 863 insertions(+), 309 deletions(-)` — siap push untuk rekan seluruh Indonesia (clone → isi kota sendiri → OSM real).
