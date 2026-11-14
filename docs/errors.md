# Errors

Every exception the SDK raises on purpose inherits from {py:class}`~digitalocean_sdk.DigitalOceanError`, so one `except DigitalOceanError` catches all API problems. Mistakes in your own arguments, like an empty name or an invalid IP address, raise plain `ValueError` before any request is sent.

## The hierarchy

```text
DigitalOceanError
├── APIConnectionError        the request never got an answer
│   └── APITimeoutError       it timed out
└── APIStatusError            DigitalOcean answered with an error status
    ├── ValidationError       400, 422
    ├── AuthenticationError   401, or no token configured
    ├── PermissionDeniedError 403, often a token without the right scope
    ├── NotFoundError         404
    ├── ConflictError         409
    ├── RateLimitError        429 after the retries ran out
    └── ServerError           500 and above
```

Any other 4xx status becomes a plain `APIStatusError`.

| Exception | Typical cause | What to do |
| --- | --- | --- |
| `ValidationError` | A record DigitalOcean does not accept, for example a `CNAME` at the apex or a host name without its trailing dot. | Read `exc.message`, fix the record. |
| `AuthenticationError` | A wrong, expired or revoked token, or none at all. | Create a new token. |
| `PermissionDeniedError` | The token lacks a scope, for example `domain:create`. | Add the scope or use another token. |
| `NotFoundError` | The zone or record id does not exist. | Check the name or id. For deletes, consider `missing_ok=True`. |
| `ConflictError` | The change clashes with the current state. | Read the current state and try again. |
| `RateLimitError` | Over 250 requests a minute or 5,000 an hour, and waiting did not help in time. | Slow down. |
| `ServerError` | A problem on DigitalOcean's side. | Try again later. Safe calls were already retried. |
| `APIConnectionError`, `APITimeoutError` | Network trouble or no answer within `timeout`. | Check the network, or raise `timeout`. |

## What an error carries

| Attribute | Meaning |
| --- | --- |
| `message` | DigitalOcean's `message`, or the SDK's own text. |
| `code` | DigitalOcean's error id from the body, for example `not_found` or `unprocessable_entity`. |
| `request_id` | DigitalOcean's id for the request, from the body or the `x-request-id` header. Quote it to their support. |
| `status_code` | The HTTP status, `None` for connection errors. |
| `response` | The raw `httpx.Response`, or `None`. |

`RateLimitError` also has `retry_after`, in seconds, from `Retry-After` or the `ratelimit-reset` header.

## Handling patterns

### Show what DigitalOcean refused

```python
from digitalocean_sdk import DigitalOcean, DNSRecord, ValidationError

with DigitalOcean() as do:
    try:
        do.dns.create("example.com", DNSRecord.cname("@", "elsewhere.com"))
    except ValidationError as exc:
        print(exc.code, exc.message, exc.request_id)
```

### Retry later or fix the request

```python
from digitalocean_sdk import APIConnectionError, APIStatusError, ServerError

try:
    do.dns.point("example.com", "shop", ip)
except ValueError:
    raise
except (ServerError, APIConnectionError):
    schedule_retry_later()
except APIStatusError as exc:
    log.error("DigitalOcean refused: %s (request %s)", exc.message, exc.request_id)
    raise
```

## Errors raised before a request

| Error | When |
| --- | --- |
| `AuthenticationError` | Building a client with no token anywhere. |
| `ValueError` | An empty domain, name or type, a name outside the domain, an invalid IP, `add()` with no records, `replace()` with no values, `update()` with an id and no fields, or a `DNSRecord` without an id where one is needed. |
| `pydantic.ValidationError` | A setting outside its range, for example `page_size=500` or `default_ttl=10`. |

The texts of the SDK's own messages can be changed or translated, see [](messages.md).
