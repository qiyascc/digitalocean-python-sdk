# digitalocean-python-sdk

A small, typed Python client for the DigitalOcean Domains and DNS API. It works with both sync and async code, waits and retries when DigitalOcean rate limits you, and returns plain dataclasses, not raw JSON.

```python
from digitalocean_sdk import DigitalOcean

with DigitalOcean("DIGITALOCEAN_TOKEN") as do:
    do.dns.point("example.com", "shop", "203.0.113.10")
```

That call makes `shop.example.com` resolve to `203.0.113.10`. If the record already exists it is updated, if it is missing it is created, and extra `A` records with the same name are removed.

## Install

```bash
pip install git+https://github.com/qiyascc/digitalocean-python-sdk.git
```

Requires Python 3.10 or newer. Dependencies: [httpx](https://www.python-httpx.org/), [goodconf](https://github.com/lincolnloop/goodconf), pydantic and PyYAML.

The import name is `digitalocean_sdk`, so it can live next to the older `python-digitalocean` package without clashing.

## Configuration

Settings are loaded with [goodconf](https://github.com/lincolnloop/goodconf), so you can configure the client from code, from environment variables or from a config file. Values passed in code win over the environment, and the environment wins over the file.

Create a personal access token at [cloud.digitalocean.com/account/api/tokens](https://cloud.digitalocean.com/account/api/tokens). For DNS work the token needs the `domain` scopes (read, create, update, delete). Then pick whichever option suits you:

```python
do = DigitalOcean("dop_v1_...")
```

```bash
export DIGITALOCEAN_TOKEN=dop_v1_...
```

```toml
token = "dop_v1_..."
timeout = 15
default_ttl = 1800
```

`DIGITALOCEAN_TOKEN` is the same variable `doctl` and Terraform use, so an existing setup usually works as is.

With no arguments, the client looks for `digitalocean.toml`, `digitalocean.yaml`, `digitalocean.yml` or `digitalocean.json` in the working directory. To load a file from somewhere else, set `DIGITALOCEAN_CONFIG=/path/to/file`, or pass `config_file=` to the client. YAML files need the `yaml` extra, and TOML files on Python 3.10 need the `toml` extra:

```bash
pip install "digitalocean-python-sdk[yaml] @ git+https://github.com/qiyascc/digitalocean-python-sdk.git"
```

| Setting | Env variable | Default |
| --- | --- | --- |
| `token` | `DIGITALOCEAN_TOKEN` | |
| `base_url` | `DIGITALOCEAN_BASE_URL` | `https://api.digitalocean.com` |
| `api_version` | `DIGITALOCEAN_API_VERSION` | `v2` |
| `endpoints.*` | `DIGITALOCEAN_ENDPOINTS__<NAME>` | see below |
| `timeout` | `DIGITALOCEAN_TIMEOUT` | `30` |
| `max_retries` | `DIGITALOCEAN_MAX_RETRIES` | `3` |
| `max_retry_wait` | `DIGITALOCEAN_MAX_RETRY_WAIT` | `60` |
| `backoff_base` | `DIGITALOCEAN_BACKOFF_BASE` | `0.5` |
| `backoff_cap` | `DIGITALOCEAN_BACKOFF_CAP` | `8` |
| `page_size` | `DIGITALOCEAN_PAGE_SIZE` | `200` (the API maximum) |
| `default_ttl` | `DIGITALOCEAN_DEFAULT_TTL` | `1800` |
| `user_agent` | `DIGITALOCEAN_USER_AGENT` | `digitalocean-python-sdk/{version}` |

Any setting can also be passed straight to the client, for example `DigitalOcean(timeout=10, max_retries=5)`. If you build settings yourself, hand them over with `settings=`:

```python
from digitalocean_sdk import DigitalOcean, load_settings

settings = load_settings("/etc/myapp/digitalocean.toml", default_ttl=300)
do = DigitalOcean(settings=settings)
```

### Endpoints

API paths are part of the settings too, so nothing is pinned in the code. Each one is a template relative to the base URL. `{version}` comes from `api_version`, and the other placeholders are filled in and URL encoded for each call.

| Name | Default |
| --- | --- |
| `account` | `/{version}/account` |
| `domains` | `/{version}/domains` |
| `domain` | `/{version}/domains/{domain}` |
| `records` | `/{version}/domains/{domain}/records` |
| `record` | `/{version}/domains/{domain}/records/{record_id}` |

```bash
export DIGITALOCEAN_ENDPOINTS__RECORDS="/{version}/domains/{domain}/records"
```

Check that the token works:

```python
do.account()
```

```python
Account(email='you@example.com', uuid='...', status='active', email_verified=True, droplet_limit=25, ...)
```

## Domains

DigitalOcean is not a registrar. A domain here is a zone you manage with DigitalOcean DNS: buy the name anywhere, then set its name servers to `ns1.digitalocean.com`, `ns2.digitalocean.com` and `ns3.digitalocean.com`.

```python
do.domains.create("example.com")
do.domains.create("example.com", ip_address="203.0.113.10")

for domain in do.domains.iter():
    print(domain.name, domain.ttl)

do.domains.list()
do.domains.get("example.com").zone_file
do.domains.exists("example.com")
do.domains.delete("example.com")
do.domains.delete("maybe-gone.com", missing_ok=True)
```

When `ip_address` is given, DigitalOcean creates an `A` record for the apex right away.

## DNS

Every DNS method takes the domain first. Record names are relative to the domain and the apex is `@`. You can also pass a full name like `www.example.com`, it is turned into `www` for you.

```python
from digitalocean_sdk import DigitalOcean, DNSRecord

do = DigitalOcean()

do.dns.list("example.com")
do.dns.list("example.com", "A")
do.dns.list("example.com", "A", "www")
do.dns.list("example.com", name="www")
do.dns.exists("example.com", "A", "shop")
do.dns.get("example.com", 28448433)
```

Filtering by type and name happens on DigitalOcean's side. Lists follow every page for you, and `iter()` does the same lazily. Each item is a `DNSRecord`:

```python
DNSRecord(type='A', name='www', data='203.0.113.10', ttl=1800, priority=None, port=None, weight=None, flags=None, tag=None, id=28448433)
```

### Creating and changing records

DigitalOcean identifies records by id. `create` and `add` return the new records with their ids filled in.

```python
record = do.dns.create("example.com", DNSRecord.a("api", "203.0.113.20"))

do.dns.add(
    "example.com",
    DNSRecord.txt("@", "google-site-verification=abc"),
    DNSRecord.mx("@", "mail.example.com", priority=10),
    DNSRecord.caa("@", "letsencrypt.org"),
    DNSRecord.srv("_sip._udp", "sip.example.com", port=5060),
)

do.dns.update("example.com", record, data="203.0.113.21", ttl=300)
do.dns.update("example.com", 28448433, name="api-v2")

record.ttl = 600
do.dns.update("example.com", record)

do.dns.delete("example.com", record)
do.dns.delete("example.com", 28448433, missing_ok=True)
do.dns.delete_all("example.com", "A", "old")
```

`update` with fields sends a `PATCH` and changes only those fields. `update` with just a record sends a `PUT` with the whole record.

Host names in `CNAME`, `MX`, `NS` and `SRV` records must be fully qualified with a trailing dot. The helpers add that dot for you, so `DNSRecord.cname("docs", "example.github.io")` is sent as `example.github.io.`. Use `@` to point at the apex itself.

### Replacing a set of records

`replace` makes one type and name hold exactly the values you pass. Matching records are kept, missing ones are created and the rest are deleted. Pass `ttl` to change it on every record in the set.

```python
do.dns.replace("example.com", "A", "www", ["203.0.113.10", "203.0.113.11"], ttl=600)
```

### Shortcuts

```python
do.dns.point("example.com", "shop", "203.0.113.10")
do.dns.point("example.com", "shop", "2001:db8::10")
do.dns.alias("example.com", "docs", "example.github.io")
do.dns.set_txt("example.com", "_acme-challenge", "token-value", ttl=60)
do.dns.unpoint("example.com", "shop")
```

`point` picks `A` or `AAAA` from the address you pass. `unpoint` deletes the matching records and returns how many it removed, so it is safe to call when nothing is there.

### Example: one subdomain per customer

```python
from digitalocean_sdk import DigitalOcean

SERVER_IP = "203.0.113.10"

def create_customer_site(slug: str) -> str:
    with DigitalOcean() as do:
        if do.dns.exists("example.com", "A", slug):
            raise ValueError(f"{slug}.example.com is already taken")
        do.dns.point("example.com", slug, SERVER_IP, ttl=300)
    return f"{slug}.example.com"
```

## Async

`AsyncDigitalOcean` has the same methods. Await them.

```python
import asyncio
from digitalocean_sdk import AsyncDigitalOcean

async def main():
    async with AsyncDigitalOcean() as do:
        records = await do.dns.list("example.com", "A")
        await do.dns.point("example.com", "shop", "203.0.113.10")
        async for domain in do.domains.iter():
            print(domain.name)

asyncio.run(main())
```

## Other endpoints

The SDK focuses on Domains and DNS, but the same authenticated client can call any other DigitalOcean endpoint, with the same retries and errors:

```python
droplets = do.request("GET", "/v2/droplets", params={"per_page": 50})
do.request("POST", "/v2/droplets/123/actions", json={"type": "reboot"})
```

## Errors

All exceptions inherit from `DigitalOceanError`.

| Exception | When |
| --- | --- |
| `ValidationError` | 400 or 422, the request body or parameters were rejected |
| `AuthenticationError` | 401, or no token was found |
| `PermissionDeniedError` | 403, often a token without the right scope |
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `RateLimitError` | 429 that is still failing after retries. Has `.retry_after` |
| `ServerError` | 5xx |
| `APIConnectionError` / `APITimeoutError` | the request never got an answer |

Status errors carry `status_code`, DigitalOcean's error `code` (for example `not_found` or `unprocessable_entity`), the `request_id` to quote to support, and the raw `response`.

```python
from digitalocean_sdk import ValidationError

try:
    do.dns.create("example.com", DNSRecord.cname("@", "elsewhere.com"))
except ValidationError as exc:
    print(exc.code, exc.message, exc.request_id)
```

## Retries and timeouts

DigitalOcean allows 5,000 requests per hour and 250 per minute. When it answers 429, the client waits until the `ratelimit-reset` time it sends and tries again, as long as that wait is under `max_retry_wait`. Server errors and dropped connections are retried with exponential backoff, but only for idempotent methods (`GET`, `PUT`, `DELETE`). A `POST` that creates a record is never sent twice.

```python
do = DigitalOcean(timeout=10, max_retries=5, max_retry_wait=30)
```

Set `max_retries=0` to turn retries off. To use proxies or a custom transport, pass your own `httpx.Client` or `httpx.AsyncClient` as `http_client=`.

## Messages

Every error and validation message the SDK produces is stored in `digitalocean_sdk/messages.yaml`, so none of them are hardcoded. You can replace some or all of them, for example to translate them:

```yaml
value:
  empty_name: Record adı boş ola bilməz
error:
  timeout: "Sorğu vaxtı bitdi: {error}"
```

```python
from digitalocean_sdk import messages

messages.use("messages.az.yaml")
messages.use({"value.empty_name": "Record adı boş ola bilməz"})
```

Unknown keys raise `KeyError`, which catches typos early. Call `messages.reset()` to go back to the defaults.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
```

The tests use `httpx.MockTransport`, so they never touch the real API.

## License

MIT
