from __future__ import annotations

from digitalocean_sdk import Domain


def test_list_follows_pages(do, api):
    next_url = "https://api.digitalocean.com/v2/domains?page=2"
    api.queue(200, {"domains": [{"name": "a.com", "ttl": 1800, "zone_file": "x"}],
                    "links": {"pages": {"next": next_url}}, "meta": {"total": 2}})
    api.queue(200, {"domains": [{"name": "b.com", "ttl": 1800}], "links": {}, "meta": {"total": 2}})
    domains = do.domains.list()
    assert [d.name for d in domains] == ["a.com", "b.com"]
    assert api.requests[0].url.params["page"] == "1"
    assert api.requests[0].url.params["per_page"] == "200"
    assert api.requests[1].url.params["page"] == "2"


def test_iter(do, api):
    api.queue(200, {"domains": [{"name": "a.com"}], "links": {}})
    assert [d.name for d in do.domains.iter()] == ["a.com"]


def test_get_create_delete(do, api):
    api.queue(200, {"domain": {"name": "example.com", "ttl": 1800, "zone_file": "$ORIGIN example.com."}})
    assert do.domains.get("Example.COM.") == Domain("example.com", 1800, "$ORIGIN example.com.")
    assert api.last.url.path == "/v2/domains/example.com"

    api.queue(201, {"domain": {"name": "example.com", "ttl": 1800, "zone_file": None}})
    created = do.domains.create("example.com", ip_address="203.0.113.10")
    assert api.last.method == "POST"
    assert api.body() == {"name": "example.com", "ip_address": "203.0.113.10"}
    assert created.name == "example.com"

    api.queue(204)
    assert do.domains.delete("example.com") is None
    assert api.last.method == "DELETE"


def test_exists_and_missing_ok(do, api):
    api.queue(200, {"domain": {"name": "example.com"}})
    api.queue(404, {"id": "not_found", "message": "nope"})
    assert do.domains.exists("example.com") is True
    assert do.domains.exists("other.com") is False
    api.queue(404, {"id": "not_found", "message": "nope"})
    assert do.domains.delete("gone.com", missing_ok=True) is None


def test_account(do, api):
    api.queue(200, {"account": {"email": "a@b.c", "uuid": "u", "status": "active", "email_verified": True,
                                "droplet_limit": 25, "team": {"uuid": "t", "name": "My Team"}}})
    account = do.account()
    assert (account.email, account.team, account.droplet_limit) == ("a@b.c", "My Team", 25)
    assert api.last.headers["Authorization"] == "Bearer token"
