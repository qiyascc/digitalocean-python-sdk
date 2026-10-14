from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from .._base import Call, Flow


def has_next(body: Any) -> bool:
    if not isinstance(body, dict):
        return False
    pages = (body.get("links") or {}).get("pages") or {}
    return bool(pages.get("next"))


def page_call(path: str, page: int, size: int, params: Optional[Mapping[str, Any]] = None) -> Call:
    return Call("GET", path, params={**(params or {}), "page": page, "per_page": size})


def items_of(body: Any, key: str, parse: Callable[[dict[str, Any]], Any]) -> list[Any]:
    rows = body.get(key) if isinstance(body, dict) else None
    return [parse(row) for row in rows or [] if isinstance(row, dict)]


def collect(
    path: str, key: str, parse: Callable[[dict[str, Any]], Any], size: int, params: Optional[Mapping[str, Any]] = None
) -> Flow[list[Any]]:
    found: list[Any] = []
    page = 1
    while True:
        body = yield page_call(path, page, size, params)
        batch = items_of(body, key, parse)
        found.extend(batch)
        if not batch or not has_next(body):
            return found
        page += 1
