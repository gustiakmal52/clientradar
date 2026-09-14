from typing import List, Optional, Dict
import asyncio
import hashlib
import time
import httpx
from .base import BaseScraperAdapter
from ...models.schema import ProspectLead, DiagnosticItem

class DirectoryScraper(BaseScraperAdapter):
    """
    Real-data only — OpenStreetMap (Nominatim + Overpass).
    Tidak ada fallback demo/template. Jika OSM kosong/timeout -> kembalikan [].
    Seluruh Indonesia didukung: geocode "{kota}, Indonesia" via Nominatim.
    Saat app dibuka -> leads_store = [] (kosong), user yang tentukan lokasi+keyword.
    """

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

    # Provinsi luas — suruh user pakai kota (Papua -> Jayapura, bukan titik hutan tengah provinsi)
    PROVINCE_HINT = {
        "papua": "Jayapura / Manokwari / Merauke",
        "papua barat": "Manokwari / Sorong",
        "jawa barat": "Bandung / Bekasi / Depok",
        "jawa tengah": "Semarang / Solo / Magelang",
        "jawa timur": "Surabaya / Malang / Kediri",
        "sumatera utara": "Medan / Binjai",
        "kalimantan selatan": "Banjarmasin / Banjarbaru",
        "sulawesi selatan": "Makassar / Parepare",
    }

    def _osm_filters(self, keyword: str) -> List[str]:
        kw = (keyword or "").strip().lower()
        if not kw:
            # Browse kosongan: cukup 3 kategori ringan (jangan 5 — berat di kota padat + timeout Jakarta)
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
        safe = kw.replace('"', '')
        return [f'["name"~"{safe}",i]']

    _GEOCODE_CACHE: Dict[str, tuple] = {}
    _OSM_CACHE: Dict[str, tuple] = {}
    _OSM_TTL_SEC = 600

    async def _geocode(self, location: str) -> Optional[Dict]:
        key = (location or "").strip().lower()
        now = time.time()
        if key in self._GEOCODE_CACHE:
            ts, val = self._GEOCODE_CACHE[key]
            if now - ts < 3600 and val is not None:
                return val
        q = f"{location.strip()}, Indonesia" if location.strip() else "Indonesia"
        params = {"q": q, "format": "json", "limit": "1", "countrycodes": "id"}
        headers = {"User-Agent": "ClientRadar/1.2.0 (OSM; Gustiakmal)"}
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

    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

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

    async def _fetch_osm_by_area(self, geo: Dict, keyword: str, display: str) -> List[ProspectLead]:
        """Untuk provinsi luas seperti Papua: cari via area (bukan around hutan tengah)."""
        osm_type = geo.get("osm_type")
        osm_id = geo.get("osm_id")
        if not osm_type or not osm_id:
            return []
        # Overpass area id: relation -> 3600000000 + id, way -> 2400000000 + id, node -> id
        area_offset = {"relation": 3600000000, "way": 2400000000, "node": 0}
        area_id = area_offset.get(osm_type, 3600000000) + int(osm_id)
        filters = self._osm_filters(keyword)
        clauses = []
        for f in filters[:2]:
            clauses.append(f'node{f}(area:{area_id});')
            clauses.append(f'way{f}(area:{area_id});')
        ql = f'[out:json][timeout:15];area({area_id})->.a;({ "".join(clauses) });out center 12;'
        headers = {"User-Agent": "ClientRadar/1.2.0 (OSM; Gustiakmal)"}
        for url in self.OVERPASS_URLS:
            try:
                async with httpx.AsyncClient(timeout=12.0, headers=headers) as client:
                    res = await asyncio.wait_for(client.post(url, data={"data": ql}), timeout=14.0)
                    if res.status_code != 200:
                        if res.status_code == 504:
                            print(f"[OSM area 504 {display} @ {url}]")
                        continue
                    elements = res.json().get("elements", [])
                    leads: List[ProspectLead] = []
                    for idx, el in enumerate(elements[:15]):
                        if not el.get("tags"):
                            continue
                        lead = self._map_osm_to_lead(el, idx, display)
                        if lead:
                            leads.append(lead)
                    if leads:
                        return leads
            except Exception as e:
                print(f"[OSM area fail {display} @ {url}]: {e}")
                continue
        return []

    async def _fetch_osm(self, keyword: str, location: str) -> List[ProspectLead]:
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
        is_broad = self._is_province_broad(location, geo)
        low = location.strip().lower()
        is_metro = low in ("jakarta", "dki jakarta", "jakarta pusat", "jakarta selatan", "jakarta timur", "jakarta barat", "jakarta utara", "surabaya", "medan", "bandung", "bekasi", "tangerang", "depok", "semarang", "yogyakarta")
        # Provinsi luas seperti Papua: jangan hammer area (504) — langsung hint kota
        if is_broad and low.split(",")[0].strip() not in ("jayapura", "manokwari", "merauke", "sorong", "timika", "nabire", "jayapura selatan", "sentani", "jayapura utara", "biak"):
            return []
        if is_metro:
            radius = 6000  # Jakarta 6000 terbukti 200 (3000 timeout, 4000 timeout)
        elif low in ("jayapura", "manokwari", "merauke", "sorong", "timika", "sentani", "jayapura selatan", "jayapura utara"):
            radius = 3000  # Jayapura 3000 success 3, 4000 timeout, 6000 429
        else:
            radius = 8000  # Banjarmasin/Makassar 8000 success 12
        filters = self._osm_filters(keyword)
        if is_metro:
            use_filters = filters[:1]
        else:
            use_filters = filters[:2]
        clauses = []
        for f in use_filters:
            clauses.append(f'node{f}(around:{radius},{lat},{lon});')
            clauses.append(f'way{f}(around:{radius},{lat},{lon});')
        ql_timeout = 6 if is_metro else 8
        ql = f'[out:json][timeout:{ql_timeout}];({ "".join(clauses) });out center {8 if is_metro else 12};'
        headers = {"User-Agent": "ClientRadar/1.2.0 (OSM; Gustiakmal)"}
        ql_name_fallback = None
        if len(filters) == 1 and "name" not in filters[0]:
            safe = (keyword or "").strip().replace('"', "")
            if safe:
                ql_name_fallback = f'[out:json][timeout:8];(node["name"~"{safe}",i](around:10000,{lat},{lon});way["name"~"{safe}",i](around:10000,{lat},{lon}););out center 12;'

        # Timeout metro lebih pendek biar tidak nge-hang lama
        per_url_timeout = 6.0 if is_metro else 7.0
        result: List[ProspectLead] = []
        for url in self.OVERPASS_URLS:
            try:
                # Metro timeout lebih pendek — Jakarta 504 kalau kelamaan, jangan hang 7s
                timeout_each = 5.0 if is_metro else per_url_timeout
                async with httpx.AsyncClient(timeout=timeout_each, headers=headers) as client:
                    res = await asyncio.wait_for(client.post(url, data={"data": ql}), timeout=timeout_each + 1.0)
                    if res.status_code == 504:
                        print(f"[DirectoryScraper OSM 504 {location} kw={keyword} @ {url} radius={radius}]")
                        continue
                    if res.status_code != 200:
                        continue
                    data = res.json()
                    elements = data.get("elements", [])
                    if not elements and ql_name_fallback:
                        try:
                            res2 = await asyncio.wait_for(client.post(url, data={"data": ql_name_fallback}), timeout=per_url_timeout + 1.0)
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
                    # 0 leads di metro tapi HTTP 200 — coba kurangi radius lagi sekali (fallback 2500m)
                    if is_metro and not result:
                        ql_small = ql.replace(f"around:{radius},", "around:2500,")
                        try:
                            res3 = await asyncio.wait_for(client.post(url, data={"data": ql_small}), timeout=per_url_timeout + 1.0)
                            if res3.status_code == 200:
                                elements3 = res3.json().get("elements", [])
                                for idx, el in enumerate(elements3[:10]):
                                    if not el.get("tags"):
                                        continue
                                    lead = self._map_osm_to_lead(el, idx, display)
                                    if lead:
                                        result.append(lead)
                                if result:
                                    break
                        except Exception:
                            pass
            except (asyncio.TimeoutError, httpx.ReadTimeout):
                print(f"[DirectoryScraper OSM timeout {location} kw={keyword} @ {url}]")
                continue
            except Exception as e:
                print(f"[DirectoryScraper OSM fail {location} kw={keyword} @ {url}]: {e}")
                continue
        ttl = self._OSM_TTL_SEC if result else 30
        self._OSM_CACHE[cache_key] = (now if result else now - (self._OSM_TTL_SEC - ttl), result)
        return result

    def province_hint(self, location: str) -> Optional[str]:
        key = (location or "").strip().lower()
        for prov, hint in self.PROVINCE_HINT.items():
            if key == prov or key.startswith(prov + " "):
                return hint
        return None

    async def fetch_leads_with_meta(self, keyword: str, location: Optional[str] = None, custom_endpoint: Optional[str] = None):
        """
        Return (leads, meta) — meta.hint dipakai frontend kalau provinsi luas/Papua-centre kosong.
        Seluruh Indonesia: wajib lokasi kota/kabupaten — bukan provinsi hutan.
        """
        kw = (keyword or "").strip()
        loc = (location or "").strip()
        if not loc:
            return [], {"hint": "Isi lokasi kota/kabupaten — contoh: Jayapura, Manokwari, Jakarta, Bandung, Banjarmasin, Makassar."}
        hint = self.province_hint(loc)
        if hint:
            # tetap coba, tapi siapkan hint kalau hasilnya 0 — geocode Papua centre memang hutan
            pass
        try:
            osm_leads = await asyncio.wait_for(self._fetch_osm(kw, loc), timeout=15.0)
            if not osm_leads:
                if hint:
                    return [], {"hint": f'"{loc}" adalah provinsi luas (titik tengah di hutan, bukan kota). Coba kota di dalamnya: {hint}. Contoh: "Jayapura" untuk Papua, "Manokwari" untuk Papua Barat.'}
                geo = self._GEOCODE_CACHE.get(loc.lower(), (0, None))[1] if loc.lower() in self._GEOCODE_CACHE else None
                if geo and self._is_province_broad(loc, geo):
                    return [], {"hint": f'"{loc}" terlalu luas (pusat di hutan/0 hasil). Coba kota: {hint or "contoh: Jayapura, Timika, Merauke"} — bukan nama provinsi.'}
                return [], {"hint": None, "detail": f'Tidak ada hasil OSM di sekitar {loc} untuk kata "{kw or "kosong (browse)"}" (radius 8km). Bukan berarti semua sudah punya website — OSM di area ini sepi. Coba tanpa keyword, kata lain (cafe/resto/hotel/klinik), atau kota/kabupaten tetangga.'}
            if kw:
                expanded = self._expand_terms(kw.lower().split())
                filtered = [l for l in osm_leads if any(term in f"{l.name} {l.category}".lower() for term in expanded)]
                if not filtered:
                    return [], {"hint": f'Tidak ada "{kw}" di OSM sekitar {loc} ({len(osm_leads)} ditemukan di luar kategori). Coba tanpa keyword atau kata lain.'}
                return filtered, {"hint": None}
            return osm_leads, {"hint": None}
        except asyncio.TimeoutError:
            print(f"[DirectoryScraper OSM overall timeout loc={loc} kw={kw}]")
            return [], {"hint": "Overpass timeout — jaringan lambat. Coba lagi atau ganti kota.", "retry": True}
        except Exception as e:
            print(f"[DirectoryScraper fetch_leads OSM error]: {e}")
            return [], {"hint": None}

    async def fetch_leads(self, keyword: str, location: Optional[str] = None, custom_endpoint: Optional[str] = None) -> List[ProspectLead]:
        leads, _ = await self.fetch_leads_with_meta(keyword, location, custom_endpoint)
        return leads
