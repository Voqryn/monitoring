import httpx
import pytest
from voqryn_monitoring.domain_watch import RegistrationStatus as S
from voqryn_monitoring.network_checker import make_checker


def test_api_status_mapping():
    def handler(request):
        assert request.url.path == "/v1/domain/check"
        assert request.url.params["domain"] == "example.com"
        return httpx.Response(200, json={"status": "possibly_available"})
    check = make_checker("http://127.0.0.1:8000", transport=httpx.MockTransport(handler))
    assert check("example.com") == S.POSSIBLY_AVAILABLE


def test_invalid_api_status_rejected():
    check = make_checker("https://api.example.com", transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"status": "available"})))
    with pytest.raises(ValueError):
        check("example.com")


def test_remote_plain_http_rejected():
    with pytest.raises(ValueError):
        make_checker("http://api.example.com")


def test_redirect_not_followed():
    check = make_checker("https://api.example.com", transport=httpx.MockTransport(lambda _: httpx.Response(302, headers={"Location": "http://127.0.0.1/"})))
    with pytest.raises(httpx.HTTPStatusError):
        check("example.com")
