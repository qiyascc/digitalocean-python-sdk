# Retries and timeouts

The SDK retries the failures worth retrying, and only when a retry cannot do harm.

## What is retried

| Failure | Retried? | Wait |
| --- | --- | --- |
| `429 Too Many Requests` | Yes, for every method. | Until the time in the `ratelimit-reset` header (or the `Retry-After` header), if that is within `max_retry_wait`. Without either, exponential backoff. |
| `500`, `502`, `503`, `504` | Only `GET`, `PUT` and `DELETE`. | Exponential backoff. |
| Timeout or connection error | Only `GET`, `PUT` and `DELETE`. | Exponential backoff. |
| Anything else | No. | |

`POST` and `PATCH` are never repeated after a server error or a dropped connection, because the first attempt may have reached DigitalOcean. A `POST` that creates a record is never sent twice. A `429` is different: DigitalOcean refused without doing anything.

## DigitalOcean's limits

DigitalOcean allows 5,000 requests per hour and 250 per minute per token. Note that some SDK calls make several requests:

| Call | Requests |
| --- | --- |
| `dns.list`, `domains.list` | one per page (200 items per page by default) |
| `dns.add` | one per record |
| `dns.replace`, `point`, `alias`, `set_txt` | one read, plus one per record created, changed or deleted |
| `dns.delete_all`, `unpoint` | one read, plus one per record deleted |

## The settings

| Setting | Default | Meaning |
| --- | --- | --- |
| `max_retries` | `3` | Retries after the first attempt. `0` turns them off. |
| `max_retry_wait` | `60` | Longest wait in seconds accepted from a rate limit answer. Longer waits raise `RateLimitError` at once. |
| `backoff_base` | `0.5` | First backoff delay in seconds, doubled on every retry. |
| `backoff_cap` | `8` | Upper limit for one backoff delay. |
| `timeout` | `30` | Seconds to wait for one request, for the HTTP client the SDK creates. |

```python
do = DigitalOcean(timeout=10, max_retries=5, max_retry_wait=30)
```

The wait for retry `n` (from 0) is `min(backoff_cap, backoff_base * 2 ** n)` plus up to `backoff_base / 2` of random jitter: about 0.5, 1, 2, 4 and then 8 seconds with the defaults.

## Turning retries off

```python
do = DigitalOcean(max_retries=0)
```

## Timeouts

`timeout` covers connecting, sending and reading for the client the SDK creates. A timed out `GET`, `PUT` or `DELETE` is retried. With your own `http_client=`, its timeout applies instead, see [](http-client.md).
