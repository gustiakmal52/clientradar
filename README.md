# ClientRadar — Developer Intelligence & Prospecting Engine

> **Author:** Gustiakmal  
> **Version:** 1.2.0  
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

### 1. Jalankan Sekaligus (All-in-One)
```bash
./start.sh
```

### 2. Jalankan Terpisah
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
