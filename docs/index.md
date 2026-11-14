# DigitalOcean Python SDK

A small, typed Python client for the DigitalOcean Domains and DNS API. It works in sync and async code, waits and retries when DigitalOcean rate limits you, and gives you plain dataclasses instead of raw JSON.

```python
from digitalocean_sdk import DigitalOcean

with DigitalOcean("DIGITALOCEAN_TOKEN") as do:
    do.dns.point("example.com", "shop", "203.0.113.10")
```

That call makes `shop.example.com` resolve to `203.0.113.10`. If the record exists it is updated, if it is missing it is created, and extra `A` records with the same name are removed.

The package is on PyPI as `digitalocean-python-sdk` and is imported as `digitalocean_sdk`, so it can live next to the older `python-digitalocean` package. It needs Python 3.10 or newer.

## Where to start

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Installation
:link: installation
:link-type: doc

Set up a virtual environment, install the package with pip, uv or Poetry, and check that it imports.
:::

:::{grid-item-card} Access token
:link: credentials
:link-type: doc

Create a personal access token with the right scopes, and reuse the one `doctl` already has.
:::

:::{grid-item-card} Quickstart
:link: quickstart
:link-type: doc

Write your first script: create a zone, read it and point a subdomain at a Droplet.
:::

:::{grid-item-card} Configuration
:link: configuration
:link-type: doc

Pass settings in code, through `DIGITALOCEAN_*` environment variables or from a TOML, YAML or JSON file.
:::

:::{grid-item-card} Domains (zones)
:link: domains
:link-type: doc

Create, list, read and delete the zones DigitalOcean DNS serves.
:::

:::{grid-item-card} DNS records
:link: dns
:link-type: doc

Records by id, create, update, delete, replace whole sets, and the shortcuts.
:::

:::{grid-item-card} Recipes
:link: examples/index
:link-type: doc

Complete scripts: a subdomain per customer, dynamic DNS, Let's Encrypt DNS-01, Django and FastAPI.
:::

:::{grid-item-card} API reference
:link: api
:link-type: doc

Every public class, method and exception with its signature.
:::
::::

## What the SDK covers

- Domains: create, list, iterate, read (including the zone file), check and delete zones.
- DNS: list and iterate records with server side filters, read by id, create, update, delete by id or by name, and make a whole set match a list of values.
- DNS shortcuts: `point`, `unpoint`, `alias` and `set_txt`.
- Account: check the token with `account()`.
- Any other DigitalOcean endpoint (Droplets, volumes and more) through `request()`, with the same authentication, retries and errors.
- Typed errors with DigitalOcean's error code and request id.
- Automatic retries for rate limits, server errors and dropped connections, only where a retry is safe.
- Settings through [goodconf](https://github.com/lincolnloop/goodconf): code, environment variables or a config file. `DIGITALOCEAN_TOKEN` is the same variable `doctl` and Terraform use.
- Every message the SDK prints lives in a YAML file you can translate.

It has three siblings with the same shape: the [GoDaddy](https://godaddy-python-sdk.readthedocs.io/en/latest/), [Namecheap](https://namecheap-python-sdk.readthedocs.io/en/latest/) and [Hostinger](https://hostinger-python-sdk.readthedocs.io/en/latest/) SDKs. `dns.point("example.com", "shop", ip)` does the same thing in all four.

```{toctree}
:hidden:
:caption: Getting started

installation
credentials
quickstart
configuration
```

```{toctree}
:hidden:
:caption: Guides

domains
dns
account
other-endpoints
async
errors
retries-timeouts
http-client
messages
testing
```

```{toctree}
:hidden:
:caption: Examples

examples/index
examples/customer-subdomains
examples/dynamic-dns
examples/acme-dns-01
examples/migrate-between-providers
examples/web-frameworks
examples/scheduled-jobs
```

```{toctree}
:hidden:
:caption: Reference

api
settings
faq
changelog
```

```{toctree}
:hidden:
:caption: Project

development
about
```
