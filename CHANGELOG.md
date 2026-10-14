# Changelog

## 0.1.0

First release.

- Sync `DigitalOcean` and async `AsyncDigitalOcean` clients
- Domains: list, iter, get, exists, create, delete
- DNS: list, iter, get, exists, create, add, update (PATCH or PUT), delete, delete_all, replace
- DNS shortcuts: point, unpoint, alias, set_txt
- Lists follow every page, filters by type and name run on DigitalOcean's side
- Relative and fully qualified record names both work, host targets get their trailing dot
- `account()` to check a token, `request()` for any other endpoint
- Typed errors with DigitalOcean's error id and request id, automatic retries for rate limits and server errors
- Configuration through goodconf: code, `DIGITALOCEAN_*` environment variables or a TOML, YAML or JSON file
- Every user facing message lives in `messages.yaml` and can be overridden at runtime
- API version and every endpoint path come from the settings and can be overridden
