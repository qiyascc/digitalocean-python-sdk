from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Mapping, Optional, TypeVar

import httpx

from .config import Settings, load_settings
from .errors import APIConnectionError, APITimeoutError, error_from_response, retry_after_from
from .messages import text

T = TypeVar("T")

IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "PUT", "DELETE", "OPTIONS"})
RETRY_STATUSES = frozenset({500, 502, 503, 504})


@dataclass
class Call:
    method: str
    path: str
    params: Optional[Mapping[str, Any]] = None
    json: Any = None
    headers: Mapping[str, str] = field(default_factory=dict)
    parse: Callable[[Any], Any] = lambda body: body
    allow_status: frozenset[int] = frozenset()

    def clean_params(self) -> Optional[dict[str, Any]]:
        if not self.params:
            return None
        cleaned: dict[str, Any] = {}
        for key, value in self.params.items():
            if value is None:
                continue
            cleaned[key] = ("true" if value else "false") if isinstance(value, bool) else value
        return cleaned or None


Flow = Generator[Call, Any, T]


def _body_of(response: httpx.Response) -> Any:
    if response.status_code == 204 or not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text


class BaseClient:
    def __init__(
        self,
        token: Optional[str] = None,
        *,
        settings: Optional[Settings] = None,
        config_file: Optional[str] = None,
        **overrides: Any,
    ) -> None:
        if settings is None:
            settings = load_settings(config_file, token=token, **overrides)
        elif token or overrides:
            changes = {k: v for k, v in dict(overrides, token=token).items() if v is not None}
            settings = load_settings(None, **{**settings.model_dump(), **changes})

        self.settings = settings
        self._token = settings.require_token()
        self.base_url = settings.resolved_base_url()
        self.timeout = settings.timeout
        self.max_retries = settings.max_retries
        self.max_retry_wait = settings.max_retry_wait
        self.user_agent = settings.resolved_user_agent()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(base_url={self.base_url!r})"

    def _default_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
        }

    def _url(self, path: str) -> str:
        return path if path.startswith(("http://", "https://")) else self.base_url + path

    def _can_retry(self, call: Call, attempt: int) -> bool:
        return attempt < self.max_retries and call.method.upper() in IDEMPOTENT_METHODS

    def _wait_for(self, attempt: int, retry_after: Optional[float] = None) -> float:
        if retry_after is not None:
            return max(0.0, retry_after)
        delay = self.settings.backoff_base * (2 ** attempt)
        return min(self.settings.backoff_cap, delay) + random.uniform(0, self.settings.backoff_base / 2)

    def _decide(self, call: Call, response: httpx.Response, attempt: int) -> tuple[str, float]:
        status = response.status_code
        if status < 400 or status in call.allow_status:
            return "done", 0.0
        if status == 429 and attempt < self.max_retries:
            wait = self._wait_for(attempt, retry_after_from(response))
            if wait <= self.max_retry_wait:
                return "retry", wait
        if status in RETRY_STATUSES and self._can_retry(call, attempt):
            return "retry", self._wait_for(attempt)
        return "fail", 0.0

    def _finish(self, call: Call, response: httpx.Response) -> Any:
        if response.status_code in call.allow_status:
            return call.parse(None)
        return call.parse(_body_of(response))

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        missing_ok: bool = False,
    ) -> Any:
        allow = frozenset({404}) if missing_ok else frozenset()
        return self._execute(Call(method.upper(), path, params=params, json=json, allow_status=allow))

    def _execute(self, call: Call) -> Any:
        raise NotImplementedError

    def _drive(self, flow: Flow[Any]) -> Any:
        raise NotImplementedError


class SyncClient(BaseClient):
    def __init__(self, *args: Any, http_client: Optional[httpx.Client] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(timeout=self.timeout)

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self: T) -> T:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _execute(self, call: Call) -> Any:
        headers = {**self._default_headers(), **call.headers}
        attempt = 0
        while True:
            try:
                response = self._http.request(
                    call.method, self._url(call.path), params=call.clean_params(), json=call.json, headers=headers
                )
            except httpx.TimeoutException as exc:
                if self._can_retry(call, attempt):
                    time.sleep(self._wait_for(attempt))
                    attempt += 1
                    continue
                raise APITimeoutError(text("error.timeout", error=exc)) from exc
            except httpx.TransportError as exc:
                if self._can_retry(call, attempt):
                    time.sleep(self._wait_for(attempt))
                    attempt += 1
                    continue
                raise APIConnectionError(text("error.connection", error=exc)) from exc

            action, wait = self._decide(call, response, attempt)
            if action == "done":
                return self._finish(call, response)
            if action == "retry":
                time.sleep(wait)
                attempt += 1
                continue
            raise error_from_response(response)

    def _drive(self, flow: Flow[Any]) -> Any:
        try:
            call = next(flow)
            while True:
                call = flow.send(self._execute(call))
        except StopIteration as stop:
            return stop.value


class AsyncClient(BaseClient):
    def __init__(self, *args: Any, http_client: Optional[httpx.AsyncClient] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=self.timeout)

    async def close(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self: T) -> T:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def _execute(self, call: Call) -> Any:
        headers = {**self._default_headers(), **call.headers}
        attempt = 0
        while True:
            try:
                response = await self._http.request(
                    call.method, self._url(call.path), params=call.clean_params(), json=call.json, headers=headers
                )
            except httpx.TimeoutException as exc:
                if self._can_retry(call, attempt):
                    await asyncio.sleep(self._wait_for(attempt))
                    attempt += 1
                    continue
                raise APITimeoutError(text("error.timeout", error=exc)) from exc
            except httpx.TransportError as exc:
                if self._can_retry(call, attempt):
                    await asyncio.sleep(self._wait_for(attempt))
                    attempt += 1
                    continue
                raise APIConnectionError(text("error.connection", error=exc)) from exc

            action, wait = self._decide(call, response, attempt)
            if action == "done":
                return self._finish(call, response)
            if action == "retry":
                await asyncio.sleep(wait)
                attempt += 1
                continue
            raise error_from_response(response)

    async def _drive(self, flow: Flow[Any]) -> Any:
        try:
            call = next(flow)
            while True:
                call = flow.send(await self._execute(call))
        except StopIteration as stop:
            return stop.value


__all__ = ["Call", "Flow", "SyncClient", "AsyncClient"]
