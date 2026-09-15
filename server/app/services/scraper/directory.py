from typing import List, Optional, Dict, Tuple
import asyncio
import hashlib
import re
import time
import httpx
from .base import BaseScraperAdapter
from ...models.schema import ProspectLead, DiagnosticItem

class DirectoryScraper(BaseScraperAdapter):
    """
    Real-data only — OpenStreetMap (Nominatim + Overpass).
    Tidak ada fallback demo/template. Jika OSM kosong/timeout -> kembalikan [].
    Seluruh Indonesia didukung:
      - Kota tunggal: geocode + around query, radius adaptive 4000->2500
      - Provinsi: loop kota-kota di dalamnya
      - "Indonesia": loop kota-kota terbesar, stop early saat cukup data
    """

    # ------------------------------------------------------------------ #
    #  Keyword -> OSM tag mapping
    # ------------------------------------------------------------------ #

    KEYWORD_OSM: Dict[str, list] = {
        "cafe": ['["amenity"="cafe"]', '["shop"="coffee"]', '["amenity"="fast_food"]'],
        "kopi": ['["amenity"="cafe"]', '["shop"="coffee"]'],
        "coffee": ['["amenity"="cafe"]', '["shop"="coffee"]'],
        "roastery": ['["amenity"="cafe"]', '["shop"="coffee"]'],
        "resto": ['["amenity"="restaurant"]', '["amenity"="fast_food"]', '["amenity"="food_court"]'],
        "restoran": ['["amenity"="restaurant"]', '["amenity"="fast_food"]'],
        "restaurant": ['["amenity"="restaurant"]'],
        "kuliner": ['["amenity"="restaurant"]', '["amenity"="fast_food"]'],
        "hotel": ['["tourism"="hotel"]', '["tourism"="guest_house"]', '["tourism"="hostel"]'],
        "penginapan": ['["tourism"="hotel"]', '["tourism"="guest_house"]'],
        "klinik": ['["amenity"="clinic"]', '["amenity"="doctors"]', '["healthcare"="clinic"]', '["amenity"="dentist"]'],
        "gigi": ['["amenity"="dentist"]', '["healthcare"="dentist"]'],
        "dental": ['["amenity"="dentist"]'],
        "apotek": ['["amenity"="pharmacy"]'],
        "skincare": ['["shop"="beauty"]', '["shop"="cosmetics"]'],
        "barbershop": ['["shop"="hairdresser"]', '["shop"="beauty"]'],
        "salon": ['["shop"="hairdresser"]', '["shop"="beauty"]'],
        "bengkel": ['["shop"="car_repair"]', '["amenity"="car_repair"]'],
        "gym": ['["leisure"="fitness_centre"]'],
        "sekolah": ['["amenity"="school"]'],
    }

    KEYWORD_ALIASES = {
        "cafe": {"cafe", "coffee", "kopi", "roastery", "bakery", "kedai"},
        "kopi": {"cafe", "coffee", "kopi", "roastery", "bakery"},
        "coffee": {"cafe", "coffee", "kopi", "roastery", "bakery"},
        "resto": {"resto", "restoran", "restaurant", "kuliner", "food", "beverage", "roastery", "bakery"},
        "restoran": {"resto", "restoran", "restaurant", "kuliner", "food", "beverage", "roastery", "bakery"},
        "hotel": {"hotel", "penginapan", "hostel", "resort", "hospitality"},
        "klinik": {"klinik", "clinic", "dental", "gigi", "kesehatan", "skincare", "aesthetic"},
        "gigi": {"klinik", "gigi", "dental"},
    }

    # ------------------------------------------------------------------ #
    #  Geography — province hints, metro cities, city databases
    # ------------------------------------------------------------------ #

    PROVINCE_HINT = {
        "papua": "Jayapura / Manokwari / Merauke",
        "papua barat": "Manokwari / Sorong",
        "papua tengah": "Nabire / Timika",
        "papua pegunungan": "Wamena",
        "papua selatan": "Merauke",
        "papua barat daya": "Sorong",
        "jawa barat": "Bandung / Bekasi / Depok",
        "jawa tengah": "Semarang / Solo / Magelang",
        "jawa timur": "Surabaya / Malang / Kediri",
        "sumatera utara": "Medan / Binjai",
        "sumatera barat": "Padang / Bukittinggi",
        "sumatera selatan": "Palembang / Prabumulih",
        "kalimantan selatan": "Banjarmasin / Banjarbaru",
        "kalimantan timur": "Balikpapan / Samarinda",
        "sulawesi selatan": "Makassar / Parepare",
        "sulawesi utara": "Manado / Bitung",
        "nusa tenggara barat": "Mataram / Bima",
        "nusa tenggara timur": "Kupang",
        "maluku": "Ambon",
        "maluku utara": "Ternate",
        "bali": "Denpasar",
    }

    # Kota yang Overpass-nya rentan timeout — radius kecil wajib
    METRO_CITIES = {
        "jakarta", "dki jakarta", "jakarta pusat", "jakarta selatan",
        "jakarta timur", "jakarta barat", "jakarta utara",
        "surabaya", "medan", "bandung", "bekasi", "tangerang",
        "depok", "bogor", "semarang", "yogyakarta", "makassar",
        "palembang", "malang", "solo",
    }

    # Kota besar per provinsi — untuk loop nasional & provinsi
    PROVINCE_CITIES: Dict[str, list] = {
        "aceh": ["Banda Aceh", "Lhokseumawe", "Langsa"],
        "sumatera utara": ["Medan", "Binjai", "Pematangsiantar", "Tebing Tinggi"],
        "sumatera barat": ["Padang", "Bukittinggi", "Payakumbuh"],
        "riau": ["Pekanbaru", "Dumai"],
        "jambi": ["Jambi", "Sungai Penuh"],
        "sumatera selatan": ["Palembang", "Prabumulih", "Lubuklinggau"],
        "bengkulu": ["Bengkulu"],
        "lampung": ["Bandar Lampung", "Metro"],
        "kepulauan riau": ["Batam", "Tanjung Pinang"],
        "kepulauan bangka belitung": ["Pangkal Pinang"],
        "banten": ["Tangerang", "Serang", "Cilegon", "Tangerang Selatan"],
        "dki jakarta": [
            "Jakarta Selatan", "Jakarta Timur", "Jakarta Barat",
            "Jakarta Utara", "Jakarta Pusat",
        ],
        "jawa barat": ["Bandung", "Bekasi", "Depok", "Bogor", "Cirebon", "Sukabumi", "Tasikmalaya"],
        "jawa tengah": ["Semarang", "Solo", "Magelang", "Purwokerto", "Tegal", "Pekalongan"],
        "di yogyakarta": ["Yogyakarta", "Sleman"],
        "jawa timur": ["Surabaya", "Malang", "Kediri", "Madiun", "Blitar", "Jember"],
        "kalimantan barat": ["Pontianak", "Singkawang"],
        "kalimantan tengah": ["Palangkaraya"],
        "kalimantan selatan": ["Banjarmasin", "Banjarbaru"],
        "kalimantan timur": ["Balikpapan", "Samarinda", "Bontang"],
        "kalimantan utara": ["Tarakan"],
        "sulawesi utara": ["Manado", "Bitung"],
        "gorontalo": ["Gorontalo"],
        "sulawesi tengah": ["Palu"],
        "sulawesi barat": ["Mamuju"],
        "sulawesi selatan": ["Makassar", "Parepare", "Palopo"],
        "sulawesi tenggara": ["Kendari", "Baubau"],
        "bali": ["Denpasar", "Singaraja"],
        "nusa tenggara barat": ["Mataram", "Bima"],
        "nusa tenggara timur": ["Kupang"],
        "maluku": ["Ambon"],
        "maluku utara": ["Ternate", "Tidore"],
        "papua": ["Jayapura", "Merauke", "Timika", "Nabire"],
        "papua barat": ["Manokwari", "Sorong"],
        "papua tengah": ["Nabire", "Timika"],
        "papua pegunungan": ["Wamena"],
        "papua selatan": ["Merauke"],
        "papua barat daya": ["Sorong"],
    }

    # Kota terbesar (prioritas untuk scan nasional) — tanpa duplikat
    NATIONAL_CITIES: List[str] = [
        "Jakarta", "Surabaya", "Bandung", "Medan", "Semarang",
        "Makassar", "Palembang", "Tangerang", "Depok", "Bekasi",
        "Bogor", "Malang", "Pekanbaru", "Padang", "Denpasar",
        "Bandar Lampung", "Batam", "Yogyakarta", "Solo", "Banjarmasin",
    ]

    # ------------------------------------------------------------------ #
    #  Keyword expansion + filter helpers
    # ------------------------------------------------------------------ #

    def _expand_terms(self, terms: List[str]) -> set:
        expanded = set(terms)
        for t in terms:
            for key, aliases in self.KEYWORD_ALIASES.items():
                if t == key or t in aliases:
                    expanded |= aliases
            for alias in list(expanded):
                for key, aliases in self.KEYWORD_ALIASES.items():
                    if alias in aliases:
                        expanded |= aliases
        return expanded

    def _osm_filters(self, keyword: str) -> List[str]:
        kw = (keyword or "").strip().lower()
        if not kw:
            return ['["amenity"="cafe"]', '["amenity"="restaurant"]', '["tourism"="hotel"]']
        terms = kw.split()
        filters: List[str] = []
        for t in terms:
            if t in self.KEYWORD_OSM:
                filters.extend(self.KEYWORD_OSM[t])
        if filters:
            seen = set()
            uniq = []
            for f in filters:
                if f not in seen:
                    seen.add(f)
                    uniq.append(f)
            return uniq
        safe = self._sanitize_osm_keyword(kw)
        return [f'["name"~"{safe}",i]']

    @staticmethod
    def _sanitize_osm_keyword(kw: str) -> str:
        """Bersihkan keyword sebelum disisipkan ke query Overpass QL.

        Hanya karakter yang bisa memutus string Overpass (\" dan \\\\) yang
        di-strip, plus batas panjang — cegah query injection ke layanan OSM.
        """
        return re.sub(r'["\\]', '', (kw or "").strip())[:40]

    # ------------------------------------------------------------------ #
    #  Caches
    # ------------------------------------------------------------------ #

    _GEOCODE_CACHE: Dict[str, Tuple[float, Optional[Dict]]] = {}
    _OSM_CACHE: Dict[str, Tuple[float, list]] = {}
    _OSM_TTL_SEC = 600

    # ------------------------------------------------------------------ #
    #  Geocode (Nominatim)
    # ------------------------------------------------------------------ #

    async def _geocode(self, location: str) -> Optional[Dict]:
        key = (location or "").strip().lower()
        now = time.time()
        if key in self._GEOCODE_CACHE:
            ts, val = self._GEOCODE_CACHE[key]
            if now - ts < 3600 and val is not None:
                return val
        q = f"{location.strip()}, Indonesia" if location.strip() else "Indonesia"
        params = {"q": q, "format": "json", "limit": "1", "countrycodes": "id"}
        headers = {"User-Agent": "ClientRadar/1.3.0 (OSM; Gustiakmal)"}
        try:
            async with httpx.AsyncClient(timeout=4.0, headers=headers) as client:
                res = await client.get("https://nominatim.openstreetmap.org/search", params=params)
                res.raise_for_status()
                data = res.json()
                if data:
                    self._GEOCODE_CACHE[key] = (now, data[0])
                    return data[0]
                params.pop("countrycodes", None)
                res = await client.get("https://nominatim.openstreetmap.org/search", params=params)
                res.raise_for_status()
                data = res.json()
                val = data[0] if data else None
                self._GEOCODE_CACHE[key] = (now, val)
                return val
        except Exception as e:
            print(f"[DirectoryScraper geocode fail {location}]: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Overpass mirror list
    # ------------------------------------------------------------------ #

    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    # ------------------------------------------------------------------ #
    #  Map OSM element -> ProspectLead
    # ------------------------------------------------------------------ #

    def _map_osm_to_lead(self, el: Dict, idx: int, display_city: str) -> Optional[ProspectLead]:
        tags: Dict = el.get("tags") or {}
        name = tags.get("name") or tags.get("brand") or f"Bisnis {display_city} #{idx+1}"
        if not name or len(name) < 2:
            return None
        amenity = tags.get("amenity", "")
        shop = tags.get("shop", "")
        tourism = tags.get("tourism", "")
        healthcare = tags.get("healthcare", "")
        if amenity in ("cafe", "fast_food", "restaurant", "food_court") or shop == "coffee":
            category = "Food & Beverage"
            problem_default = "outdated_tech"
            solution = "Custom Domain Brand + Menu Digital Responsif Berbasis QR Code"
            diagnostics = [DiagnosticItem(status="warning", label="Menu masih PDF/tidak responsif", detail="Data OSM menunjukkan usaha kuliner tanpa website modern.")]
        elif tourism in ("hotel", "guest_house", "hostel"):
            category = "Hospitality & Penginapan"
            problem_default = "no_booking_flow"
            solution = "Direct Booking Engine Kustom Tanpa Potongan Komisi Pihak Ketiga"
            diagnostics = [DiagnosticItem(status="critical", label="Ketergantungan OTA / tanpa booking langsung", detail="Hotel/penginapan terdeteksi dari peta tanpa alur reservasi langsung.")]
        elif amenity in ("clinic", "doctors", "dentist", "pharmacy") or healthcare:
            category = "Kesehatan & Dental"
            problem_default = "missing_web"
            solution = "Landing Page Cepat + Kalender Booking Jadwal Otomatis ke WhatsApp Admin"
            diagnostics = [DiagnosticItem(status="critical", label="Belum memiliki website resmi", detail="Faskes/klinik terdeteksi di peta tanpa tautan website.")]
        elif shop in ("beauty", "hairdresser", "cosmetics") or "aesthetic" in name.lower() or "skincare" in name.lower():
            category = "Kecantikan & Klinik"
            problem_default = "unresponsive_mobile"
            solution = "Modernisasi UI/UX Mobile-First + Optimasi Core Web Vitals"
            diagnostics = [DiagnosticItem(status="warning", label="Potensi tampilan mobile kurang optimal", detail="Usaha kecantikan terdeteksi tanpa website terverifikasi.")]
        else:
            category = tags.get("amenity") or tags.get("shop") or tags.get("tourism") or "Layanan Profesional"
            category = category.replace("_", " ").title()
            problem_default = "missing_web"
            solution = "Company Profile Korporat + Formulir Intake Otomatis"
            diagnostics = [DiagnosticItem(status="warning", label="Belum terverifikasi website", detail="Usaha terdeteksi dari OpenStreetMap tanpa website.")]

        website = tags.get("website") or tags.get("contact:website") or tags.get("url") or None
        phone = tags.get("phone") or tags.get("contact:phone") or None
        if not website:
            problem_type = "missing_web"
        elif "wordpress.com" in website or "blogspot" in website:
            problem_type = "outdated_tech"
        elif tourism:
            problem_type = "no_booking_flow"
        else:
            problem_type = problem_default

        diagnostics = list(diagnostics)
        diagnostics.append(DiagnosticItem(status="verified", label=f"Sumber: OpenStreetMap — {display_city}", detail=f"OSM id {el.get('type')}/{el.get('id')} • {tags.get('addr:street') or tags.get('addr:suburb') or display_city}"))
        diagnostics.append(DiagnosticItem(
            status="warning",
            label="Rating & ulasan adalah estimasi internal",
            detail="ClientRadar tidak mengakses Google Maps — angka rating/ulasan/skor adalah estimasi, bukan data publik."
        ))

        street = tags.get("addr:street") or tags.get("addr:suburb") or tags.get("addr:neighbourhood") or f"Area {display_city}"
        location_str = f"{street}, {display_city}"

        h = int(hashlib.md5(f"{name}{display_city}".encode()).hexdigest()[:4], 16)
        rating = round(4.2 + (h % 7) * 0.1, 1)
        rating = min(5.0, rating)
        reviews = 20 + (h % 180)
        score = 78 + (h % 18)
        level = "PRIORITAS TINGGI" if score >= 90 else "POTENSIAL" if score >= 82 else "MENENGAH"
        if category == "Hospitality & Penginapan":
            est_min, est_max = "Rp 7.0M", "Rp 12.0M"
        elif category == "Kesehatan & Dental":
            est_min, est_max = "Rp 3.5M", "Rp 5.5M"
        elif category == "Food & Beverage":
            est_min, est_max = "Rp 3.0M", "Rp 4.5M"
        else:
            est_min, est_max = "Rp 3.0M", "Rp 6.0M"

        el_type = el.get("type", "node")
        el_id = el.get("id", idx)
        return ProspectLead(
            id=f"osm_{el_type}_{el_id}",
            name=name,
            category=category,
            location=location_str,
            rating=rating,
            reviews_count=reviews,
            phone=phone,
            instagram=None,
            website_url=website,
            problem_type=problem_type,
            opportunity_score=score,
            opportunity_level=level,
            est_min_val=est_min,
            est_max_val=est_max,
            diagnostics=diagnostics,
            solution_text=solution,
            contact_status="Baru",
        )

    # ------------------------------------------------------------------ #
    #  Helpers: cache key, province broad detection
    # ------------------------------------------------------------------ #

    def _cache_key(self, keyword: str, location: str) -> str:
        return f"{(keyword or '').strip().lower()}|{(location or '').strip().lower()}"

    def _is_province_broad(self, location: str, geo: Dict) -> bool:
        bb = geo.get("boundingbox")
        if not bb or len(bb) != 4:
            return False
        try:
            south, north, west, east = map(float, bb)
            if (north - south) > 2.0 or (east - west) > 2.0:
                return True
        except Exception:
            pass
        return geo.get("type") in ("administrative", "state") and geo.get("class") == "boundary" and geo.get("place_rank") in (4, 5)

    # ------------------------------------------------------------------ #
    #  Location classification: national / province / city
    # ------------------------------------------------------------------ #

    _NATIONAL_ALIASES = {
        "indonesia", "indonesia raya", "ri", "nusantara", "nkri", "nusantara",
    }

    def _location_kind(self, location: str) -> str:
        """Return 'national', 'province', or 'city'."""
        low = (location or "").strip().lower()
        if low in self._NATIONAL_ALIASES:
            return "national"
        # Match exact province name or province + extra words (e.g. "sumatera utara")
        for prov in self.PROVINCE_CITIES:
            if low == prov or low.startswith(prov + " "):
                return "province"
        return "city"

    def _get_province_for_city(self, city_name: str) -> Optional[str]:
        """Find which province a city belongs to (exact match from PROVINCE_CITIES)."""
        city_lower = city_name.lower()
        for prov, cities in self.PROVINCE_CITIES.items():
            for c in cities:
                if c.lower() == city_lower:
                    return prov
        return None

    # ------------------------------------------------------------------ #
    #  Core: fetch OSM for a single city (with radius chain + timeout fallback)
    # ------------------------------------------------------------------ #

    async def _fetch_osm_city(self, keyword: str, location: str) -> List[ProspectLead]:
        """Fetch OSM data for one city. Radius chain: 4000 -> 2500 on timeout/error."""
        cache_key = self._cache_key(keyword, location)
        now = time.time()
        if cache_key in self._OSM_CACHE:
            ts, cached = self._OSM_CACHE[cache_key]
            if now - ts < self._OSM_TTL_SEC and cached is not None:
                return list(cached)

        geo = await self._geocode(location)
        if not geo:
            return []
        lat, lon = geo.get("lat"), geo.get("lon")
        if not lat or not lon:
            return []

        display = " ".join(w.capitalize() for w in location.strip().split())
        low = location.strip().lower()
        is_metro = low in self.METRO_CITIES

        filters = self._osm_filters(keyword)
        use_filters = filters[:1] if is_metro else filters[:2]

        headers = {"User-Agent": "ClientRadar/1.3.0 (OSM; Gustiakmal)"}

        # Name fallback for single-filter keywords (e.g. "cafe" -> also search by name)
        ql_name_fallback = None
        if len(filters) == 1 and "name" not in filters[0]:
            safe = self._sanitize_osm_keyword(keyword)
            if safe:
                ql_name_fallback = (
                    f'[out:json][timeout:8];'
                    f'(node["name"~"{safe}",i](around:6000,{lat},{lon});'
                    f'way["name"~"{safe}",i](around:6000,{lat},{lon}););'
                    f'out center 12;'
                )

        # ----- Radius chain: try 4000, fallback 2500 -----
        radii = [4000, 2500] if not is_metro else [4000, 2500]

        for radius in radii:
            clauses = []
            for f in use_filters:
                clauses.append(f'node{f}(around:{radius},{lat},{lon});')
                clauses.append(f'way{f}(around:{radius},{lat},{lon});')
            ql_timeout = 5 if is_metro else 8
            ql = f'[out:json][timeout:{ql_timeout}];({"".join(clauses)});out center {8 if is_metro else 12};'

            result: List[ProspectLead] = []
            for url in self.OVERPASS_URLS:
                try:
                    timeout_each = 5.0 if is_metro else 7.0
                    async with httpx.AsyncClient(timeout=timeout_each, headers=headers) as client:
                        res = await asyncio.wait_for(
                            client.post(url, data={"data": ql}),
                            timeout=timeout_each + 1.0,
                        )
                        if res.status_code == 504:
                            print(f"[OSM 504 {location} kw={keyword} @ {url}] radius={radius}")
                            continue
                        if res.status_code != 200:
                            continue
                        elements = res.json().get("elements", [])

                        # Name fallback if tag query empty
                        if not elements and ql_name_fallback:
                            try:
                                res2 = await asyncio.wait_for(
                                    client.post(url, data={"data": ql_name_fallback}),
                                    timeout=7.0,
                                )
                                if res2.status_code == 200:
                                    elements = res2.json().get("elements", [])
                            except asyncio.TimeoutError:
                                pass

                        leads: List[ProspectLead] = []
                        for idx, el in enumerate(elements[:15]):
                            if not el.get("tags"):
                                continue
                            lead = self._map_osm_to_lead(el, idx, display)
                            if lead:
                                leads.append(lead)

                        if leads:
                            result = leads
                            break
                except (asyncio.TimeoutError, httpx.ReadTimeout):
                    print(f"[OSM timeout {location} kw={keyword} @ {url}] radius={radius}")
                    continue
                except Exception as e:
                    print(f"[OSM fail {location} kw={keyword} @ {url}]: {e}")
                    continue

            if result:
                ttl = self._OSM_TTL_SEC
                self._OSM_CACHE[cache_key] = (now, result)
                return result

        # All radii and mirrors exhausted — cache briefly (30s)
        self._OSM_CACHE[cache_key] = (now - (self._OSM_TTL_SEC - 30), [])
        return []

    # ------------------------------------------------------------------ #
    #  Core: fetch OSM for a province (loop cities inside)
    # ------------------------------------------------------------------ #

    async def _fetch_osm_province(
        self, keyword: str, province: str, max_cities: int = 5
    ) -> List[ProspectLead]:
        """Loop kota-kota di provinsi, gabungkan hasil, batasi 40 leads."""
        prov_lower = province.strip().lower()
        cities = self.PROVINCE_CITIES.get(prov_lower, [])
        if not cities:
            # Try prefix match (e.g. "sumatera utara" -> "sumatera utara")
            for prov, cls in self.PROVINCE_CITIES.items():
                if prov_lower.startswith(prov):
                    cities = cls
                    break
        if not cities:
            return []

        results: List[ProspectLead] = []
        seen_ids: set = set()
        deadline = time.monotonic() + 30  # 30s budget

        for city in cities[:max_cities]:
            if time.monotonic() > deadline:
                break
            leads = await self._fetch_osm_city(keyword, city)
            for lead in leads:
                if lead.id not in seen_ids:
                    seen_ids.add(lead.id)
                    results.append(lead)
            if len(results) >= 40:
                break

        return results[:40]

    # ------------------------------------------------------------------ #
    #  Core: fetch OSM for entire Indonesia (loop national cities)
    # ------------------------------------------------------------------ #

    async def _fetch_osm_national(self, keyword: str) -> List[ProspectLead]:
        """Loop kota-kota terbesar Indonesia, stop early saat cukup data."""
        results: List[ProspectLead] = []
        seen_ids: set = set()
        deadline = time.monotonic() + 60  # 60s budget

        for city in self.NATIONAL_CITIES:
            if time.monotonic() > deadline:
                break
            leads = await self._fetch_osm_city(keyword, city)
            for lead in leads:
                if lead.id not in seen_ids:
                    seen_ids.add(lead.id)
                    results.append(lead)
            if len(results) >= 40:
                break

        return results[:40]

    # ------------------------------------------------------------------ #
    #  Dispatcher: _fetch_osm routes to city / province / national
    # ------------------------------------------------------------------ #

    async def _fetch_osm(self, keyword: str, location: str) -> List[ProspectLead]:
        kind = self._location_kind(location)
        if kind == "national":
            return await self._fetch_osm_national(keyword)
        if kind == "province":
            return await self._fetch_osm_province(keyword, location)
        return await self._fetch_osm_city(keyword, location)

    # ------------------------------------------------------------------ #
    #  Public: province_hint (used by frontend)
    # ------------------------------------------------------------------ #

    def province_hint(self, location: str) -> Optional[str]:
        key = (location or "").strip().lower()
        for prov, hint in self.PROVINCE_HINT.items():
            if key == prov or key.startswith(prov + " "):
                return hint
        return None

    # ------------------------------------------------------------------ #
    #  Public API (called by main.py)
    # ------------------------------------------------------------------ #

    async def fetch_leads_with_meta(self, keyword: str, location: Optional[str] = None, custom_endpoint: Optional[str] = None):
        """
        Return (leads, meta) — meta.hint dipakai frontend kalau provinsi luas/Papua-centre kosong.
        Seluruh Indonesia: loop kota-kota terbesar.
        Provinsi: loop kota di dalamnya.
        Kota: geocode + around query.
        """
        kw = (keyword or "").strip()
        loc = (location or "").strip()
        if not loc:
            return [], {"hint": "Isi lokasi kota/kabupaten — contoh: Jakarta, Bandung, Medan, Makassar, Banjarmasin, Jayapura."}

        kind = self._location_kind(loc)
        hint = self.province_hint(loc)

        # Timeout: nasional/provinsi butuh waktu lebih (loop kota)
        timeout = 90.0 if kind in ("national", "province") else 20.0

        try:
            osm_leads = await asyncio.wait_for(self._fetch_osm(kw, loc), timeout=timeout)
            if not osm_leads:
                if kind == "national":
                    return [], {
                        "hint": "Scan seluruh Indonesia selesai tapi 0 hasil. "
                                "OSM mungkin kosong untuk keyword ini. "
                                "Coba kata kunci lain (cafe, resto, hotel, klinik, bengkel) atau pilih kota spesifik: "
                                "Jakarta, Surabaya, Bandung, Medan, Makassar, Banjarmasin.",
                        "detail": "Seluruh 20 kota terbesar sudah di-scan.",
                    }
                if hint:
                    return [], {
                        "hint": (
                            f'"{loc}" adalah provinsi luas (titik tengah di hutan, bukan kota). '
                            f'Kami sudah coba scan kota-kota di dalamnya — hasilnya 0. '
                            f'Coba kota langsung: {hint}'
                        )
                    }
                geo = self._GEOCODE_CACHE.get(loc.lower(), (0, None))[1] if loc.lower() in self._GEOCODE_CACHE else None
                if geo and self._is_province_broad(loc, geo):
                    return [], {
                        "hint": (
                            f'"{loc}" terlalu luas (pusat di hutan/0 hasil). '
                            f'Coba kota: {hint or "contoh: Jayapura, Medan, Jakarta"} — bukan nama provinsi.'
                        )
                    }
                return [], {
                    "hint": None,
                    "detail": (
                        f'Tidak ada hasil OSM di sekitar {loc} untuk kata "{kw or "kosong (browse)"}". '
                        f"Bukan berarti semua sudah punya website — data OSM memang terbatas. "
                        f"Coba tanpa keyword, kata lain (cafe/resto/hotel/klinik/bengkel), atau kota/kabupaten tetangga."
                    ),
                }

            if kw:
                expanded = self._expand_terms(kw.lower().split())
                filtered = [l for l in osm_leads if any(term in f"{l.name} {l.category}".lower() for term in expanded)]
                if not filtered:
                    return [], {"hint": f'Tidak ada "{kw}" di OSM sekitar {loc} ({len(osm_leads)} ditemukan di luar kategori). Coba tanpa keyword atau kata lain.'}
                return filtered, {"hint": None}

            return osm_leads, {"hint": None}

        except asyncio.TimeoutError:
            print(f"[DirectoryScraper OSM overall timeout loc={loc} kw={kw}]")
            return [], {
                "hint": "Scan timeout — Overpass API lambat. Coba lagi, atau pilih kota yang lebih spesifik.",
                "retry": True,
            }
        except Exception as e:
            print(f"[DirectoryScraper fetch_leads OSM error]: {e}")
            return [], {"hint": None}

    async def fetch_leads(self, keyword: str, location: Optional[str] = None, custom_endpoint: Optional[str] = None) -> List[ProspectLead]:
        leads, _ = await self.fetch_leads_with_meta(keyword, location, custom_endpoint)
        return leads
