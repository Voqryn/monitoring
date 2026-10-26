"""Bounded Network API adapter for the domain-watch worker."""
from urllib.parse import urlsplit
import httpx
from voqryn_monitoring.domain_watch import RegistrationStatus


def make_checker(api_base: str, *, transport: httpx.BaseTransport | None = None):
    parsed = urlsplit(api_base)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise ValueError("API base must be an origin without credentials, path or query")
    if parsed.scheme != "https" and parsed.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Remote API must use HTTPS")
    origin = api_base.rstrip("/")

    def check(domain: str) -> RegistrationStatus:
        # Domain is encoded as a query parameter by httpx, never a caller-provided URL.
        with httpx.Client(timeout=httpx.Timeout(6.0, connect=2.0), follow_redirects=False, trust_env=False, transport=transport) as client:
            response = client.get(origin + "/v1/domain/check", params={"domain": domain}, headers={"Accept": "application/json"})
            response.raise_for_status()
            if len(response.content) > 16_384:
                raise ValueError("Oversized Network API response")
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Invalid API response")
            return RegistrationStatus(payload["status"])

    return check
