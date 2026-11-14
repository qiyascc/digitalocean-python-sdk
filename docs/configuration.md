# Configuration

Settings are loaded with [goodconf](https://github.com/lincolnloop/goodconf). You can set any of them in three places, and mix them freely:

1. **In code**, as arguments to `DigitalOcean(...)`.
2. **In the environment**, as `DIGITALOCEAN_*` variables.
3. **In a config file**: TOML, YAML or JSON.

When the same setting is in more than one place, code wins over the environment, and the environment wins over the file. Anything you do not set keeps its default. The full list is on [](settings.md).

## In code

The first positional argument is the token. Every other setting is a keyword argument with its own name:

```python
from digitalocean_sdk import DigitalOcean

do = DigitalOcean("dop_v1_...", timeout=10, max_retries=5, default_ttl=300)
```

Passing `None` for a setting is the same as not passing it.

## In the environment

Every setting has a variable named `DIGITALOCEAN_` plus the setting name in capitals:

```bash
export DIGITALOCEAN_TOKEN=dop_v1_your-token
export DIGITALOCEAN_TIMEOUT=15
export DIGITALOCEAN_DEFAULT_TTL=300
```

Endpoint paths, which are nested, use a double underscore:

```bash
export DIGITALOCEAN_ENDPOINTS__RECORDS="/{version}/domains/{domain}/records"
```

## In a config file

With no arguments, the client looks in the current working directory for, in this order:

1. `digitalocean.toml`
2. `digitalocean.yaml`
3. `digitalocean.yml`
4. `digitalocean.json`

To load a file from somewhere else, set `DIGITALOCEAN_CONFIG` or pass `config_file=`:

```python
do = DigitalOcean(config_file="/etc/myapp/digitalocean.toml")
```

::::{tab-set}

:::{tab-item} TOML
```toml
token = "dop_v1_your-token"
timeout = 15
max_retries = 3
default_ttl = 1800
```
:::

:::{tab-item} YAML
```yaml
token: dop_v1_your-token
timeout: 15
max_retries: 3
default_ttl: 1800
```
:::

:::{tab-item} JSON
```json
{"token": "dop_v1_your-token", "timeout": 15, "max_retries": 3, "default_ttl": 1800}
```
:::
::::

YAML needs the `yaml` extra, and TOML needs the `toml` extra on Python 3.10. JSON always works. Unknown keys are ignored.

```{warning}
A config file with the token in it is a secret. Keep it out of git and readable only by the user that runs your code.
```

## Building settings yourself

```python
from digitalocean_sdk import DigitalOcean, load_settings

settings = load_settings("/etc/myapp/digitalocean.toml", default_ttl=300)
do = DigitalOcean(settings=settings)
```

The first argument is the config file (or `None` for the default lookup). Keyword arguments override the file and the environment. Arguments passed next to `settings=` are applied on top of a copy:

```python
do = DigitalOcean(settings=settings, timeout=5)
```

## Settings that change behaviour

### `default_ttl`

The TTL, in seconds, for new records when you give none. Default `1800`. Values under 30 are rejected when the settings load. When `replace` (and the shortcuts built on it) keeps an existing record and you pass no TTL, the record keeps its own TTL.

### `page_size`

How many items to ask for per page while listing domains or records, from 1 to 200. Default `200`, the API maximum, which means the fewest requests.

## Base URL, version and endpoints

`base_url` is `https://api.digitalocean.com` and `api_version` is `v2`. Every endpoint is a path template relative to the base URL, with `{version}` filled from `api_version` and the other placeholders filled and URL encoded per call:

| Name | Default | Used by |
| --- | --- | --- |
| `account` | `/{version}/account` | `account()` |
| `domains` | `/{version}/domains` | `domains.list`, `domains.iter`, `domains.create` |
| `domain` | `/{version}/domains/{domain}` | `domains.get`, `domains.exists`, `domains.delete` |
| `records` | `/{version}/domains/{domain}/records` | `dns.list`, `dns.iter`, `dns.exists`, `dns.create`, `dns.add`, and the reads in `replace` and `delete_all` |
| `record` | `/{version}/domains/{domain}/records/{record_id}` | `dns.get`, `dns.update`, `dns.delete`, and the updates and deletes in `replace` and `delete_all` |

Override one and the others keep their defaults.

## User agent

Every request carries `User-Agent: digitalocean-python-sdk/<version>`. Change it with `user_agent`; `{version}` is replaced with the package version.

## Reading the active settings

```python
do = DigitalOcean()
print(do)
print(do.settings.default_ttl, do.settings.page_size)
```

```text
DigitalOcean(base_url='https://api.digitalocean.com')
1800 200
```
