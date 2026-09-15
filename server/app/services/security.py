"""Security helpers: SSRF guard + in-memory rate limiter.

Dipakai oleh audit.py (audit URL arbitrer) dan custom.py (endpoint kustom)
untuk mencegah server mem-fetch alamat internal (localhost, private,
link-local, metadata cloud) — API7:2023 SSRF / WSTG-INJT-19 / CWE-918.
"""
import ipaddress
import socket
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional
from urllib.parse import urlparse

# Jaringan yang tidak boleh di-fetch server-side.
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),     # CGNAT
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("169.254.0.0/16"),    # link-local / metadata cloud
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),     # benchmark
    ipaddress.ip_network("224.0.0.0/4"),       # multicast
    ipaddress.ip_network("240.0.0.0/4"),       # reserved
    ipaddress.ip_network("::1/128"),           # loopback v6
    ipaddress.ip_network("fc00::/7"),          # ULA
    ipaddress.ip_network("fe80::/10"),         # link-local v6
    ipaddress.ip_network("ff00::/8"),          # multicast v6
]


def _is_blocked_ip(ip_str: str) -> bool:
    """True jika IP termasuk jaringan terlarang (atau tidak valid)."""
    try:
        ip = ipaddress.ip_address(ip_str.split("%")[0])
    except ValueError:
        return True
    return any(ip in net for net in BLOCKED_NETWORKS)


def resolve_host_ips(hostname: str) -> set:
    """Resolve hostname ke semua IP (IPv4 + IPv6). Kosong jika gagal."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, OSError):
        return set()
    return {info[4][0] for info in infos}


def validate_ssrf_url(url: str) -> Optional[str]:
    """Return pesan error jika URL tidak aman di-fetch server-side, else None.

    Memeriksa: skema http/https, hostname valid, dan semua IP hasil resolve
    tidak termasuk jaringan internal/terlarang.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "URL harus http atau https"
    hostname = parsed.hostname
    if not hostname:
        return "URL tidak valid"

    # Hostname berupa IP literal — cek langsung tanpa DNS.
    try:
        ip = ipaddress.ip_address(hostname)
        if _is_blocked_ip(str(ip)):
            return "Target tidak diizinkan (alamat internal)"
        return None
    except ValueError:
        pass

    # Hostname domain — resolve dan cek semua IP (anti DNS rebinding sederhana).
    ips = resolve_host_ips(hostname)
    if not ips:
        return "Domain tidak dapat di-resolve"
    for ip in ips:
        if _is_blocked_ip(ip):
            return "Target tidak diizinkan (alamat internal)"
    return None


class RateLimiter:
    """Sliding-window rate limiter in-memory per key (mis. client IP)."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)