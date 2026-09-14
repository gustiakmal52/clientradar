from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class DiagnosticItem(BaseModel):
    status: Literal["critical", "warning", "verified"]
    label: str
    detail: str

class ProspectLead(BaseModel):
    id: str
    name: str
    category: str
    location: str
    rating: float = 0.0
    reviews_count: int = 0
    phone: Optional[str] = None
    instagram: Optional[str] = None
    website_url: Optional[str] = None
    problem_type: Literal["missing_web", "unresponsive_mobile", "no_booking_flow", "outdated_tech"]
    opportunity_score: int = 85
    opportunity_level: Literal["PRIORITAS TINGGI", "POTENSIAL", "MENENGAH"]
    est_min_val: str
    est_max_val: str
    diagnostics: List[DiagnosticItem] = []
    solution_text: str
    contact_status: str = "Baru"

class ScanRequest(BaseModel):
    keyword: str
    location: Optional[str] = None
    problem_filter: Optional[str] = "all"
    custom_source_url: Optional[str] = None

class AuditUrlRequest(BaseModel):
    url: str

class AuditUrlResponse(BaseModel):
    url: str
    status_code: Optional[int] = None
    is_ssl: bool = False
    response_time_ms: float = 0.0
    has_mobile_viewport: bool = False
    detected_tech: List[str] = []
    issues: List[DiagnosticItem] = []
    overall_score: int = 50

class PitchRequest(BaseModel):
    lead: ProspectLead
    channel: Literal["wa", "email", "dm"] = "wa"

class PitchResponse(BaseModel):
    channel: str
    text: str
    direct_link: Optional[str] = None

class CustomSourceConfig(BaseModel):
    app_endpoint_url: str
    api_key: Optional[str] = None
    active: bool = True
