import time
import httpx
from bs4 import BeautifulSoup
from typing import List, Optional
from ..models.schema import DiagnosticItem, AuditUrlResponse
from .security import validate_ssrf_url

MAX_RESPONSE_BYTES = 2_000_000  # 2 MB cap — cegah memory exhaustion (CWE-400)
MAX_REDIRECTS = 3


class _BlockedTarget(Exception):
    """URL target diblokir oleh SSRF guard."""


class _ResponseTooLarge(Exception):
    """Respons melebihi batas ukuran."""


async def _safe_get(client: httpx.AsyncClient, url: str, headers: dict):
    """GET dengan SSRF validation tiap hop + redirect manual + size cap.

    Redirect diikuti manual agar setiap hop divalidasi ulang (anti-bypass
    via redirect ke alamat internal). follow_redirects=False di httpx.
    """
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        err = validate_ssrf_url(current)
        if err:
            raise _BlockedTarget(err)
        async with client.stream(
            "GET", current, headers=headers, follow_redirects=False
        ) as res:
            if res.status_code in (301, 302, 303, 307, 308):
                location = res.headers.get("location")
                if location:
                    current = str(httpx.URL(current).join(location))
                    continue
            total = 0
            chunks = []
            async for chunk in res.aiter_bytes():
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    raise _ResponseTooLarge()
                chunks.append(chunk)
            return res, b"".join(chunks)
    raise _BlockedTarget("Terlalu banyak redirect")


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
        async with httpx.AsyncClient(timeout=10.0) as client:
            res, body = await _safe_get(client, target_url, headers={
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

            # HTML Parsing (decode aman, batasi ukuran)
            html_text = body.decode("utf-8", errors="replace").lower()
            soup = BeautifulSoup(html_text, "html.parser")

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

    except _BlockedTarget as exc:
        score = 20
        issues.append(DiagnosticItem(
            status="critical",
            label="Target Tidak Diizinkan",
            detail=str(exc)
        ))
    except _ResponseTooLarge:
        score = 20
        issues.append(DiagnosticItem(
            status="critical",
            label="Respons Terlalu Besar",
            detail="Website mengirim respons melebihi batas aman (2 MB)."
        ))
    except Exception:
        score = 20
        issues.append(DiagnosticItem(
            status="critical",
            label="Koneksi Timeout / Domain Tidak Merespon",
            detail="Gagal menghubungi server web. Periksa kembali alamatnya."
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