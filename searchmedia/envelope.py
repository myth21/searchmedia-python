"""Builds the response envelope (status, meta, pagination, timestamp, request id) every endpoint returns."""

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

TERMS = "/api/searchmedia/v1/doc/"

HTTP_STATUSES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    410: "This method has been deprecated and is no longer available",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
}


def meta_body(
    code: int,
    *,
    request_id: str,
    meta: Mapping[str, Any] | None = None,
    pagination: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status_code": code,
        "status_text": HTTP_STATUSES[code],
        "meta": dict(meta or {}),
        "pagination": dict(pagination or {}),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "request_id": request_id,
        "terms": TERMS,
    }


def pagination(*, limit: int, offset: int, items_count: int) -> dict[str, int]:
    return {"limit": limit, "offset": offset, "items_count": items_count}


def error_body(
    code: int,
    *,
    request_id: str,
    message: str,
    help_url: str,
    details: Sequence[str] = (),
    error_id: str = "",
) -> dict[str, Any]:
    body = meta_body(code, request_id=request_id)
    body["error"] = {
        "id": error_id,
        "message": message,
        "help": help_url,
        "details": list(details),
    }

    return body
