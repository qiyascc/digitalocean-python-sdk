# Account

`account()` on the client returns details of the account the token belongs to. It is the simplest way to check that a token works.

```python
from digitalocean_sdk import DigitalOcean

with DigitalOcean() as do:
    account = do.account()
    print(account.email, account.status, account.team)
```

It returns an {py:class}`~digitalocean_sdk.Account`:

| Field | Meaning |
| --- | --- |
| `email` | The account's email address. |
| `uuid` | The account's id. |
| `status` | For example `active`. |
| `email_verified` | Whether the email address is verified. |
| `droplet_limit` | How many Droplets the account may run. |
| `floating_ip_limit` | How many reserved IPs it may hold. |
| `team` | The team name, when the token belongs to a team. |

The token needs the `account:read` scope for this call. A token with only `domain` scopes gets `PermissionDeniedError` here, even though all DNS calls work.

On the async client, await it: `await do.account()`.
