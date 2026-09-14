from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from typing import List, Optional
import csv
import io

from .models.schema import (
    ProspectLead, ScanRequest, ScanResponse, AuditUrlRequest, AuditUrlResponse,
    PitchRequest, PitchResponse, CustomSourceConfig, CustomSourceConfigResponse
)
from .services.audit import audit_web_url
from .services.pitch import generate_pitch
from .services.scraper.directory import DirectoryScraper
from .services.scraper.custom import CustomUserAppScraper

app = FastAPI(
    title="ClientRadar API",
    description="Developer Lead Finder & Web Audit Engine by Gustiakmal",
    version="1.2.0"
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "engine": "ClientRadar v1.2.0",
        "author": "Gustiakmal",
        "total_leads": len(leads_store),
        "custom_source_active": custom_source_config.active,
        "custom_source_configured": bool(custom_source_config.app_endpoint_url)
    }

@app.get("/api/leads", response_model=List[ProspectLead])
def get_current_leads(problem_type: Optional[str] = None):
    if not problem_type or problem_type == "all":
        return leads_store
    return [lead for lead in leads_store if lead.problem_type == problem_type]

@app.post("/api/scan", response_model=ScanResponse)
async def scan_leads(req: ScanRequest):
    global leads_store
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
async def audit_url_endpoint(req: AuditUrlRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="URL harus diisi")
    return await audit_web_url(req.url.strip())

@app.post("/api/generate-pitch", response_model=PitchResponse)
def generate_pitch_endpoint(req: PitchRequest):
    return generate_pitch(req.lead, channel=req.channel)

@app.post("/api/leads/{lead_id}/status")
def update_lead_status(lead_id: str, status: str = Query(...)):
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
def set_source_config(config: CustomSourceConfig):
    global custom_source_config
    api_key = config.api_key.strip() if config.api_key else None
    if not api_key and config.app_endpoint_url == custom_source_config.app_endpoint_url:
        api_key = custom_source_config.api_key
    custom_source_config = config.model_copy(update={"api_key": api_key})
    custom_app_scraper.set_target_address(config.app_endpoint_url, api_key)
    return public_source_config()

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
            l.id, l.name, l.category, l.location, l.rating, l.reviews_count,
            l.phone or "-", l.instagram or "-", l.website_url or "-",
            l.problem_type, l.opportunity_score, l.est_min_val, l.est_max_val,
            l.solution_text, l.contact_status
        ])
    return PlainTextResponse(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clientradar_leads.csv"}
    )
