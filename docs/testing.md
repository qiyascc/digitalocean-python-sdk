# Testing your code

Code that edits DNS should be tested without real DNS. The client accepts any `httpx` client, so you can plug in `httpx.MockTransport` and decide what "DigitalOcean" answers. The SDK's own tests work this way.

## A recorder fixture for pytest

```python
import json

import httpx
import pytest

from digitalocean_sdk import DigitalOcean


class Recorder:
    def __init__(self):
        self.requests = []
        self.responses = []

    def queue(self, status=200, body=None, headers=None):
        content = b"" if body is None else json.dumps(body).encode()
        self.responses.append(httpx.Response(status, content=content, headers=headers or {}))

    def __call__(self, request):
        self.requests.append(request)
        if not self.responses:
            return httpx.Response(200, content=b"{}")
        return self.responses.pop(0)

    @property
    def last(self):
        return self.requests[-1]

    def body(self, index=-1):
        return json.loads(self.requests[index].content)

    def calls(self):
        return [(r.method, r.url.path) for r in self.requests]


def record(id, type, name, data, ttl=1800):
    return {"id": id, "type": type, "name": name, "data": data, "ttl": ttl,
            "priority": None, "port": None, "weight": None, "flags": None, "tag": None}


def page(*records):
    return {"domain_records": list(records), "links": {}, "meta": {"total": len(records)}}


@pytest.fixture
def api():
    return Recorder()


@pytest.fixture
def do(api):
    http = httpx.Client(transport=httpx.MockTransport(api))
    client = DigitalOcean("token", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client
```

`record` and `page` build answers in DigitalOcean's shape. A page without `links.pages.next` is the last one. The `_wait_for` line makes retries instant in tests; it is internal, so keep it in test code.

## Example tests

The function under test:

```python
def create_customer_site(do, slug: str) -> str:
    if do.dns.exists("example.com", "A", slug):
        raise ValueError(f"{slug}.example.com is already taken")
    do.dns.point("example.com", slug, "203.0.113.10", ttl=300)
    return f"{slug}.example.com"
```

```python
def test_creates_the_record(do, api):
    api.queue(200, page())
    api.queue(200, page())
    api.queue(201, {"domain_record": record(7, "A", "acme", "203.0.113.10", 300)})

    assert create_customer_site(do, "acme") == "acme.example.com"

    assert api.calls()[-1] == ("POST", "/v2/domains/example.com/records")
    assert api.body() == {"type": "A", "name": "acme", "data": "203.0.113.10", "ttl": 300}
    assert api.requests[0].url.params["name"] == "acme.example.com"


def test_refuses_a_taken_name(do, api):
    api.queue(200, page(record(5, "A", "acme", "198.51.100.1")))

    with pytest.raises(ValueError):
        create_customer_site(do, "acme")
    assert len(api.requests) == 1
```

The first test queues two empty pages: one for `exists`, one for the read inside `point`. The last check shows that the name filter is sent to DigitalOcean as a full name.

## Testing error handling

```python
from digitalocean_sdk import DNSRecord, ValidationError


def test_shows_the_reason(do, api):
    api.queue(422, {"id": "unprocessable_entity", "message": "Name is invalid", "request_id": "r-1"})

    with pytest.raises(ValidationError) as caught:
        do.dns.create("example.com", DNSRecord.a("www", "203.0.113.10"))

    assert (caught.value.code, caught.value.request_id) == ("unprocessable_entity", "r-1")
```

## Async tests

```python
import httpx
import pytest

from digitalocean_sdk import AsyncDigitalOcean


@pytest.fixture
def ado(api):
    http = httpx.AsyncClient(transport=httpx.MockTransport(api))
    client = AsyncDigitalOcean("token", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client


@pytest.mark.asyncio
async def test_async_point(ado, api):
    api.queue(200, page())
    api.queue(201, {"domain_record": record(9, "A", "shop", "203.0.113.10")})
    result = await ado.dns.point("example.com", "shop", "203.0.113.10")
    assert result[0].id == 9
```
