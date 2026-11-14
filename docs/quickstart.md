# Quickstart

This page builds one small script step by step: it makes sure a zone exists, reads its records, and points a subdomain at a server. It assumes you have [installed the package](installation.md) and [created a token](credentials.md).

DigitalOcean is not a registrar. A "domain" here is a DNS zone that DigitalOcean serves. You buy the name anywhere, then set its name servers to `ns1.digitalocean.com`, `ns2.digitalocean.com` and `ns3.digitalocean.com` at your registrar.

## 1. Give the SDK your token

::::{tab-set}

:::{tab-item} Linux and macOS
```bash
export DIGITALOCEAN_TOKEN=dop_v1_your-token
```
:::

:::{tab-item} Windows (CMD)
```bat
set DIGITALOCEAN_TOKEN=dop_v1_your-token
```
:::
::::

With the variable set, `DigitalOcean()` needs no arguments.

## 2. Make sure the zone exists

Create `first.py`:

```python
from digitalocean_sdk import DigitalOcean

with DigitalOcean() as do:
    if not do.domains.exists("example.com"):
        do.domains.create("example.com")
        print("Created the zone for example.com")

    for domain in do.domains.iter():
        print(domain.name, domain.ttl)
```

```bash
python first.py
```

```text
Created the zone for example.com
example.com 1800
```

What happens here:

- `DigitalOcean()` reads the settings and the token. It does not send a request yet.
- `with` closes the connection pool when the block ends.
- `domains.exists` asks for the zone and treats a 404 as `False`.
- `domains.create` adds the zone. DigitalOcean fills in its own `NS` and `SOA` records.
- `domains.iter` walks through every zone, page by page.

## 3. Read the records

Add inside the `with` block:

```python
    for record in do.dns.list("example.com"):
        print(record.id, record.type, record.name, record.data, record.ttl)
```

```text
3352896 NS @ ns1.digitalocean.com 1800
3352897 NS @ ns2.digitalocean.com 1800
3352898 NS @ ns3.digitalocean.com 1800
```

Every record is a {py:class}`~digitalocean_sdk.DNSRecord` with an `id`. DigitalOcean identifies records by that id, which matters when you update or delete one.

To narrow the list, pass a type, a name or both. DigitalOcean does the filtering:

```python
do.dns.list("example.com", "A")
do.dns.list("example.com", "A", "www")
do.dns.list("example.com", name="www")
```

## 4. Point a subdomain at a server

```python
    records = do.dns.point("example.com", "shop", "203.0.113.10", ttl=300)
    print(records)
```

```text
[DNSRecord(type='A', name='shop', data='203.0.113.10', ttl=300, priority=None, port=None, weight=None, flags=None, tag=None, id=3352899)]
```

`point` picks `A` for an IPv4 address and `AAAA` for IPv6, then makes the set match: if `shop` has no `A` record it creates one, if it has one with that address it keeps it (and updates the TTL if you passed a different one), and any other `A` records of `shop` are deleted. It returns the records now in the set. Running it twice changes nothing the second time.

Check from your machine once the name servers point at DigitalOcean:

```bash
nslookup shop.example.com ns1.digitalocean.com
```

## 5. Handle errors

```python
from digitalocean_sdk import DigitalOcean, DigitalOceanError, NotFoundError, PermissionDeniedError

try:
    with DigitalOcean() as do:
        do.dns.point("example.com", "shop", "203.0.113.10")
except NotFoundError:
    print("There is no zone for example.com in this account")
except PermissionDeniedError:
    print("The token is missing the domain scopes")
except DigitalOceanError as exc:
    print("DigitalOcean said:", exc)
```

Every exception the SDK raises inherits from {py:class}`~digitalocean_sdk.DigitalOceanError`. [](errors.md) lists them all.

## The same script, async

```python
import asyncio

from digitalocean_sdk import AsyncDigitalOcean


async def main() -> None:
    async with AsyncDigitalOcean() as do:
        async for domain in do.domains.iter():
            print(domain.name)
        await do.dns.point("example.com", "shop", "203.0.113.10")


asyncio.run(main())
```

## Where to go next

- [](configuration.md): all settings and the three ways to set them.
- [](dns.md): every DNS method in detail.
- [](domains.md): creating and removing zones.
- [](examples/index.md): complete scripts for common jobs.
