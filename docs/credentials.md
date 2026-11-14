# Access token

The DigitalOcean API uses personal access tokens. The SDK sends yours on every request as:

```text
Authorization: Bearer <token>
```

## Create a token

1. Sign in to the DigitalOcean control panel and open [API, Tokens](https://cloud.digitalocean.com/account/api/tokens).
2. Generate a new token. Give it a name you will recognise later, like `dns-automation`.
3. Choose its scopes. For DNS work the token needs the `domain` scopes: read, create, update and delete. Add `account:read` if you want to use `do.account()` to check the token.
4. Copy the token. It starts with `dop_v1_`.

A token with only the scopes it needs limits the damage if it ever leaks. A token without the right scope gets `PermissionDeniedError` (HTTP 403) on the calls it may not make.

## Give it to the SDK

```python
from digitalocean_sdk import DigitalOcean

do = DigitalOcean("dop_v1_...")
```

```bash
export DIGITALOCEAN_TOKEN=dop_v1_...
```

```toml
token = "dop_v1_..."
```

`DIGITALOCEAN_TOKEN` is the same variable `doctl` and Terraform use, so on a machine already set up for them the SDK usually works with no extra configuration. The token is the first positional argument of the client, or the keyword `token=`.

## Where to keep it

Keep the token out of your source code and out of git.

- In development, an environment variable or a `digitalocean.toml` file listed in `.gitignore`.
- On a server, the environment of the service (a systemd `EnvironmentFile`, a container secret, your platform's secret store).
- In CI, the CI system's secret variables.

The settings store the token as a pydantic `SecretStr`, so printing the settings shows `**********`. If a token leaks, revoke it on the same page and create a new one.

## Check that it works

```python
from digitalocean_sdk import AuthenticationError, DigitalOcean

with DigitalOcean() as do:
    try:
        account = do.account()
    except AuthenticationError:
        print("DigitalOcean rejected the token")
    else:
        print("Token works for", account.email, "status:", account.status)
```

If the token has no `account:read` scope, check with a DNS read instead: `do.domains.list()`.

If no token is found anywhere, building the client raises `AuthenticationError` before any request, with a message that lists every place the SDK looked.
