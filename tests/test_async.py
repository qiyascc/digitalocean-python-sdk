from __future__ import annotations

from conftest import record, records

from digitalocean_sdk import DNSRecord


async def test_async_dns(ado, api):
    api.queue(200, records(record(1, "A", "www", "1.1.1.1"), next_page=True))
    api.queue(200, records(record(2, "A", "www", "1.1.1.2")))
    found = await ado.dns.list("example.com", "A", "www")
    assert [r.id for r in found] == [1, 2]

    api.queue(200, records())
    api.queue(201, {"domain_record": record(3, "A", "shop", "203.0.113.10")})
    result = await ado.dns.point("example.com", "shop", "203.0.113.10")
    assert result[0].id == 3

    api.queue(201, {"domain_record": record(4, "TXT", "@", "x")})
    assert (await ado.dns.create("example.com", DNSRecord.txt("@", "x"))).id == 4


async def test_async_iter_and_account(ado, api):
    api.queue(200, {"domains": [{"name": "a.com"}], "links": {"pages": {"next": "x"}}})
    api.queue(200, {"domains": [{"name": "b.com"}], "links": {}})
    names = [d.name async for d in ado.domains.iter()]
    assert names == ["a.com", "b.com"]
    api.queue(200, {"domain_records": [record(1, "A", "@", "1.2.3.4")], "links": {}})
    assert [r.id async for r in ado.dns.iter("example.com")] == [1]
    api.queue(200, {"account": {"email": "a@b.c", "uuid": "u", "status": "active"}})
    assert (await ado.account()).status == "active"
    await ado.close()
