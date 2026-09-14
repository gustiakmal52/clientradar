from abc import ABC, abstractmethod
from typing import List, Optional
from ...models.schema import ProspectLead

class BaseScraperAdapter(ABC):
    """
    Abstract Interface for Scraper Data Providers.
    Any custom scraper source (Google Maps, Job Board, Directory, or User's App)
    implements this contract.
    """
    @abstractmethod
    async def fetch_leads(self, keyword: str, location: Optional[str] = None, custom_endpoint: Optional[str] = None) -> List[ProspectLead]:
        pass
