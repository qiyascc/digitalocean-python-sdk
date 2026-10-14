from __future__ import annotations

from typing import Any, AsyncIterator, Iterator, Optional

from .._base import Call
from ..messages import text
from ..models import Domain
from ._paging import collect, has_next, items_of, page_call


def domain_name(value: str) -> str:
    name = value.strip().lower().rstrip(".")
    if not name:
        raise ValueError(text("value.empty_domain"))
    return name


def _domain(body: Any) -> Domain:
    return Domain.from_api((body or {}).get("domain") or {})


class _DomainsBase:
    def __init__(self, client: Any) -> None:
        self._client = client

    def _path(self, endpoint: str, **params: Any) -> str:
        return self._client.settings.path(endpoint, **params)

    def list(self) -> Any:
        flow = collect(self._path("domains"), "domains", Domain.from_api, self._client.settings.page_size)
        return self._client._drive(flow)

    def get(self, name: str) -> Any:
        return self._client._execute(Call("GET", self._path("domain", domain=domain_name(name)), parse=_domain))

    def exists(self, name: str) -> Any:
        path = self._path("domain", domain=domain_name(name))
        return self._client._execute(Call("GET", path, parse=lambda body: body is not None,
                                          allow_status=frozenset({404})))

    def create(self, name: str, ip_address: Optional[str] = None) -> Any:
        body: dict[str, Any] = {"name": domain_name(name)}
        if ip_address:
            body["ip_address"] = ip_address
        return self._client._execute(Call("POST", self._path("domains"), json=body, parse=_domain))

    def delete(self, name: str, *, missing_ok: bool = False) -> Any:
        allow = frozenset({404}) if missing_ok else frozenset()
        path = self._path("domain", domain=domain_name(name))
        return self._client._execute(Call("DELETE", path, parse=lambda _: None, allow_status=allow))


class Domains(_DomainsBase):
    def iter(self) -> Iterator[Domain]:
        page = 1
        while True:
            body = self._client._execute(page_call(self._path("domains"), page, self._client.settings.page_size))
            batch = items_of(body, "domains", Domain.from_api)
            yield from batch
            if not batch or not has_next(body):
                return
            page += 1


class AsyncDomains(_DomainsBase):
    async def iter(self) -> AsyncIterator[Domain]:
        page = 1
        while True:
            call = page_call(self._path("domains"), page, self._client.settings.page_size)
            body = await self._client._execute(call)
            batch = items_of(body, "domains", Domain.from_api)
            for item in batch:
                yield item
            if not batch or not has_next(body):
                return
            page += 1
