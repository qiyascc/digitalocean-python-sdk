from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from .messages import text


class DigitalOceanError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        response: Optional[httpx.Response] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.request_id = request_id
        self.response = response

    def __str__(self) -> str:
        parts = []
        if self.status_code:
            parts.append(f"[{self.status_code}]")
        if self.code:
            parts.append(self.code)
        parts.append(self.message)
        if self.request_id:
            parts.append(f"(request {self.request_id})")
        return " ".join(parts)


class APIConnectionError(DigitalOceanError):
    pass


class APITimeoutError(APIConnectionError):
    pass


class APIStatusError(DigitalOceanError):
    pass


class ValidationError(APIStatusError):
    pass


class AuthenticationError(APIStatusError):
    pass


class PermissionDeniedError(APIStatusError):
    pass


class NotFoundError(APIStatusError):
    pass


class ConflictError(APIStatusError):
    pass


class RateLimitError(APIStatusError):
    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(APIStatusError):
    pass


_STATUS_MAP: dict[int, type[APIStatusError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
}


def retry_after_from(response: httpx.Response, now: Optional[float] = None) -> Optional[float]:
    header = response.headers.get("Retry-After")
    if header:
        try:
            return max(0.0, float(header))
        except ValueError:
            pass
    reset = response.headers.get("ratelimit-reset")
    if reset:
        try:
            return max(0.0, float(reset) - (now if now is not None else time.time()))
        except ValueError:
            return None
    return None


def error_from_response(response: httpx.Response) -> APIStatusError:
    try:
        body = response.json()
    except ValueError:
        body = None

    if isinstance(body, dict):
        message = str(body.get("message") or response.reason_phrase or text("error.request_failed"))
        code = body.get("id")
        request_id = body.get("request_id") or response.headers.get("x-request-id")
    else:
        message = response.text.strip() or response.reason_phrase or text("error.request_failed")
        code = None
        request_id = response.headers.get("x-request-id")

    status = response.status_code
    kwargs: dict[str, Any] = dict(status_code=status, code=code, request_id=request_id, response=response)

    if status == 429:
        return RateLimitError(message, retry_after=retry_after_from(response), **kwargs)
    if status >= 500:
        return ServerError(message, **kwargs)
    return _STATUS_MAP.get(status, APIStatusError)(message, **kwargs)
