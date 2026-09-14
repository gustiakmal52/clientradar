import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app, custom_app_scraper
from app.services.audit import audit_web_url
from app.services.scraper.custom import CustomUserAppScraper


class ConfigTest(unittest.TestCase):
    def test_api_key_is_stored_but_never_returned(self):
        client = TestClient(app)
        response = client.post("/api/config/source", json={
            "app_endpoint_url": "https://example.com/leads",
            "api_key": "review-secret",
            "active": True,
        })

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("api_key", response.json())
        self.assertTrue(response.json()["has_api_key"])
        self.assertNotIn("api_key", client.get("/api/config/source").json())

    def test_empty_custom_result_does_not_fall_back_to_demo_data(self):
        client = TestClient(app)
        client.post("/api/config/source", json={
            "app_endpoint_url": "https://example.com/leads",
            "active": True,
        })
        try:
            with patch.object(custom_app_scraper, "fetch_leads", AsyncMock(return_value=[])):
                response = client.post("/api/scan", json={"keyword": "klinik"})

            self.assertEqual(response.status_code, 200)
            body = response.json()
            leads = body.get("leads") if isinstance(body, dict) and "leads" in body else body
            self.assertEqual(leads, [])
        finally:
            client.post("/api/config/source", json={"app_endpoint_url": "", "active": False})

    def test_scan_returns_empty_when_no_location(self):
        client = TestClient(app)
        client.post("/api/config/source", json={"app_endpoint_url": "", "active": False})
        response = client.post("/api/scan", json={"keyword": "", "location": ""})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        leads = body.get("leads") if isinstance(body, dict) and "leads" in body else body
        self.assertEqual(leads, [])

    def test_scan_empty_hint_for_province(self):
        # Papua adalah provinsi luas — harus kasih hint kota (Jayapura) baik itu timeout maupun kosong
        from app.services.scraper.directory import DirectoryScraper
        import asyncio
        from unittest.mock import patch as m_patch

        scraper = DirectoryScraper()

        # Mock OSM biar deterministik (network lambat/504 di test)
        async def fake_fetch_osm(self2, kw, loc):
            return []  # simulasi 0 hasil -> trigger hint provinsi

        with m_patch.object(DirectoryScraper, "_fetch_osm", fake_fetch_osm):
            leads, meta = asyncio.run(scraper.fetch_leads_with_meta("", "Papua"))
        self.assertEqual(leads, [])
        self.assertIsNotNone(meta.get("hint"))
        self.assertIn("Jayapura", meta["hint"])


class CustomScraperTest(unittest.IsolatedAsyncioTestCase):
    async def test_api_key_is_sent_as_bearer_token(self):
        request = {}

        class Response:
            status_code = 200

            @staticmethod
            def raise_for_status():
                return None

            @staticmethod
            def json():
                return []

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def get(self, url, **kwargs):
                request.update(url=url, **kwargs)
                return Response()

        scraper = CustomUserAppScraper("https://example.com/leads", "review-secret")
        with patch("app.services.scraper.custom.httpx.AsyncClient", return_value=Client()):
            await scraper.fetch_leads("klinik", "Bandung")

        self.assertEqual(request["headers"], {"Authorization": "Bearer review-secret"})

    async def test_empty_custom_result_stays_empty(self):
        class Response:
            status_code = 200

            @staticmethod
            def raise_for_status():
                return None

            @staticmethod
            def json():
                return []

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def get(self, *_args, **_kwargs):
                return Response()

        with patch("app.services.scraper.custom.httpx.AsyncClient", return_value=Client()):
            leads = await CustomUserAppScraper("https://example.com/leads").fetch_leads("none")

        self.assertEqual(leads, [])

    async def test_failed_https_connection_is_not_reported_as_valid_ssl(self):
        class Client:
            async def __aenter__(self):
                raise OSError("connection failed")

            async def __aexit__(self, *_):
                return None

        with patch("app.services.audit.httpx.AsyncClient", return_value=Client()):
            result = await audit_web_url("https://example.com")

        self.assertIsNone(result.status_code)
        self.assertFalse(result.is_ssl)

    async def test_https_redirect_to_http_is_not_reported_as_ssl(self):
        class Response:
            status_code = 200
            url = httpx.URL("http://example.com/final")
            text = '<meta name="viewport" content="width=device-width">'
            headers = {}

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def get(self, *_args, **_kwargs):
                return Response()

        with patch("app.services.audit.httpx.AsyncClient", return_value=Client()):
            result = await audit_web_url("https://example.com")

        self.assertFalse(result.is_ssl)
        self.assertTrue(any("Redirect" in issue.label for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
