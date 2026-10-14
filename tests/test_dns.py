from __future__ import annotations

import pytest
from conftest import record, records

from digitalocean_sdk import DNSRecord, RecordType
from digitalocean_sdk.resources import fqdn, relative_name


def test_names():
    assert relative_name("@", "example.com") == "@"
    assert relative_name("example.com.", "example.com") == "@"
    assert relative_name("WWW.example.com", "example.com") == "www"
    assert relative_name("a.b", "example.com") == "a.b"
    assert fqdn("www", "example.com") == "www.example.com"
    assert fqdn("@", "example.com") == "example.com"
    with pytest.raises(ValueError):
        relative_name("www.other.com.", "example.com")
    with pytest.raises(ValueError):
        relative_name(" ", "example.com")


def test_list_filters_on_server(do, api):
    api.queue(200, records(record(1, "A", "www", "1.2.3.4"), next_page=True))
    api.queue(200, records(record(2, "A", "www", "1.2.3.5")))
    found = do.dns.list("example.com", RecordType.A, "www")
    assert [r.id for r in found] == [1, 2]
    params = api.requests[0].url.params
    assert (params["type"], params["name"], params["per_page"]) == ("A", "www.example.com", "200")
    assert api.requests[1].url.params["page"] == "2"
    assert found[0] == DNSRecord("A", "www", "1.2.3.4", 1800, id=1)


def test_list_apex_and_iter(do, api):
    api.queue(200, records(record(1, "NS", "@", "ns1.digitalocean.com")))
    assert do.dns.list("example.com", name="@")[0].type == "NS"
    assert api.last.url.params["name"] == "example.com"
    api.queue(200, records(record(1, "A", "@", "1.2.3.4")))
    assert [r.data for r in do.dns.iter("example.com")] == ["1.2.3.4"]


def test_create_uses_default_ttl_and_relative_name(do, api):
    api.queue(201, {"domain_record": record(9, "A", "api", "203.0.113.20")})
    created = do.dns.create("example.com", DNSRecord.a("api.example.com", "203.0.113.20"))
    assert api.last.url.path == "/v2/domains/example.com/records"
    assert api.body() == {"type": "A", "name": "api", "data": "203.0.113.20", "ttl": 1800}
    assert created.id == 9


def test_record_helpers():
    assert DNSRecord.cname("docs", "example.github.io").data == "example.github.io."
    assert DNSRecord.cname("www", "@").data == "@"
    mx = DNSRecord.mx("@", "mail.example.com", priority=5).to_api()
    assert mx == {"type": "MX", "name": "@", "data": "mail.example.com.", "priority": 5}
    srv = DNSRecord.srv("_sip._udp", "sip.example.com", port=5060).to_api(300)
    assert (srv["port"], srv["weight"], srv["priority"], srv["ttl"]) == (5060, 5, 10, 300)
    assert DNSRecord.caa("@", "letsencrypt.org").to_api()["tag"] == "issue"
    with pytest.raises(ValueError):
        DNSRecord.a("www", "2001:db8::1")


def test_add(do, api):
    api.queue(201, {"domain_record": record(1, "TXT", "@", "v=spf1")})
    api.queue(201, {"domain_record": record(2, "MX", "@", "mail.example.com.", priority=10)})
    created = do.dns.add("example.com", DNSRecord.txt("@", "v=spf1"), DNSRecord.mx("@", "mail.example.com"))
    assert [r.id for r in created] == [1, 2]
    assert api.calls() == [("POST", "/v2/domains/example.com/records")] * 2
    with pytest.raises(ValueError):
        do.dns.add("example.com")


def test_update_patch_and_put(do, api):
    api.queue(200, {"domain_record": record(5, "A", "www", "1.1.1.1", ttl=300)})
    do.dns.update("example.com", 5, data="1.1.1.1", ttl=300, name="www.example.com")
    assert (api.last.method, api.last.url.path) == ("PATCH", "/v2/domains/example.com/records/5")
    assert api.body() == {"data": "1.1.1.1", "ttl": 300, "name": "www"}

    api.queue(200, {"domain_record": record(5, "A", "www", "1.1.1.2")})
    do.dns.update("example.com", DNSRecord("A", "www", "1.1.1.2", 600, id=5))
    assert api.last.method == "PUT"
    assert api.body() == {"type": "A", "name": "www", "data": "1.1.1.2", "ttl": 600}

    with pytest.raises(ValueError):
        do.dns.update("example.com", 5)
    with pytest.raises(ValueError):
        do.dns.update("example.com", DNSRecord("A", "www", "1.1.1.2"), ttl=60)


def test_delete_and_delete_all(do, api):
    api.queue(204)
    do.dns.delete("example.com", DNSRecord("A", "x", "1.2.3.4", id=7))
    assert (api.last.method, api.last.url.path) == ("DELETE", "/v2/domains/example.com/records/7")
    api.queue(404, {"id": "not_found", "message": "gone"})
    assert do.dns.delete("example.com", 8, missing_ok=True) is None

    api.queue(200, records(record(1, "A", "old", "1.2.3.4"), record(2, "A", "old", "1.2.3.5")))
    api.queue(204)
    api.queue(204)
    assert do.dns.delete_all("example.com", "A", "old") == 2
    assert api.calls()[-2:] == [("DELETE", "/v2/domains/example.com/records/1"),
                                ("DELETE", "/v2/domains/example.com/records/2")]


def test_replace_keeps_creates_patches_and_deletes(do, api):
    api.queue(200, records(record(1, "A", "www", "1.1.1.1", ttl=1800), record(2, "A", "www", "9.9.9.9")))
    api.queue(201, {"domain_record": record(3, "A", "www", "2.2.2.2", ttl=600)})
    api.queue(200, {"domain_record": record(1, "A", "www", "1.1.1.1", ttl=600)})
    api.queue(204)
    result = do.dns.replace("example.com", "A", "www", ["2.2.2.2", "1.1.1.1"], ttl=600)
    assert [(r.id, r.ttl) for r in result] == [(3, 600), (1, 600)]
    assert api.calls() == [
        ("GET", "/v2/domains/example.com/records"),
        ("POST", "/v2/domains/example.com/records"),
        ("PATCH", "/v2/domains/example.com/records/1"),
        ("DELETE", "/v2/domains/example.com/records/2"),
    ]
    assert api.body(1) == {"type": "A", "name": "www", "data": "2.2.2.2", "ttl": 600}
    assert api.body(2) == {"ttl": 600}


def test_point_is_idempotent(do, api):
    api.queue(200, records(record(1, "A", "shop", "203.0.113.10")))
    result = do.dns.point("example.com", "shop", "203.0.113.10")
    assert [r.id for r in result] == [1]
    assert api.calls() == [("GET", "/v2/domains/example.com/records")]


def test_point_ipv6_alias_and_txt(do, api):
    api.queue(200, records())
    api.queue(201, {"domain_record": record(1, "AAAA", "shop", "2001:db8::10")})
    do.dns.point("example.com", "shop", "2001:db8::10")
    assert api.requests[0].url.params["type"] == "AAAA"
    assert api.body() == {"type": "AAAA", "name": "shop", "data": "2001:db8::10", "ttl": 1800}

    api.queue(200, records(record(4, "CNAME", "docs", "example.github.io.")))
    do.dns.alias("example.com", "docs", "example.github.io")
    assert api.last.method == "GET"

    api.queue(200, records(record(5, "TXT", "_acme-challenge", "old")))
    api.queue(201, {"domain_record": record(6, "TXT", "_acme-challenge", "new", ttl=60)})
    api.queue(204)
    do.dns.set_txt("example.com", "_acme-challenge", "new", ttl=60)
    assert api.calls()[-2:] == [("POST", "/v2/domains/example.com/records"),
                                ("DELETE", "/v2/domains/example.com/records/5")]


def test_unpoint(do, api):
    api.queue(200, records())
    assert do.dns.unpoint("example.com", "shop") == 0
    assert api.last.url.params["type"] == "A"
