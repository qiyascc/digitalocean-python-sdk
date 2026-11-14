# Let's Encrypt DNS-01

Let's Encrypt can check that you control a domain in two common ways: over HTTP, by fetching a file from your web server, or over DNS, by looking up a `TXT` record at `_acme-challenge.<domain>`. Only the DNS check (DNS-01) can issue **wildcard** certificates like `*.example.com`, and it works for machines that are not reachable from the internet at all.

[Certbot](https://certbot.eff.org/) supports DNS-01 through two hooks you write yourself: one that publishes the record, one that removes it afterwards. This page gives you both, built on the SDK.

## How certbot calls the hooks

For each name being validated, certbot runs the auth hook with two environment variables:

| Variable | Example | Meaning |
| --- | --- | --- |
| `CERTBOT_DOMAIN` | `example.com` | The name being validated. For `*.example.com` it is `example.com`. |
| `CERTBOT_VALIDATION` | `gfj9Xq...Rg85nM` | The value the `TXT` record must hold. |

Once the check is done, it runs the cleanup hook with the same variables.

A certificate for `example.com` and `*.example.com` needs **two** values under the same name, `_acme-challenge.example.com`, at the same time. So the hook must add its value next to any that are already there, not replace them.

## The hook script

Save this as `/etc/letsencrypt/digitalocean-hook.py` and make it executable:

```python
#!/usr/bin/env python3
import os
import sys
import time

from digitalocean_sdk import DigitalOcean

ZONE = os.environ.get("ACME_ZONE", "example.com")
WAIT = int(os.environ.get("ACME_WAIT", "60"))


def record_name(domain: str) -> str:
    domain = domain.rstrip(".").lower()
    if domain == ZONE:
        return "_acme-challenge"
    if domain.endswith("." + ZONE):
        return "_acme-challenge." + domain[: -len(ZONE) - 1]
    raise SystemExit(f"{domain} is not inside {ZONE}")


def current_values(do, name: str) -> list[str]:
    return [r.data.strip('"') for r in do.dns.list(ZONE, "TXT", name)]


def auth() -> None:
    name, value = record_name(os.environ["CERTBOT_DOMAIN"]), os.environ["CERTBOT_VALIDATION"]
    with DigitalOcean() as do:
        values = current_values(do, name)
        if value not in values:
            do.dns.set_txt(ZONE, name, values + [value], ttl=60)
    time.sleep(WAIT)


def cleanup() -> None:
    name, value = record_name(os.environ["CERTBOT_DOMAIN"]), os.environ["CERTBOT_VALIDATION"]
    with DigitalOcean() as do:
        remaining = [v for v in current_values(do, name) if v != value]
        if remaining:
            do.dns.set_txt(ZONE, name, remaining, ttl=60)
        else:
            do.dns.delete_all(ZONE, "TXT", name)


if __name__ == "__main__":
    {"auth": auth, "cleanup": cleanup}[sys.argv[1]]()
```

The cleanup removes only its own value. If another validation is still running for the same name, its value stays. When nothing is left, the record is deleted. `current_values` strips surrounding quotes, so values compare equal however DigitalOcean stores them.

`WAIT` gives DigitalOcean's name servers time to publish the record before Let's Encrypt looks it up. 60 seconds is a reasonable start. If Let's Encrypt reports that it could not find the TXT record, raise it.

## Run certbot

Put the credentials where the hook can read them, then ask for the certificate:

```bash
export DIGITALOCEAN_TOKEN=dop_v1_your-token
export ACME_ZONE=example.com

certbot certonly --manual --preferred-challenges dns \
  --manual-auth-hook "/etc/letsencrypt/digitalocean-hook.py auth" \
  --manual-cleanup-hook "/etc/letsencrypt/digitalocean-hook.py cleanup" \
  -d example.com -d "*.example.com"
```

Certbot remembers the hooks in the renewal config, so `certbot renew` runs them again automatically. Make sure the renewal job (the certbot timer or cron entry your system installed) has the same environment variables, for example by keeping them in a config file the SDK reads, see [](../configuration.md).

## Test against the staging server first

Let's Encrypt limits how many certificates you can request. While you get the hooks working, add `--dry-run` (for `renew`) or `--test-cert` (for `certonly`) to use their staging server, which has much higher limits.
