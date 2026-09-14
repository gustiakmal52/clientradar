import time
import httpx
from bs4 import BeautifulSoup
from typing import List
from ..models.schema import DiagnosticItem, AuditUrlResponse

async def audit_web_url(url: str) -> AuditUrlResponse:
    if not url.startswith("http://") and not url.startswith("https://"):
        target_url = "https://" + url
    else:
        target_url = url

    uses_https = target_url.startswith("https://")
    is_ssl = False
    issues: List[DiagnosticItem] = []
    detected_tech: List[str] = []
    score = 100

    if not uses_https:
        score -= 25
        issues.append(DiagnosticItem(
            status="critical",
            label="Sertifikat SSL Tidak Aktif (HTTP Biasa)",
            detail="Browser menandai web sebagai 'Not Secure'. Berpotensi menurunkan kepercayaan pelanggan."
        ))

    status_code = None
    elapsed_ms = 0.0
    has_viewport = False

    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            res = await client.get(target_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            })
            elapsed_ms = round((time.time() - start_time) * 1000, 1)
            status_code = res.status_code
            is_ssl = res.url.scheme == "https"

            if uses_https and not is_ssl:
                score -= 25
                issues.append(DiagnosticItem(
                    status="critical",
                    label="Redirect Berakhir Tanpa HTTPS",
                    detail="Website mengalihkan koneksi HTTPS ke HTTP biasa."
                ))

            if status_code >= 400:
                score -= 30
                issues.append(DiagnosticItem(
                    status="critical",
                    label=f"HTTP Error {status_code}",
                    detail="Halaman tidak dapat diakses secara normal oleh pengunjung."
                ))

            if elapsed_ms > 2500:
                score -= 20
                issues.append(DiagnosticItem(
                    status="critical",
                    label=f"Loading Sangat Lambat ({elapsed_ms}ms)",
                    detail="Waktu muat di atas 2.5 detik menyebabkan tingginya angka bounce rate pengunjung."
                ))
            elif elapsed_ms > 1200:
                score -= 10
                issues.append(DiagnosticItem(
                    status="warning",
                    label=f"Response Time Lambat ({elapsed_ms}ms)",
                    detail="Website membutuhkan optimasi aset dan kompresi gambar."
                ))

            # HTML Parsing
            soup = BeautifulSoup(res.text, "html.parser")

            # Check Mobile Viewport
            viewport = soup.find("meta", attrs={"name": "viewport"})
            if viewport and "width=" in str(viewport.get("content", "")):
                has_viewport = True
            else:
                score -= 30
                issues.append(DiagnosticItem(
                    status="critical",
                    label="Tidak Ramah Ponsel (No Mobile Viewport)",
                    detail="Tampilan website tidak responsif dan berantakan ketika diakses dari smartphone."
                ))

            # Check Tech Signatures
            html_text = res.text.lower()
            headers_str = str(res.headers).lower()

            if "wp-content" in html_text or "wp-includes" in html_text or "wordpress" in headers_str:
                detected_tech.append("WordPress")
                if "xmlrpc.php" in html_text:
                    issues.append(DiagnosticItem(
                        status="warning",
                        label="XML-RPC Aktif pada WordPress",
                        detail="Konfigurasi default WordPress rentan terhadap serangan brute force & amplify."
                    ))
            if "shopify" in html_text or "cdn.shopify.com" in html_text:
                detected_tech.append("Shopify")
            if "wix.com" in html_text:
                detected_tech.append("Wix Site Builder")
            if "blogspot.com" in html_text:
                detected_tech.append("Blogger / Blogspot")
                score -= 15
                issues.append(DiagnosticItem(
                    status="warning",
                    label="Menggunakan Template Blogspot Lama",
                    detail="Kurang kredibel untuk brand profesional modern."
                ))
            if "__next" in html_text or "_next/static" in html_text:
                detected_tech.append("Next.js")
            if "jquery" in html_text:
                detected_tech.append("jQuery Legacy")

            # Check WhatsApp booking link
            if "wa.me/" not in html_text and "api.whatsapp.com" not in html_text:
                issues.append(DiagnosticItem(
                    status="warning",
                    label="Tanpa Tombol WhatsApp Direct Booking",
                    detail="Pelanggan Indonesia umumnya lebih suka melakukan reservasi cepat via WhatsApp."
                ))

    except Exception as e:
        score = 20
        issues.append(DiagnosticItem(
            status="critical",
            label="Koneksi Timeout / Domain Tidak Merespon",
            detail=f"Gagal menghubungi server web: {str(e)[:80]}"
        ))

    score = max(10, min(100, score))

    return AuditUrlResponse(
        url=target_url,
        status_code=status_code,
        is_ssl=is_ssl,
        response_time_ms=elapsed_ms,
        has_mobile_viewport=has_viewport,
        detected_tech=detected_tech,
        issues=issues,
        overall_score=score
    )
