from __future__ import annotations

from typing import Any

from ._base import AsyncClient, Call, SyncClient
from .models import Account
from .resources import DNS, AsyncDNS, AsyncDomains, Domains


def _account(body: Any) -> Account:
    return Account.from_api((body or {}).get("account") or {})


class DigitalOcean(SyncClient):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.domains = Domains(self)
        self.dns = DNS(self)

    def account(self) -> Account:
        result: Account = self._execute(Call("GET", self.settings.path("account"), parse=_account))
        return result


class AsyncDigitalOcean(AsyncClient):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.domains = AsyncDomains(self)
        self.dns = AsyncDNS(self)

    async def account(self) -> Account:
        result: Account = await self._execute(Call("GET", self.settings.path("account"), parse=_account))
        return result
