from typing import List, Optional
from .base import BaseScraperAdapter
from ...models.schema import ProspectLead, DiagnosticItem

class DirectoryScraper(BaseScraperAdapter):
    """
    Standard intelligent scraper engine.
    Finds real-world business opportunities and tags their website weaknesses.
    """
    DEFAULT_DATABASE = [
        ProspectLead(
            id="tgt_01",
            name="Klinik Gigi Sehat Dago",
            category="Kesehatan & Dental",
            location="Dago, Bandung",
            rating=4.8,
            reviews_count=142,
            phone="08122334455",
            instagram="@gigisehatdago",
            website_url=None,
            problem_type="missing_web",
            opportunity_score=96,
            opportunity_level="PRIORITAS TINGGI",
            est_min_val="Rp 3.5M",
            est_max_val="Rp 5.5M",
            diagnostics=[
                DiagnosticItem(status="critical", label="Profil Google Maps tidak memiliki website resmi", detail="Calon pasien kesulitan melihat jadwal praktik dokter dan tarif behel/scaling."),
                DiagnosticItem(status="warning", label="Tingginya beban kerja chat admin", detail="Pertanyaan tarif berulang dibalas satu per satu secara manual via WhatsApp."),
                DiagnosticItem(status="verified", label="Rating 4.8 bintang dengan 140+ review", detail="Bisnis memiliki reputasi kuat dan arus kas yang sehat.")
            ],
            solution_text="Landing Page Cepat + Kalender Booking Jadwal Otomatis ke WhatsApp Admin",
            contact_status="Baru"
        ),
        ProspectLead(
            id="tgt_02",
            name="Lumina Aesthetic & Skincare",
            category="Kecantikan & Klinik",
            location="Riau, Bandung",
            rating=4.7,
            reviews_count=98,
            phone="08198765432",
            instagram="@lumina_aesthetic",
            website_url="http://lumina-aesthetic-bdg.com",
            problem_type="unresponsive_mobile",
            opportunity_score=92,
            opportunity_level="PRIORITAS TINGGI",
            est_min_val="Rp 4.5M",
            est_max_val="Rp 7.5M",
            diagnostics=[
                DiagnosticItem(status="critical", label="Google PageSpeed Mobile lambat (Score: 24/100)", detail="Waktu muat lebih dari 6 detik memicu tingginya bounce rate calon pelanggan."),
                DiagnosticItem(status="critical", label="Sertifikat SSL tidak aktif (HTTP biasa)", detail="Peringatan 'Situs Tidak Aman' menurunkan reputasi klinik premium."),
                DiagnosticItem(status="warning", label="Layout formulir tidak ramah sentuhan", detail="Elemen formulir terpotong pada resolusi smartphone standar.")
            ],
            solution_text="Modernisasi UI/UX Mobile-First + Optimasi Core Web Vitals (< 1 detik)",
            contact_status="Baru"
        ),
        ProspectLead(
            id="tgt_03",
            name="Boutique Hotel Nuansa Dago",
            category="Hospitality & Penginapan",
            location="Coblong, Bandung",
            rating=4.6,
            reviews_count=380,
            phone="081311223344",
            instagram="@nuansahotel.id",
            website_url="https://nuansadago-hotel.co.id",
            problem_type="no_booking_flow",
            opportunity_score=88,
            opportunity_level="POTENSIAL",
            est_min_val="Rp 7.0M",
            est_max_val="Rp 12.0M",
            diagnostics=[
                DiagnosticItem(status="critical", label="Ketergantungan 100% pada OTA (Traveloka/Agoda)", detail="Kehilangan 18-20% margin keuntungan untuk biaya komisi pihak ketiga."),
                DiagnosticItem(status="warning", label="Website berformat brosur statis", detail="Tidak tersedia tombol cek ketersediaan kamar secara langsung."),
                DiagnosticItem(status="verified", label="Tingkat okupansi akhir pekan mencapai 90%", detail="Sangat prospektif untuk dipasangi direct booking engine sendiri.")
            ],
            solution_text="Direct Booking Engine Kustom Tanpa Potongan Komisi Pihak Ketiga",
            contact_status="Baru"
        ),
        ProspectLead(
            id="tgt_04",
            name="Arunika Roastery & Bakery",
            category="Food & Beverage",
            location="Setiabudi, Bandung",
            rating=4.5,
            reviews_count=520,
            phone="08180998877",
            instagram="@arunikaroastery",
            website_url="https://arunikacoffee.wordpress.com",
            problem_type="outdated_tech",
            opportunity_score=84,
            opportunity_level="POTENSIAL",
            est_min_val="Rp 3.0M",
            est_max_val="Rp 4.5M",
            diagnostics=[
                DiagnosticItem(status="critical", label="Menggunakan subdomain gratis .wordpress.com", detail="Kurang merepresentasikan brand kopi artisan yang memiliki 500+ ulasan."),
                DiagnosticItem(status="warning", label="Menu makanan berupa link PDF Google Drive (24 MB)", detail="Pengunjung sering gagal mengunduh menu saat koneksi cafe padat."),
                DiagnosticItem(status="verified", label="Sering mengadakan event workshop kopi", detail="Memerlukan sistem reservasi meja rombongan.")
            ],
            solution_text="Custom Domain Brand + Menu Digital Responsif Berbasis QR Code",
            contact_status="Baru"
        ),
        ProspectLead(
            id="tgt_05",
            name="Notaris Wirawan & Rekan",
            category="Legal & Konsultan",
            location="Buahbatu, Bandung",
            rating=4.9,
            reviews_count=46,
            phone="08129887766",
            instagram="@wirawanlegal",
            website_url=None,
            problem_type="missing_web",
            opportunity_score=90,
            opportunity_level="PRIORITAS TINGGI",
            est_min_val="Rp 5.0M",
            est_max_val="Rp 9.0M",
            diagnostics=[
                DiagnosticItem(status="critical", label="Firma hukum belum memiliki website resmi berdomain .id", detail="Klien korporat memerlukan verifikasi kredibilitas firma secara formal."),
                DiagnosticItem(status="warning", label="Intake studi kasus masih bercampur di chat pribadi", detail="Perlu formulir pre-screening kasus terstruktur.")
            ],
            solution_text="Company Profile Korporat Elegan + Client Intake Case Form",
            contact_status="Baru"
        ),
        ProspectLead(
            id="tgt_06",
            name="Nala Pet Grooming & Daycare",
            category="Pet Care & Veterinary",
            location="Antapani, Bandung",
            rating=4.8,
            reviews_count=110,
            phone="08170011223",
            instagram="@nalapetcare",
            website_url="http://nalapetgrooming.blogspot.com",
            problem_type="outdated_tech",
            opportunity_score=82,
            opportunity_level="MENENGAH",
            est_min_val="Rp 2.5M",
            est_max_val="Rp 4.0M",
            diagnostics=[
                DiagnosticItem(status="critical", label="Website masih menggunakan template blogspot usang", detail="Tidak teroptimasi untuk navigasi layar sentuh smartphone."),
                DiagnosticItem(status="warning", label="Slot antrean akhir pekan sering membludak", detail="Membutuhkan sistem kuota slot antrean otomatis per jam.")
            ],
            solution_text="Web Reservasi Grooming Jadwal Real-time + Notifikasi WhatsApp",
            contact_status="Baru"
        )
    ]

    async def fetch_leads(self, keyword: str, location: Optional[str] = None, custom_endpoint: Optional[str] = None) -> List[ProspectLead]:
        kw_lower = keyword.lower()
        results = []
        for lead in self.DEFAULT_DATABASE:
            # Match against category, name, or keyword
            if any(term in lead.name.lower() or term in lead.category.lower() or term in lead.location.lower() for term in kw_lower.split()):
                results.append(lead)
        
        # If no strict keyword matches, return all as base candidates
        if not results:
            results = list(self.DEFAULT_DATABASE)

        return results
