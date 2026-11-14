# Domains (zones)

DigitalOcean is not a registrar. A domain in its API is a **DNS zone** DigitalOcean serves for you. You buy the name at any registrar, add it here, then set its name servers at the registrar to:

```text
ns1.digitalocean.com
ns2.digitalocean.com
ns3.digitalocean.com
```

Until that is done, the records you create here exist but nobody on the internet asks DigitalOcean for them.

## Create a zone

```python
do.domains.create("example.com")
do.domains.create("example.com", ip_address="203.0.113.10")
```

Returns the new {py:class}`~digitalocean_sdk.Domain`. When `ip_address` is given, DigitalOcean also creates an `A` record for the apex pointing at it. The domain is cleaned first: `" Example.COM. "` becomes `example.com`.

## List zones

```python
for domain in do.domains.iter():
    print(domain.name, domain.ttl)

all_domains = do.domains.list()
```

`iter()` goes page by page and yields as it goes. `list()` follows every page and returns one `list[Domain]`. Pages hold `page_size` items (default 200).

## Read one

```python
domain = do.domains.get("example.com")
print(domain.name, domain.ttl)
print(domain.zone_file)
```

| Field | Meaning |
| --- | --- |
| `name` | The domain. |
| `ttl` | The zone's default TTL as DigitalOcean reports it. |
| `zone_file` | The whole zone in BIND zone file format, as text. Handy for backups. |

A zone that does not exist raises `NotFoundError`.

## Check whether it exists

```python
if not do.domains.exists("example.com"):
    do.domains.create("example.com")
```

Returns `True` or `False`. A 404 means `False`, it does not raise.

## Delete a zone

```python
do.domains.delete("example.com")
do.domains.delete("maybe-gone.com", missing_ok=True)
```

```{danger}
Deleting a zone deletes every record in it. If the domain's name servers still point at DigitalOcean, the domain stops resolving.
```

Without `missing_ok=True`, deleting a zone that does not exist raises `NotFoundError`.

## A worked example: back up every zone

```python
from pathlib import Path

from digitalocean_sdk import DigitalOcean

backup = Path("zone-backups")
backup.mkdir(exist_ok=True)

with DigitalOcean() as do:
    for domain in do.domains.iter():
        zone = do.domains.get(domain.name).zone_file or ""
        (backup / f"{domain.name}.zone").write_text(zone)
        print("saved", domain.name)
```

Run it nightly as a [scheduled job](examples/scheduled-jobs.md) and keep the folder in version control to see every DNS change over time.

## Async

On `AsyncDigitalOcean`, await the calls and use `async for` with `iter()`:

```python
async with AsyncDigitalOcean() as do:
    async for domain in do.domains.iter():
        print(domain.name)
    await do.domains.create("example.org")
```
