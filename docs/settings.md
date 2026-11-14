# Settings reference

Every setting the client reads, with its environment variable and default. Set them in code, in the environment or in a config file, as described in [](configuration.md).

| Setting | Environment variable | Type | Default | Allowed | Description |
| --- | --- | --- | --- | --- | --- |
| `token` | `DIGITALOCEAN_TOKEN` | secret string | not set |  | Personal access token from cloud.digitalocean.com/account/api/tokens. |
| `base_url` | `DIGITALOCEAN_BASE_URL` | string | `https://api.digitalocean.com` |  | API URL without the version part. |
| `api_version` | `DIGITALOCEAN_API_VERSION` | string | `v2` |  | API version that fills the {version} part of every endpoint. |
| `endpoints` | `DIGITALOCEAN_ENDPOINTS__<NAME>` | table | see below |  | Path templates for every API call, relative to the base URL. |
| `timeout` | `DIGITALOCEAN_TIMEOUT` | number | `30` | > 0 | Seconds to wait for a single request. |
| `max_retries` | `DIGITALOCEAN_MAX_RETRIES` | integer | `3` | >= 0 | How many times a failed request is tried again. |
| `max_retry_wait` | `DIGITALOCEAN_MAX_RETRY_WAIT` | number | `60` | >= 0 | Longest wait in seconds the client accepts from a rate limit answer. |
| `backoff_base` | `DIGITALOCEAN_BACKOFF_BASE` | number | `0.5` | >= 0 | First backoff delay in seconds, doubled on every retry. |
| `backoff_cap` | `DIGITALOCEAN_BACKOFF_CAP` | number | `8` | >= 0 | Longest backoff delay in seconds. |
| `page_size` | `DIGITALOCEAN_PAGE_SIZE` | integer | `200` | >= 1, <= 200 | Items asked for on every page when listing, between 1 and 200. |
| `default_ttl` | `DIGITALOCEAN_DEFAULT_TTL` | integer | `1800` | >= 30 | TTL in seconds used for new records when none is given. |
| `user_agent` | `DIGITALOCEAN_USER_AGENT` | string | `digitalocean-python-sdk/{version}` |  | User-Agent header. {version} is replaced with the package version. |

## Endpoints

Each endpoint is a path template relative to the base URL. `{version}` is filled from `api_version`, the other placeholders from the call. Override one with `DIGITALOCEAN_ENDPOINTS__<NAME>`, for example `DIGITALOCEAN_ENDPOINTS__ACCOUNT`.

| Name | Default |
| --- | --- |
| `endpoints.account` | `/{version}/account` |
| `endpoints.domains` | `/{version}/domains` |
| `endpoints.domain` | `/{version}/domains/{domain}` |
| `endpoints.records` | `/{version}/domains/{domain}/records` |
| `endpoints.record` | `/{version}/domains/{domain}/records/{record_id}` |

## Files

Without `config_file=`, the client looks for these files in the working directory, in this order, and uses the first one it finds:

- `digitalocean.toml`
- `digitalocean.yaml`
- `digitalocean.yml`
- `digitalocean.json`

`DIGITALOCEAN_CONFIG` points at a file anywhere else.
