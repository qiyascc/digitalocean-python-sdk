# Other endpoints

The SDK wraps the Domains and DNS APIs. DigitalOcean's API covers much more: Droplets, volumes, load balancers, Spaces keys and so on. For those, the client has a generic `request()` method with the same token, retries and error classes:

```python
from digitalocean_sdk import DigitalOcean

with DigitalOcean() as do:
    droplets = do.request("GET", "/v2/droplets", params={"per_page": 50})
    do.request("POST", "/v2/droplets/123/actions", json={"type": "reboot"})
```

## Signature

```text
do.request(method, path, *, params=None, json=None, missing_ok=False)
```

| Argument | Meaning |
| --- | --- |
| `method` | HTTP method, for example `"GET"` or `"POST"`. Upper cased for you. |
| `path` | Path relative to `base_url`, like `/v2/droplets`. A full `https://` URL is used as it is. |
| `params` | Query parameters. `None` values are dropped, `True`/`False` become `"true"`/`"false"`. |
| `json` | Request body, sent as JSON. |
| `missing_ok` | Return `None` instead of raising `NotFoundError` on a 404. |

It returns the decoded JSON body, the plain text if the body is not JSON, or `None` for an empty answer. Paging is up to you: pass `page` and `per_page`, and follow `links.pages.next` in the answer.

## A worked example: point a name at a Droplet by its name

```python
from digitalocean_sdk import DigitalOcean

with DigitalOcean() as do:
    body = do.request("GET", "/v2/droplets", params={"name": "web-1"})
    droplet = body["droplets"][0]
    ip = next(n["ip_address"] for n in droplet["networks"]["v4"] if n["type"] == "public")
    do.dns.point("example.com", "web", ip, ttl=300)
```

The token needs the `droplet:read` scope for the first call.

## Retries and errors

`request()` behaves like every other call: `429` answers are waited out, server errors and dropped connections are retried for `GET`, `PUT` and `DELETE`, and error statuses raise the exceptions on [](errors.md). `POST` and `PATCH` are never repeated after a server error.

## Async

```python
async with AsyncDigitalOcean() as do:
    droplets = await do.request("GET", "/v2/droplets")
```
