from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import List, Optional
import csv
import io

from .models.schema import (
    ProspectLead, ScanRequest, ScanResponse, AuditUrlRequest, AuditUrlResponse,
    PitchRequest, PitchResponse, CustomSourceConfig, CustomSourceConfigResponse,
    GeoLocateResponse,
)
from .services.audit import audit_web_url
from .services.pitch import generate_pitch
from .services.scraper.directory import DirectoryScraper
from .services.scraper.custom import CustomUserAppScraper
from .services.security import RateLimiter

app = FastAPI(
    title="ClientRadar API",
    description="Developer Lead Finder & Web Audit Engine by Gustiakmal",
    version="1.3.0"
)

# CORS — allowlist origin lokal saja (frontend Vite dev). Bukan wildcard:
# wildcard memungkinkan website jahat memanggil API dari browser korban.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter in-memory per client IP — cegah resource exhaustion (API4:2023)
scan_limiter = RateLimiter(max_requests=3, window_seconds=60)
audit_limiter = RateLimiter(max_requests=10, window_seconds=60)
config_limiter = RateLimiter(max_requests=5, window_seconds=60)
status_limiter = RateLimiter(max_requests=20, window_seconds=60)

# Persistent in-memory storage & scraper registry (Started empty)
directory_scraper = DirectoryScraper()
custom_app_scraper = CustomUserAppScraper()
leads_store: List[ProspectLead] = []
custom_source_config = CustomSourceConfig(
    app_endpoint_url="",
    active=False
)

@app.on_event("startup")
async def startup_event():
    # Initial state is strictly empty
    global leads_store
    leads_store = []

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "engine": "ClientRadar v1.3.0",
        "author": "Gustiakmal",
        "total_leads": len(leads_store),
        "custom_source_active": custom_source_config.active,
        "custom_source_configured": bool(custom_source_config.app_endpoint_url)
    }

@app.get("/api/geo/locate", response_model=GeoLocateResponse)
async def geo_locate():
    """
    Auto-detect lokasi user via IP (ipwho.is -> ipapi.co -> timezone fallback).
    Dipakai frontend untuk auto-fill kolom lokasi, dan API sharing untuk developer.
    """
    import httpx as _httpx

    async def _try_ipwho() -> Optional[dict]:
        try:
            async with _httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://ipwho.is/")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("success") is not False and (data.get("city") or data.get("region")):
                        return {
                            "city": data.get("city"),
                            "region": data.get("region"),
                            "country": data.get("country") or "Indonesia",
                            "ip": data.get("ip"),
                        }
        except Exception:
            pass
        return None

    async def _try_ipapi() -> Optional[dict]:
        try:
            async with _httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://ipapi.co/json/")
                if res.status_code == 200:
                    data = res.json()
                    if not data.get("error") and (data.get("city") or data.get("region")):
                        return {
                            "city": data.get("city"),
                            "region": data.get("region") or data.get("region_name"),
                            "country": data.get("country_name") or "Indonesia",
                            "ip": data.get("ip"),
                        }
        except Exception:
            pass
        return None

    # 1) ipwho.is  2) ipapi.co  3) timezone browser tidak tersedia di server — fallback None
    result = await _try_ipwho() or await _try_ipapi()
    if result:
        return GeoLocateResponse(**result)
    return GeoLocateResponse(city=None, region=None, country=None, ip=None)

@app.get("/api/leads", response_model=List[ProspectLead])
def get_current_leads(problem_type: Optional[str] = None):
    if not problem_type or problem_type == "all":
        return leads_store
    return [lead for lead in leads_store if lead.problem_type == problem_type]

@app.post("/api/scan", response_model=ScanResponse)
async def scan_leads(req: ScanRequest, request: Request):
    global leads_store
    client_ip = request.client.host if request.client else "unknown"
    if not scan_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Terlalu banyak scan — tunggu 60 detik")

    leads = []
    hint = None
    meta = None

    if custom_source_config.active and custom_source_config.app_endpoint_url:
        try:
            leads = await custom_app_scraper.fetch_leads(
                keyword=req.keyword,
                location=req.location,
                custom_endpoint=custom_source_config.app_endpoint_url
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    else:
        leads, meta = await directory_scraper.fetch_leads_with_meta(
            keyword=req.keyword or "",
            location=req.location
        )
        hint = (meta or {}).get("hint")

    leads_store = leads

    if req.problem_filter and req.problem_filter != "all":
        leads = [l for l in leads if l.problem_type == req.problem_filter]

    return ScanResponse(leads=leads, hint=hint, meta=meta)

@app.post("/api/audit-url", response_model=AuditUrlResponse)
async def audit_url_endpoint(req: AuditUrlRequest, request: Request):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="URL harus diisi")
    client_ip = request.client.host if request.client else "unknown"
    if not audit_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Terlalu banyak audit — tunggu 60 detik")
    return await audit_web_url(req.url.strip())

@app.post("/api/generate-pitch", response_model=PitchResponse)
def generate_pitch_endpoint(req: PitchRequest):
    return generate_pitch(req.lead, channel=req.channel)

@app.post("/api/leads/{lead_id}/status")
def update_lead_status(lead_id: str, status: str = Query(...), request: Request = None):
    client_ip = request.client.host if request and request.client else "unknown"
    if not status_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Terlalu banyak permintaan — tunggu 60 detik")
    for lead in leads_store:
        if lead.id == lead_id:
            lead.contact_status = status
            return {"status": "success", "lead": lead}
    raise HTTPException(status_code=404, detail="Lead tidak ditemukan")

def public_source_config():
    return CustomSourceConfigResponse(
        app_endpoint_url=custom_source_config.app_endpoint_url,
        active=custom_source_config.active,
        has_api_key=bool(custom_source_config.api_key)
    )

@app.get("/api/config/source", response_model=CustomSourceConfigResponse)
def get_source_config():
    return public_source_config()

@app.post("/api/config/source", response_model=CustomSourceConfigResponse)
def set_source_config(config: CustomSourceConfig, request: Request):
    global custom_source_config
    client_ip = request.client.host if request.client else "unknown"
    if not config_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Terlalu banyak permintaan — tunggu 60 detik")
    api_key = config.api_key.strip() if config.api_key else None
    if not api_key and config.app_endpoint_url == custom_source_config.app_endpoint_url:
        api_key = custom_source_config.api_key
    custom_source_config = config.model_copy(update={"api_key": api_key})
    custom_app_scraper.set_target_address(config.app_endpoint_url, api_key)
    return public_source_config()


def _csv_safe(value) -> str:
    """Cegah CSV formula injection (CWE-1236): prefix ' untuk sel diawali =+-@."""
    if value is None:
        return "-"
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


@app.get("/api/export")
def export_leads_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Nama Bisnis", "Kategori", "Lokasi", "Rating", "Jumlah Ulasan",
        "Telepon", "Instagram", "Website", "Masalah Utama", "Skor Peluang",
        "Estimasi Tarif Min", "Estimasi Tarif Max", "Solusi", "Status Kontak"
    ])
    for l in leads_store:
        writer.writerow([
            _csv_safe(l.id), _csv_safe(l.name), _csv_safe(l.category), _csv_safe(l.location),
            _csv_safe(l.rating), _csv_safe(l.reviews_count),
            _csv_safe(l.phone), _csv_safe(l.instagram), _csv_safe(l.website_url),
            _csv_safe(l.problem_type), _csv_safe(l.opportunity_score),
            _csv_safe(l.est_min_val), _csv_safe(l.est_max_val),
            _csv_safe(l.solution_text), _csv_safe(l.contact_status)
        ])
    return PlainTextResponse(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clientradar_leads.csv"}
    )
