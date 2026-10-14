from __future__ import annotations

import ipaddress
from typing import Any, AsyncIterator, Iterable, Iterator, Optional, Union

from .._base import Call, Flow
from ..messages import text
from ..models import HOST_TYPES, DNSRecord, RecordType, RecordTypeLike, hostname, record_type
from ._paging import collect, has_next, items_of, page_call
from .domains import domain_name

RecordValues = Union[str, DNSRecord, Iterable[Union[str, DNSRecord]]]
RecordRef = Union[int, str, DNSRecord]


def relative_name(name: str, domain: str) -> str:
    value = name.strip().lower()
    if not value:
        raise ValueError(text("value.empty_name"))
    if value in ("@", domain, f"{domain}."):
        return "@"
    bare = value.rstrip(".")
    if bare.endswith(f".{domain}"):
        return bare[: -len(domain) - 1]
    if value.endswith("."):
        raise ValueError(text("value.foreign_name", name=name, domain=domain))
    return value


def fqdn(name: str, domain: str) -> str:
    relative = relative_name(name, domain)
    return domain if relative == "@" else f"{relative}.{domain}"


def ip_record_type(ip: str) -> RecordType:
    return RecordType.A if ipaddress.ip_address(ip).version == 4 else RecordType.AAAA


def _record(body: Any) -> DNSRecord:
    return DNSRecord.from_api((body or {}).get("domain_record") or {})


def _record_id(ref: RecordRef) -> int:
    if isinstance(ref, DNSRecord):
        if ref.id is None:
            raise ValueError(text("value.needs_id", name=ref.name))
        return ref.id
    return int(ref)


def _same_data(kind: str, left: str, right: str) -> bool:
    if kind in HOST_TYPES:
        return left.rstrip(".").lower() == right.rstrip(".").lower()
    return left == right


class _DNSBase:
    def __init__(self, client: Any) -> None:
        self._client = client

    def _path(self, endpoint: str, **params: Any) -> str:
        return self._client.settings.path(endpoint, **params)

    def _filters(self, domain: str, type: Optional[RecordTypeLike], name: Optional[str]) -> dict[str, Any]:
        return {"type": record_type(type) if type is not None else None,
                "name": fqdn(name, domain) if name else None}

    def _list_flow(self, domain: str, type: Optional[RecordTypeLike] = None, name: Optional[str] = None) -> Flow[Any]:
        zone = domain_name(domain)
        return collect(self._path("records", domain=zone), "domain_records", DNSRecord.from_api,
                       self._client.settings.page_size, self._filters(zone, type, name))

    def _create_call(self, zone: str, record: DNSRecord) -> Call:
        body = record.to_api(self._client.settings.default_ttl)
        body["name"] = relative_name(record.name, zone)
        return Call("POST", self._path("records", domain=zone), json=body, parse=_record)

    def _delete_call(self, zone: str, record_id: int, missing_ok: bool = False) -> Call:
        allow = frozenset({404}) if missing_ok else frozenset()
        path = self._path("record", domain=zone, record_id=record_id)
        return Call("DELETE", path, parse=lambda _: None, allow_status=allow)

    def list(self, domain: str, type: Optional[RecordTypeLike] = None, name: Optional[str] = None) -> Any:
        return self._client._drive(self._list_flow(domain, type, name))

    def get(self, domain: str, record_id: int) -> Any:
        path = self._path("record", domain=domain_name(domain), record_id=int(record_id))
        return self._client._execute(Call("GET", path, parse=_record))

    def exists(self, domain: str, type: RecordTypeLike, name: str) -> Any:
        def flow() -> Flow[bool]:
            return bool((yield from self._list_flow(domain, type, name)))

        return self._client._drive(flow())

    def create(self, domain: str, record: DNSRecord) -> Any:
        return self._client._execute(self._create_call(domain_name(domain), record))

    def add(self, domain: str, *records: DNSRecord) -> Any:
        if not records:
            raise ValueError(text("value.add_needs_records"))
        zone = domain_name(domain)

        def flow() -> Flow[list[DNSRecord]]:
            created = []
            for record in records:
                created.append((yield self._create_call(zone, record)))
            return created

        return self._client._drive(flow())

    def update(self, domain: str, record: RecordRef, **fields: Any) -> Any:
        zone = domain_name(domain)
        path = self._path("record", domain=zone, record_id=_record_id(record))
        if not fields:
            if not isinstance(record, DNSRecord):
                raise ValueError(text("value.update_needs_fields"))
            body = record.to_api(self._client.settings.default_ttl)
            body["name"] = relative_name(record.name, zone)
            return self._client._execute(Call("PUT", path, json=body, parse=_record))
        if "name" in fields and fields["name"] is not None:
            fields["name"] = relative_name(fields["name"], zone)
        if "type" in fields and fields["type"] is not None:
            fields["type"] = record_type(fields["type"])
        return self._client._execute(Call("PATCH", path, json=fields, parse=_record))

    def delete(self, domain: str, record: RecordRef, *, missing_ok: bool = False) -> Any:
        return self._client._execute(self._delete_call(domain_name(domain), _record_id(record), missing_ok))

    def delete_all(self, domain: str, type: RecordTypeLike, name: str) -> Any:
        zone = domain_name(domain)

        def flow() -> Flow[int]:
            found = yield from self._list_flow(zone, type, name)
            for record in found:
                yield self._delete_call(zone, record.id, missing_ok=True)
            return len(found)

        return self._client._drive(flow())

    def replace(
        self, domain: str, type: RecordTypeLike, name: str, values: RecordValues, *, ttl: Optional[int] = None
    ) -> Any:
        zone = domain_name(domain)
        kind = record_type(type)
        label = relative_name(name, zone)
        if isinstance(values, (str, DNSRecord)):
            values = [values]
        wanted = [v if isinstance(v, DNSRecord) else DNSRecord(kind, label, str(v), ttl) for v in values]
        if not wanted:
            raise ValueError(text("value.no_values"))
        for record in wanted:
            record.type, record.name = kind, label
            if record.ttl is None:
                record.ttl = ttl
            if kind in HOST_TYPES:
                record.data = hostname(record.data)

        def flow() -> Flow[list[DNSRecord]]:
            existing = yield from self._list_flow(zone, kind, label)
            result: list[DNSRecord] = []
            spare = list(existing)
            for record in wanted:
                match = next((r for r in spare if _same_data(kind, r.data, record.data)), None)
                if match is None:
                    result.append((yield self._create_call(zone, record)))
                    continue
                spare.remove(match)
                changes = {key: getattr(record, key) for key in ("ttl", "priority", "port", "weight", "flags", "tag")
                           if getattr(record, key) is not None and getattr(record, key) != getattr(match, key)}
                if changes:
                    path = self._path("record", domain=zone, record_id=match.id)
                    match = yield Call("PATCH", path, json=changes, parse=_record)
                result.append(match)
            for record in spare:
                yield self._delete_call(zone, record.id, missing_ok=True)
            return result

        return self._client._drive(flow())

    def point(self, domain: str, name: str, ip: str, *, ttl: Optional[int] = None) -> Any:
        address = str(ipaddress.ip_address(ip))
        return self.replace(domain, ip_record_type(address), name, [address], ttl=ttl)

    def unpoint(self, domain: str, name: str, ip_version: int = 4) -> Any:
        return self.delete_all(domain, RecordType.A if ip_version == 4 else RecordType.AAAA, name)

    def alias(self, domain: str, name: str, target: str, *, ttl: Optional[int] = None) -> Any:
        return self.replace(domain, RecordType.CNAME, name, [target], ttl=ttl)

    def set_txt(self, domain: str, name: str, values: Union[str, Iterable[str]], *, ttl: Optional[int] = None) -> Any:
        return self.replace(domain, RecordType.TXT, name, values, ttl=ttl)



class DNS(_DNSBase):
    def iter(
        self, domain: str, type: Optional[RecordTypeLike] = None, name: Optional[str] = None
    ) -> Iterator[DNSRecord]:
        zone = domain_name(domain)
        path, params = self._path("records", domain=zone), self._filters(zone, type, name)
        page = 1
        while True:
            body = self._client._execute(page_call(path, page, self._client.settings.page_size, params))
            batch = items_of(body, "domain_records", DNSRecord.from_api)
            yield from batch
            if not batch or not has_next(body):
                return
            page += 1


class AsyncDNS(_DNSBase):
    async def iter(
        self, domain: str, type: Optional[RecordTypeLike] = None, name: Optional[str] = None
    ) -> AsyncIterator[DNSRecord]:
        zone = domain_name(domain)
        path, params = self._path("records", domain=zone), self._filters(zone, type, name)
        page = 1
        while True:
            body = await self._client._execute(page_call(path, page, self._client.settings.page_size, params))
            batch = items_of(body, "domain_records", DNSRecord.from_api)
            for item in batch:
                yield item
            if not batch or not has_next(body):
                return
            page += 1
