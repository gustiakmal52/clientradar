import urllib.parse
from ..models.schema import ProspectLead, PitchResponse

def generate_pitch(lead: ProspectLead, channel: str = "wa") -> PitchResponse:
    name = lead.name
    cat = lead.category
    loc = lead.location
    prob = lead.problem_type
    sol = lead.solution_text
    rating = lead.rating or 4.8
    phone = lead.phone or ""

    clean_phone = phone
    if clean_phone.startswith("0"):
        clean_phone = "62" + clean_phone[1:]
    clean_phone = "".join(filter(str.isdigit, clean_phone))

    text = ""
    direct_link = None

    if channel == "wa":
        if prob == "missing_web":
            text = (
                f"Halo tim *{name}*, salam kenal.\n\n"
                f"Saya perhatikan {name} di {loc} memiliki reputasi yang baik, "
                f"namun saat saya ingin melihat katalog layanan & jadwal reservasi resminya, kolom website belum tersedia.\n\n"
                f"Sebagai developer independen, saya sempat membuat mockup preview solusi: *{sol}* "
                f"agar pasien/pelanggan bisa langsung memesan slot tanpa admin repot membalas chat satu per satu.\n\n"
                f"Kira-kira berkenan kah jika saya kirimkan tautan demonya secara gratis untuk dilihat-lihat? Terima kasih banyak."
            )
        elif prob == "unresponsive_mobile":
            text = (
                f"Halo tim *{name}*, salam kenal.\n\n"
                f"Saya sempat mengunjungi website resmi {name} via smartphone. Layanannya sangat menarik, "
                f"namun saat dibuka di ponsel, waktu loadingnya agak lambat dan tampilan tombol reservasinya bergeser.\n\n"
                f"Saya sudah merangkum dokumen mini-audit teknis singkat mengenai optimasi kecepatan & solusi: *{sol}* "
                f"agar calon pelanggan tidak batal pesan.\n\n"
                f"Apakah ada kontak manajer/penanggung jawab yang bisa saya kirimkan ringkasan auditnya? Terima kasih."
            )
        elif prob == "no_booking_flow":
            text = (
                f"Halo manajemen *{name}*, salam hangat.\n\n"
                f"Melihat antusiasme pelanggan {name} di {loc}, terdapat potensi besar untuk meningkatkan margin keuntungan "
                f"dengan memfasilitasi direct reservation otomatis tanpa potongan komisi pihak ketiga.\n\n"
                f"Solusi yang saya tawarkan: *{sol}*.\n\n"
                f"Jika berkenan, saya dengan senang hati mendemonstrasikan preview interaktifnya dalam 5 menit. Terima kasih!"
            )
        else:
            text = (
                f"Halo tim *{name}*, salam kenal.\n\n"
                f"Saya melihat reputasi {name} sudah sangat mapan di industri {cat}. "
                f"Untuk meningkatkan kepercayaan calon klien korporat/eksekutif, upgrade ke custom domain dan sistem modern: *{sol}* "
                f"akan sangat mendongkrak konversi.\n\n"
                f"Apakah berkenan saya bagikan portofolio singkat sistem serupa yang pernah kami buat? Terima kasih banyak."
            )

        if clean_phone:
            direct_link = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(text)}"

    elif channel == "email":
        text = (
            f"Subject: Tinjauan Akselerasi Portal Digital untuk {name}\n\n"
            f"Yth. Manajemen {name},\n\n"
            f"Perkenalkan saya seorang software developer independen. Mengamati reputasi positif {name} di {loc}, "
            f"kami melihat ada peluang strategis untuk memperluas akuisisi pelanggan digital:\n\n"
            f"Identifikasi Solusi: {sol}\n"
            f"Nilai Manfaat: Mempermudah reservasi instan 24 jam tanpa membebani jam kerja staf admin.\n\n"
            f"Kami telah menyiapkan draf demonstrasi interaktif tanpa komitmen apapun. "
            f"Apakah Anda memiliki waktu 5 menit pekan ini untuk meninjau pratinjaunya?\n\n"
            f"Hormat kami,\nDeveloper Partner"
        )
    else:  # Instagram DM
        ig_handle = lead.instagram or name.lower().replace(" ", "")
        ig_handle = ig_handle.replace("@", "")
        text = (
            f"Halo tim @{ig_handle}! Salam hangat dari Bandung 🙌\n\n"
            f"Suka sekali lihat konsistensi konten & layanan {name}. Mau tanya, untuk reservasi layanan saat ini apakah masih "
            f"manual via DM atau sudah otomatis via web? Kami ada ide mockup *{sol}* untuk bantu meringankan tim admin kakak.\n\n"
            f"Boleh izin kirimkan link demonya di sini Kak? Terima kasih banyak!"
        )

    return PitchResponse(
        channel=channel,
        text=text,
        direct_link=direct_link
    )
