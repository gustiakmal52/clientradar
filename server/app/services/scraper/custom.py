import httpx
from typing import List, Optional
from .base import BaseScraperAdapter
from ...models.schema import ProspectLead, DiagnosticItem

class CustomUserAppScraper(BaseScraperAdapter):
    """
    Adapter designed to consume the user's custom application address or API.
    Once the user shares their target URL/endpoint, this connector parses and maps
    the data directly into ClientRadar's standardized ProspectLead model.
    """
    def __init__(self, target_address: Optional[str] = None):
        self.target_address = target_address

    def set_target_address(self, address: str):
        self.target_address = address

    async def fetch_leads(self, keyword: str, location: Optional[str] = None, custom_endpoint: Optional[str] = None) -> List[ProspectLead]:
        endpoint = custom_endpoint or self.target_address
        if not endpoint:
            # Fallback if no target address configured yet
            return []

        leads: List[ProspectLead] = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(endpoint, params={"q": keyword, "location": location or ""})
                if res.status_code == 200:
                    data = res.json()
                    # Support both list directly or nested { "data": [...] }
                    items = data if isinstance(data, list) else data.get("data", data.get("leads", []))
                    for idx, item in enumerate(items):
                        lead = ProspectLead(
                            id=str(item.get("id", f"custom_{idx}")),
                            name=item.get("name", "Bisnis Target"),
                            category=item.get("category", "Layanan Profesional"),
                            location=item.get("location", location or "Indonesia"),
                            rating=float(item.get("rating", 4.5)),
                            reviews_count=int(item.get("reviews_count", 25)),
                            phone=item.get("phone", None),
                            instagram=item.get("instagram", None),
                            website_url=item.get("website", None),
                            problem_type=item.get("problem_type", "missing_web" if not item.get("website") else "unresponsive_mobile"),
                            opportunity_score=int(item.get("score", 90)),
                            opportunity_level=item.get("opportunity_level", "PRIORITAS TINGGI"),
                            est_min_val=item.get("est_min_val", "Rp 3.0M"),
                            est_max_val=item.get("est_max_val", "Rp 5.0M"),
                            diagnostics=[
                                DiagnosticItem(
                                    status="critical" if not item.get("website") else "warning",
                                    label="Dianalisis dari Aplikasi Kustom Pengguna",
                                    detail=f"Target diperoleh via konektor endpoint: {endpoint}"
                                )
                            ],
                            solution_text=item.get("solution_text", "Pengembangan Website Terintegrasi & Otomasi Sistem"),
                            contact_status="Baru"
                        )
                        leads.append(lead)
        except Exception as e:
            print(f"[CustomUserAppScraper Error]: {e}")
        
        return leads
