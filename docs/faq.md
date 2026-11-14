# FAQ and troubleshooting

## `AuthenticationError: Missing token`

The client found no token. It looked at the first argument, `DIGITALOCEAN_TOKEN` and the config files listed on [](settings.md#files). Variables exported in one terminal are not seen by another terminal or by a system service.

## `PermissionDeniedError` on DNS calls

The token lacks a scope. DNS work needs `domain:read`, `domain:create`, `domain:update` and `domain:delete`. `account()` needs `account:read`. Scopes are set when the token is created, so create a new one with the right set.

## `NotFoundError` for a domain I own

DigitalOcean only knows zones you have added. Create it with `do.domains.create("example.com")`. Owning the name at a registrar is not enough.

## My records exist but the domain does not resolve

The name servers at your registrar must be `ns1.digitalocean.com`, `ns2.digitalocean.com` and `ns3.digitalocean.com`. Check what DigitalOcean serves directly with `nslookup www.example.com ns1.digitalocean.com`. If that answers and a normal lookup does not, the registrar still points elsewhere, or caches have not expired yet.

## `ValidationError` when creating a `CNAME` or `MX` record

DigitalOcean wants host names with a trailing dot (`mail.example.com.`). The constructors and `replace` add it. If you built the `DNSRecord` by hand, add the dot or use `DNSRecord.cname` / `DNSRecord.mx`.

## Calling `add` twice created duplicates

`add` creates what you give it, every time. Use `replace` (or `point`, `alias`, `set_txt`) when you want the set to end up with exactly some values, however many times you run it.

## How do I change one value without touching the others?

Update the record by id:

```python
for record in do.dns.list("example.com", "A", "www"):
    if record.data == "203.0.113.10":
        do.dns.update("example.com", record, data="198.51.100.7")
```

## What is the lowest TTL I can use?

The SDK accepts 30 seconds and up for `default_ttl`. What DigitalOcean accepts on a single record is up to DigitalOcean, and it answers with `ValidationError` if a value is out of range.

## Can I manage Droplets with this?

Not with dedicated methods, but `do.request()` calls any endpoint with the same token and retries. See [](other-endpoints.md).

## How do I see what is sent?

Pass an `httpx.Client` with event hooks, see [](http-client.md#logging-every-request).
