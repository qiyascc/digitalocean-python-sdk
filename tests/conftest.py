from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from digitalocean_sdk import AsyncDigitalOcean, DigitalOcean


class Recorder:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.responses: list[httpx.Response] = []

    def queue(self, status: int = 200, body: Any = None, headers: dict[str, str] | None = None) -> None:
        content = b"" if body is None else json.dumps(body).encode()
        self.responses.append(httpx.Response(status, content=content, headers=headers or {}))

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if not self.responses:
            return httpx.Response(200, content=b"{}")
        return self.responses.pop(0)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def body(self, index: int = -1) -> Any:
        return json.loads(self.requests[index].content)

    def calls(self) -> list[tuple[str, str]]:
        return [(r.method, r.url.path) for r in self.requests]


@pytest.fixture
def api() -> Recorder:
    return Recorder()


@pytest.fixture
def do(api: Recorder) -> DigitalOcean:
    http = httpx.Client(transport=httpx.MockTransport(api))
    client = DigitalOcean("token", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client


@pytest.fixture
def ado(api: Recorder) -> AsyncDigitalOcean:
    http = httpx.AsyncClient(transport=httpx.MockTransport(api))
    client = AsyncDigitalOcean("token", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client


def record(id: int, type: str, name: str, data: str, ttl: int = 1800, **extra: Any) -> dict[str, Any]:
    base = {"id": id, "type": type, "name": name, "data": data, "priority": None, "port": None, "ttl": ttl,
            "weight": None, "flags": None, "tag": None}
    base.update(extra)
    return base


def records(*items: dict[str, Any], next_page: bool = False) -> dict[str, Any]:
    next_url = "https://api.digitalocean.com/v2/domains/example.com/records?page=2"
    links = {"pages": {"next": next_url}} if next_page else {}
    return {"domain_records": list(items), "links": links, "meta": {"total": len(items)}}
