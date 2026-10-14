from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

from .messages import text


class RecordType(str, Enum):
    A = "A"
    AAAA = "AAAA"
    CAA = "CAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"
    SOA = "SOA"
    SRV = "SRV"
    TXT = "TXT"

    def __str__(self) -> str:
        return self.value


RecordTypeLike = Union[RecordType, str]
HOST_TYPES = frozenset({"CNAME", "MX", "NS", "SRV"})


def record_type(value: RecordTypeLike) -> str:
    kind = value.value if isinstance(value, RecordType) else str(value).strip().upper()
    if not kind:
        raise ValueError(text("value.empty_type"))
    return kind


def hostname(value: str) -> str:
    host = value.strip()
    if host == "@" or host.endswith(".") or "." not in host:
        return host
    return f"{host}."


@dataclass
class DNSRecord:
    type: str
    name: str
    data: str
    ttl: Optional[int] = None
    priority: Optional[int] = None
    port: Optional[int] = None
    weight: Optional[int] = None
    flags: Optional[int] = None
    tag: Optional[str] = None
    id: Optional[int] = field(default=None, compare=False)

    def __post_init__(self) -> None:
        self.type = record_type(self.type)
        self.name = self.name.strip() or "@"

    @classmethod
    def a(cls, name: str, ip: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("A", name, str(ipaddress.IPv4Address(ip)), ttl)

    @classmethod
    def aaaa(cls, name: str, ip: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("AAAA", name, str(ipaddress.IPv6Address(ip)), ttl)

    @classmethod
    def cname(cls, name: str, target: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("CNAME", name, hostname(target), ttl)

    @classmethod
    def txt(cls, name: str, value: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("TXT", name, value, ttl)

    @classmethod
    def mx(cls, name: str, host: str, priority: int = 10, ttl: Optional[int] = None) -> DNSRecord:
        return cls("MX", name, hostname(host), ttl, priority=priority)

    @classmethod
    def ns(cls, name: str, host: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("NS", name, hostname(host), ttl)

    @classmethod
    def srv(
        cls, name: str, target: str, port: int, priority: int = 10, weight: int = 5, ttl: Optional[int] = None
    ) -> DNSRecord:
        return cls("SRV", name, hostname(target), ttl, priority=priority, port=port, weight=weight)

    @classmethod
    def caa(cls, name: str, value: str, tag: str = "issue", flags: int = 0, ttl: Optional[int] = None) -> DNSRecord:
        return cls("CAA", name, value, ttl, flags=flags, tag=tag)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DNSRecord:
        return cls(
            type=str(data.get("type", "")),
            name=str(data.get("name", "@")),
            data=str(data.get("data", "")),
            ttl=data.get("ttl"),
            priority=data.get("priority"),
            port=data.get("port"),
            weight=data.get("weight"),
            flags=data.get("flags"),
            tag=data.get("tag"),
            id=data.get("id"),
        )

    def to_api(self, default_ttl: Optional[int] = None) -> dict[str, Any]:
        body: dict[str, Any] = {"type": self.type, "name": self.name, "data": self.data}
        ttl = self.ttl if self.ttl is not None else default_ttl
        if ttl is not None:
            body["ttl"] = ttl
        for key in ("priority", "port", "weight", "flags", "tag"):
            value = getattr(self, key)
            if value is not None:
                body[key] = value
        return body

    def fqdn(self, domain: str) -> str:
        return domain if self.name == "@" else f"{self.name}.{domain}"


@dataclass
class Domain:
    name: str
    ttl: Optional[int] = None
    zone_file: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Domain:
        return cls(name=str(data.get("name", "")), ttl=data.get("ttl"), zone_file=data.get("zone_file"))


@dataclass
class Account:
    email: str
    uuid: str
    status: str
    email_verified: bool = False
    droplet_limit: Optional[int] = None
    floating_ip_limit: Optional[int] = None
    team: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Account:
        team = data.get("team") if isinstance(data.get("team"), dict) else {}
        return cls(
            email=str(data.get("email", "")),
            uuid=str(data.get("uuid", "")),
            status=str(data.get("status", "")),
            email_verified=bool(data.get("email_verified", False)),
            droplet_limit=data.get("droplet_limit"),
            floating_ip_limit=data.get("floating_ip_limit"),
            team=team.get("name") if team else None,
        )
