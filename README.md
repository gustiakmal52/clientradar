# ClientRadar — Developer Intelligence & Prospecting Engine

> **Author:** Gustiakmal  
> **Version:** 1.3.0  
> **License:** MIT

A full-stack, modular client prospecting and web audit application designed specifically for freelance developers, agencies, and software houses to discover high-value development clients, run instant technical audits, and generate high-converting outreach pitches.

---

## 🚀 Fitur Utama

1. **Mesin Pencari Prospek Klien (Client Radar):**
   * Mendeteksi bisnis lokal/klien berdasarkan kelemahan digital:
     * 🚫 **Belum Ada Web:** Bisnis dengan ulasan/rating Google tinggi namun tanpa link website resmi.
     * 📱 **Mobile Rusak / Lelet:** Website dengan waktu muat lambat (>2.5s) atau tanpa viewport mobile.
     * 💬 **Tanpa Booking Flow:** Web statis tanpa jalur konversi WhatsApp langsung.
     * ⚠️ **Tech Stack Usang:** Menggunakan template subdomain gratisan atau CMS versi lama.
   * **Seluruh Indonesia:** scan nasional (loop 20 kota terbesar), scan per provinsi (loop kota di dalamnya), atau scan kota tunggal — radius Overpass adaptive (4000m → 2500m) anti-timeout.
   * **Auto-detect lokasi:** `GET /api/geo/locate` mendeteksi kota user via IP (ipwho.is → ipapi.co), frontend auto-fill kolom lokasi saat app dibuka.

2. **Audit Live URL Langsung (On-Demand Web Auditor):**
   * Analisis instan untuk sembarang website target: status HTTP, sertifikat SSL, latency response time, deteksi teknologi (WordPress, Shopify, Next.js, jQuery, dsb.), dan daftar isu teknis.

3. **Generator Penawaran Dingin Anti-Spam (Outreach Pitch):**
   * Memformat pesan profesional berbasis solusi bisnis (bukan jargon teknis) untuk WhatsApp, Email, dan Instagram DM.
   * Dilengkapi tombol satu-klik **"Kirim via WhatsApp Langsung"** (`wa.me`).

4. **Konektor Adapter Aplikasi Kustom (Modular Custom Source):**
   * Siap menerima alamat URL atau API endpoint dari aplikasi yang akan Anda bagikan sewaktu-waktu.
   * Begitu alamat target diinputkan di menu pengaturan (`Target: Custom App`), scraper otomatis mengalihkan query ke endpoint tersebut.

---

## 🛠️ Arsitektur & Teknologi

* **Frontend:** Vite, React 18, Tailwind CSS, Lucide Icons, Plus Jakarta Sans, JetBrains Mono.
* **Backend:** FastAPI, Python 3.14, HTTPX (async client), BeautifulSoup4, Pydantic v2, Uvicorn.

---

## ⚡ Cara Menjalankan

### 1. Instalasi pertama
```bash
python3 -m venv venv
venv/bin/python3 -m pip install -r server/requirements.txt
npm ci --prefix client
```

### 2. Install Launcher (sekali saja)
```bash
./clientradar install
```
Membuat:
- `~/.local/bin/clientradar` — perintah terminal
- Desktop shortcut `clientradar.desktop` (klik untuk start)
- Menu aplikasi "ClientRadar"

### 3. Jalankan
```bash
clientradar start     # jalankan backend + frontend + buka browser
clientradar status    # cek status
clientradar stop      # hentikan semua
clientradar restart   # ulang
clientradar uninstall # hapus launcher (project tetap utuh)
```

Atau langsung:
```bash
./start.sh
```

Secara default aplikasi hanya dapat diakses dari komputer sendiri. Untuk jaringan yang Anda percaya, jalankan `CLIENTRADAR_HOST=0.0.0.0 ./start.sh`. Mode ini ditujukan untuk satu pengguna/instalasi lokal; jangan mengekspos API langsung ke internet tanpa autentikasi, penyimpanan per pengguna, dan pembatasan tujuan request keluar.

> **Keamanan bawaan (v1.3.0):** SSRF guard memblokir fetch ke alamat internal (localhost/private/link-local/cloud metadata) pada audit URL & endpoint kustom; CORS dibatasi ke origin lokal (`localhost:5173`, `127.0.0.1:5173`); rate limiter per IP (scan 3/60s, audit 10/60s, config 5/60s); export CSV disanitasi terhadap formula injection; rating/ulasan lead ditandai sebagai estimasi internal (bukan data Google Maps).

### 3. Jalankan Terpisah
**Backend:**
```bash
cd server
../venv/bin/python3 -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd client
npm run dev
```

* **Frontend UI:** [http://localhost:5173](http://localhost:5173)
* **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Auto-detect lokasi:** [http://localhost:8000/api/geo/locate](http://localhost:8000/api/geo/locate)

> Sumber bawaan berisi data demonstrasi. Untuk mengambil data nyata, hubungkan endpoint/API milik Anda melalui **Target: Custom App**. Token opsional dikirim sebagai `Authorization: Bearer <token>` dan tidak dikembalikan oleh API konfigurasi.

## 🌏 Scan Seluruh Indonesia

Masukkan `Indonesia` sebagai lokasi → sistem otomatis scan 20 kota terbesar (Jakarta, Surabaya, Bandung, Medan, Semarang, Makassar, Palembang, dll) dan menggabungkan hasilnya. Masukkan nama provinsi (misal `Sumatera Utara`) → scan kota-kota di dalamnya. Radius Overpass adaptive (4000m → 2500m) mencegah timeout di kota padat.

## 📍 Auto-detect Lokasi

Frontend otomatis mendeteksi kota user saat app dibuka (via `/api/geo/locate` → ipwho.is → ipapi.co → timezone browser). Untuk API sharing, panggil langsung:

```bash
curl http://localhost:8000/api/geo/locate
# {"city":"Jakarta","region":"Jakarta","country":"Indonesia","ip":"..."}
```
