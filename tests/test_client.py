from __future__ import annotations

import time

import httpx
import pytest

from digitalocean_sdk import (
    AuthenticationError,
    DigitalOcean,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    load_settings,
)
from digitalocean_sdk.errors import retry_after_from


def test_missing_token(monkeypatch, tmp_path):
    monkeypatch.delenv("DIGITALOCEAN_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(AuthenticationError):
        DigitalOcean()


def test_token_from_env_and_file(monkeypatch, tmp_path):
    monkeypatch.setenv("DIGITALOCEAN_TOKEN", "from-env")
    assert DigitalOcean()._token == "from-env"
    monkeypatch.delenv("DIGITALOCEAN_TOKEN")
    path = tmp_path / "do.json"
    path.write_text('{"token": "from-file", "default_ttl": 300}')
    client = DigitalOcean(config_file=str(path))
    assert (client._token, client.settings.default_ttl) == ("from-file", 300)


def test_endpoint_override(monkeypatch):
    monkeypatch.setenv("DIGITALOCEAN_ENDPOINTS__RECORDS", "/custom/{domain}/r")
    settings = load_settings(token="t")
    assert settings.path("records", domain="example.com") == "/custom/example.com/r"
    assert settings.path("record", domain="example.com", record_id=5) == "/v2/domains/example.com/records/5"


def test_errors_carry_details(do, api):
    api.queue(422, {"id": "unprocessable_entity", "message": "Name is invalid", "request_id": "req-1"})
    with pytest.raises(ValidationError) as info:
        do.dns.get("example.com", 1)
    assert (info.value.code, info.value.request_id, info.value.status_code) == ("unprocessable_entity", "req-1", 422)
    assert "req-1" in str(info.value)
    api.queue(404, {"id": "not_found", "message": "missing"})
    with pytest.raises(NotFoundError):
        do.domains.get("example.com")


def test_rate_limit_is_retried(do, api):
    api.queue(429, {"id": "too_many_requests", "message": "slow down"}, {"ratelimit-reset": str(int(time.time()) + 1)})
    api.queue(200, {"domain": {"name": "example.com"}})
    assert do.domains.get("example.com").name == "example.com"
    assert len(api.requests) == 2


def test_rate_limit_gives_up(do, api):
    for _ in range(3):
        api.queue(429, {"id": "too_many_requests", "message": "slow down"}, {"Retry-After": "1"})
    with pytest.raises(RateLimitError) as info:
        do.domains.get("example.com")
    assert info.value.retry_after == 1.0


def test_retry_after_parsing():
    response = httpx.Response(429, headers={"ratelimit-reset": "1000"})
    assert retry_after_from(response, now=990) == 10
    assert retry_after_from(httpx.Response(429, headers={"Retry-After": "3"})) == 3
    assert retry_after_from(httpx.Response(429)) is None


def test_server_errors_retry_only_idempotent(do, api):
    api.queue(503)
    api.queue(200, {"domain": {"name": "example.com"}})
    do.domains.get("example.com")
    assert len(api.requests) == 2

    api.queue(503)
    with pytest.raises(ServerError):
        do.domains.create("example.com")
    assert api.requests[-1].method == "POST"
    assert len(api.requests) == 3


def test_connection_errors(api):
    def boom(request):
        raise httpx.ConnectError("down")

    client = DigitalOcean("t", http_client=httpx.Client(transport=httpx.MockTransport(boom)), max_retries=0)
    from digitalocean_sdk import APIConnectionError

    with pytest.raises(APIConnectionError):
        client.domains.list()


def test_raw_request(do, api):
    api.queue(200, {"droplets": []})
    assert do.request("get", "/v2/droplets", params={"per_page": 5}) == {"droplets": []}
    assert api.last.url.params["per_page"] == "5"
    api.queue(404, {"id": "not_found", "message": "x"})
    assert do.request("DELETE", "/v2/droplets/1", missing_ok=True) is None
