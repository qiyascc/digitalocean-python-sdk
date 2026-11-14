# DNS records

Everything under `do.dns` works on the records of a zone that exists in your account ([create it first](domains.md) if needed).

## Records have ids

DigitalOcean stores each record on its own and gives it a numeric `id`. Updates and deletes address a record by that id. The SDK gives you both styles:

- **By id**, close to the API: `get`, `create`, `update`, `delete`.
- **By name and type**, like the sibling SDKs: `list`, `exists`, `add`, `replace`, `delete_all` and the shortcuts. These look up the ids for you.

## Names, types and the apex

Record names are relative to the domain, and the apex is `@`. A full name works too: `www.example.com` and `www.example.com.` become `www`. A name with a trailing dot outside the domain raises `ValueError`. Names are lower cased.

Types are strings or members of {py:class}`~digitalocean_sdk.RecordType`: `A`, `AAAA`, `CAA`, `CNAME`, `MX`, `NS`, `SOA`, `SRV` and `TXT`.

## The DNSRecord dataclass

```python
DNSRecord(type='A', name='www', data='203.0.113.10', ttl=1800, priority=None, port=None, weight=None, flags=None, tag=None, id=28448433)
```

| Field | Meaning |
| --- | --- |
| `type` | Record type, upper case. |
| `name` | Relative name, `@` for the apex. |
| `data` | The value: address, host name or text. |
| `ttl` | Seconds. `None` on a new record means `default_ttl`. |
| `priority` | `MX` and `SRV`. |
| `port`, `weight` | `SRV`. |
| `flags`, `tag` | `CAA`. |
| `id` | DigitalOcean's id. Filled on records read from or created through the API. Ignored when comparing records. |

`record.fqdn("example.com")` gives the full name.

### Constructors

```python
from digitalocean_sdk import DNSRecord

DNSRecord.a("www", "203.0.113.10")
DNSRecord.aaaa("www", "2001:db8::10")
DNSRecord.cname("blog", "example.github.io")
DNSRecord.txt("@", "v=spf1 include:spf.example.net ~all")
DNSRecord.mx("@", "mail.example.com", priority=10)
DNSRecord.ns("eu", "ns1.example.net")
DNSRecord.srv("_sip._udp", "sip.example.com", port=5060)
DNSRecord.caa("@", "letsencrypt.org")
```

| Constructor | Notes |
| --- | --- |
| `a(name, ip, ttl=None)` | Raises `ValueError` for anything but IPv4. |
| `aaaa(name, ip, ttl=None)` | Raises `ValueError` for anything but IPv6. |
| `cname(name, target, ttl=None)` | Target gets a trailing dot. |
| `txt(name, value, ttl=None)` | |
| `mx(name, host, priority=10, ttl=None)` | Host gets a trailing dot. |
| `ns(name, host, ttl=None)` | Host gets a trailing dot. |
| `srv(name, target, port, priority=10, weight=5, ttl=None)` | Target gets a trailing dot. |
| `caa(name, value, tag="issue", flags=0, ttl=None)` | `flags` and `tag` are separate fields, `data` holds the value. |

DigitalOcean requires host names in `CNAME`, `MX`, `NS` and `SRV` records to be fully qualified with a trailing dot. The constructors add it, and so does `replace`. If you build a `DNSRecord` by hand and pass it to `create` or `add`, add the dot yourself. Use `@` as the data to point at the apex.

## Reading

### `list` and `iter`

```python
do.dns.list("example.com")
do.dns.list("example.com", "A")
do.dns.list("example.com", "A", "www")
do.dns.list("example.com", name="www")

for record in do.dns.iter("example.com", "TXT"):
    print(record.name, record.data)
```

Type and name filters are applied by DigitalOcean, not in Python, so even a huge zone only sends back what you asked for. `list` follows every page and returns one `list[DNSRecord]`, `iter` yields records page by page.

### `get`

```python
record = do.dns.get("example.com", 28448433)
```

One record by id. A missing id raises `NotFoundError`.

### `exists`

```python
do.dns.exists("example.com", "A", "shop")
```

`True` when at least one record of that type and name exists.

## Creating

### `create`

```python
record = do.dns.create("example.com", DNSRecord.a("api", "203.0.113.20"))
print(record.id)
```

Creates one record and returns it with its new `id`.

### `add`

```python
created = do.dns.add(
    "example.com",
    DNSRecord.txt("@", "google-site-verification=abc"),
    DNSRecord.mx("@", "mail.example.com", priority=10),
    DNSRecord.caa("@", "letsencrypt.org"),
    DNSRecord.srv("_sip._udp", "sip.example.com", port=5060),
)
```

Creates several records, one request each, and returns them in order with their ids. It does not check for duplicates: calling it twice creates the records twice. Use `replace` when you want "make it so".

## Changing

### `update`

```python
do.dns.update("example.com", record, data="203.0.113.21", ttl=300)
do.dns.update("example.com", 28448433, name="api-v2")

record.ttl = 600
do.dns.update("example.com", record)
```

The record is a `DNSRecord` with an `id`, or the id itself.

- **With fields**, it sends a `PATCH` that changes only those fields. `name` is made relative to the domain and `type` upper cased for you.
- **Without fields**, it sends a `PUT` with the whole record. That needs a `DNSRecord`, not just an id, or it raises `ValueError`.

It returns the updated record. A `DNSRecord` without an `id` raises `ValueError`, since there is nothing to address.

### `replace`

```python
do.dns.replace("example.com", "A", "www", ["203.0.113.10", "203.0.113.11"], ttl=600)
do.dns.replace("example.com", "MX", "@", [
    DNSRecord.mx("@", "mx1.example.net", priority=10),
    DNSRecord.mx("@", "mx2.example.net", priority=20),
])
```

Makes one type and name hold exactly the values you pass:

1. Reads the current records of that type and name.
2. Keeps the ones whose value is in your list. If you passed a different TTL (or priority, port, weight, flags or tag), it updates only those fields with a `PATCH`.
3. Creates the values that are missing.
4. Deletes the rest.

Records that already match are not touched, so their ids stay the same. Returns the records now in the set. Host values are compared without the trailing dot and without regard to case.

## Deleting

### `delete`

```python
do.dns.delete("example.com", record)
do.dns.delete("example.com", 28448433, missing_ok=True)
```

Deletes one record by `DNSRecord` or id. Without `missing_ok=True`, a missing record raises `NotFoundError`.

### `delete_all`

```python
removed = do.dns.delete_all("example.com", "A", "old")
```

Deletes every record of that type and name and returns how many it removed, `0` if there were none.

## Shortcuts

```python
do.dns.point("example.com", "shop", "203.0.113.10")
do.dns.point("example.com", "shop", "2001:db8::10")
do.dns.alias("example.com", "docs", "example.github.io")
do.dns.set_txt("example.com", "_acme-challenge", "token-value", ttl=60)
do.dns.unpoint("example.com", "shop")
```

| Method | Built on | Returns |
| --- | --- | --- |
| `point(domain, name, ip, ttl=None)` | `replace` with `A` or `AAAA` | the records in the set |
| `alias(domain, name, target, ttl=None)` | `replace` with `CNAME` | the records in the set |
| `set_txt(domain, name, values, ttl=None)` | `replace` with `TXT` | the records in the set |
| `unpoint(domain, name, ip_version=4)` | `delete_all` with `A` (or `AAAA`) | how many were removed |

`unpoint` is safe to call when nothing is there.

## A worked example: moving a site

```python
from digitalocean_sdk import DigitalOcean

OLD, NEW = "203.0.113.10", "198.51.100.7"

with DigitalOcean() as do:
    for record in do.dns.iter("example.com", "A"):
        if record.data == OLD:
            do.dns.update("example.com", record, data=NEW)
            print(f"{record.name}: {OLD} -> {NEW}")
```

Updating by id keeps every other value of the name in place, which matters for names that have several `A` records.

## Async

`AsyncDigitalOcean().dns` has the same methods with the same arguments. Await them, and use `async for` with `iter`:

```python
async with AsyncDigitalOcean() as do:
    async for record in do.dns.iter("example.com", "A"):
        print(record.name, record.data)
    await do.dns.point("example.com", "shop", "203.0.113.10")
```
