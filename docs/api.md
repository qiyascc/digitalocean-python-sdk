# API reference

This page lists every public class and function with its signature. The guides explain how to use them: [](domains.md), [](dns.md), [](account.md), [](other-endpoints.md), [](errors.md) and [](configuration.md).

Everything below can be imported from `digitalocean_sdk`, except the resource classes, which you reach through a client (`do.dns`, `do.domains`).

## Clients

`DigitalOcean` is the sync client and `AsyncDigitalOcean` the async one. Both take the same arguments:

| Argument | Meaning |
| --- | --- |
| `token` | The personal access token. First positional argument. |
| `settings` | A ready `Settings` object. Other arguments are applied on top of it. |
| `config_file` | Path to a TOML, YAML or JSON settings file. |
| `http_client` | Your own `httpx.Client` (sync) or `httpx.AsyncClient` (async). |
| any setting | For example `timeout=10`, `default_ttl=300`. See [](settings.md). |

Each client has `dns`, `domains`, `settings` and `base_url`, plus `account()` and the generic `request()`.

```{eval-rst}
.. autoclass:: digitalocean_sdk.DigitalOcean
   :members:
   :inherited-members:
   :exclude-members: settings

.. autoclass:: digitalocean_sdk.AsyncDigitalOcean
   :members:
   :inherited-members:
   :exclude-members: settings
```

## What the methods return

The resource methods are annotated as returning `Any`, because one implementation serves both clients: on `DigitalOcean` they return the value, on `AsyncDigitalOcean` a coroutine that resolves to it.

| Method | Returns |
| --- | --- |
| `domains.list` | `list[Domain]`, all pages |
| `domains.iter` | iterator of `Domain` (async iterator on the async client) |
| `domains.get`, `domains.create` | `Domain` |
| `domains.exists` | `bool` |
| `domains.delete` | `None` |
| `dns.list` | `list[DNSRecord]`, all pages |
| `dns.iter` | iterator of `DNSRecord` (async iterator on the async client) |
| `dns.get`, `dns.create`, `dns.update` | `DNSRecord` |
| `dns.exists` | `bool` |
| `dns.add` | `list[DNSRecord]`, the created records |
| `dns.replace`, `dns.point`, `dns.alias`, `dns.set_txt` | `list[DNSRecord]`, the records now in the set |
| `dns.delete` | `None` |
| `dns.delete_all`, `dns.unpoint` | `int`, how many were removed |
| `account` | `Account` |
| `request` | decoded JSON, text, or `None` |

## Domains

```{eval-rst}
.. autoclass:: digitalocean_sdk.resources.Domains
   :members:
   :inherited-members:

.. autoclass:: digitalocean_sdk.resources.AsyncDomains
   :members:
   :inherited-members:
```

## DNS

```{eval-rst}
.. autoclass:: digitalocean_sdk.resources.DNS
   :members:
   :inherited-members:

.. autoclass:: digitalocean_sdk.resources.AsyncDNS
   :members:
   :inherited-members:
```

## Models

```{eval-rst}
.. autoclass:: digitalocean_sdk.DNSRecord
   :members:

.. autoclass:: digitalocean_sdk.RecordType
   :members:
   :undoc-members:

.. autoclass:: digitalocean_sdk.Domain
   :members:

.. autoclass:: digitalocean_sdk.Account
   :members:
```

## Settings

```{eval-rst}
.. autofunction:: digitalocean_sdk.load_settings

.. autoclass:: digitalocean_sdk.Settings
   :members: resolved_base_url, path, resolved_user_agent
```

## Errors

```{eval-rst}
.. autoexception:: digitalocean_sdk.DigitalOceanError
.. autoexception:: digitalocean_sdk.APIConnectionError
.. autoexception:: digitalocean_sdk.APITimeoutError
.. autoexception:: digitalocean_sdk.APIStatusError
.. autoexception:: digitalocean_sdk.ValidationError
.. autoexception:: digitalocean_sdk.AuthenticationError
.. autoexception:: digitalocean_sdk.PermissionDeniedError
.. autoexception:: digitalocean_sdk.NotFoundError
.. autoexception:: digitalocean_sdk.ConflictError
.. autoexception:: digitalocean_sdk.RateLimitError
.. autoexception:: digitalocean_sdk.ServerError
```

## Messages

```{eval-rst}
.. automodule:: digitalocean_sdk.messages
   :members: use, reset, catalog, text
```
