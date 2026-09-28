"""Calls each configured search service and merges the results into one list."""

import json
import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from searchmedia import giphy, google, klipy
from searchmedia.client import HttpClient, HttpResponse
from searchmedia.config import Config
from searchmedia.plan import ServiceLimitPlan
from searchmedia.query import SearchQuery

logger = logging.getLogger(__name__)

IMPLEMENTED_SERVICES = (klipy.SERVICE_NAME, google.SERVICE_NAME, giphy.SERVICE_NAME)


@dataclass(frozen=True)
class ServiceCallResult:
    decoded_body: dict[str, Any]
    is_available: bool
    processing_time: float


def call_service(
    client: HttpClient, url: str, headers: dict[str, str] | None = None
) -> ServiceCallResult:
    start = time.monotonic()

    try:
        response = client.get(url, headers)
    except Exception:
        # HttpClient.get() already turns network failures into an HttpResponse, so getting here means a bug.
        # Only the host is logged, never the full URL: the query string contains the API key.
        logger.exception("Unexpected error calling %s", urlsplit(url).netloc)
        response = HttpResponse.none()

    is_available = response.is_ok()
    processing_time = round(time.monotonic() - start, 2)

    if not is_available:
        return ServiceCallResult({}, False, processing_time)

    return ServiceCallResult(_decode_body(response.body), True, processing_time)


def _decode_body(body: str) -> dict[str, Any]:
    try:
        decoded = json.loads(body)
    except json.JSONDecodeError:
        return {}

    return decoded if isinstance(decoded, dict) else {}


def search(
    client: HttpClient,
    config: Config,
    query: SearchQuery,
    available_service_names: Sequence[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Returns (items, meta): items merged from all services, and per-service call metadata."""

    limit_plan = ServiceLimitPlan.for_request(
        available_service_names, query.service_names, query.limit
    )

    items: list[dict[str, Any]] = []
    meta: dict[str, Any] = {}

    for service_name in IMPLEMENTED_SERVICES:
        limit = limit_plan.limit_for(service_name)
        if limit <= 0:
            continue

        service_items, service_meta = _call(service_name, client, config, query, limit)
        meta[service_name] = service_meta
        items.extend(service_items)

    return items, meta


@dataclass(frozen=True)
class _ServiceAdapter:
    build_url: Callable[[Config, SearchQuery, int], str]
    headers: dict[str, str] | None
    map_items: Callable[[dict[str, Any]], list[dict[str, Any]]]
    terms: str


_SERVICE_ADAPTERS: dict[str, _ServiceAdapter] = {
    klipy.SERVICE_NAME: _ServiceAdapter(
        build_url=lambda config, query, limit: klipy.build_search_url(
            config.klipy_key, query.text, limit, query.offset
        ),
        headers=klipy.REQUEST_HEADERS,
        map_items=klipy.map_items,
        terms=klipy.LINK_TO_TERMS,
    ),
    google.SERVICE_NAME: _ServiceAdapter(
        build_url=lambda config, query, limit: google.build_search_url(
            config.google_key, config.google_cx, query.text, limit, query.offset
        ),
        headers=None,
        map_items=google.map_items,
        terms=google.LINK_TO_TERMS,
    ),
    giphy.SERVICE_NAME: _ServiceAdapter(
        build_url=lambda config, query, limit: giphy.build_search_url(
            config.giphy_key, query.text, limit, query.offset
        ),
        headers=None,
        map_items=giphy.map_items,
        terms=giphy.LINK_TO_TERMS,
    ),
}


def _call(
    service_name: str, client: HttpClient, config: Config, query: SearchQuery, limit: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    adapter = _SERVICE_ADAPTERS[service_name]

    url = adapter.build_url(config, query, limit)
    result = call_service(client, url, adapter.headers)
    service_items = adapter.map_items(result.decoded_body)

    return service_items, {
        "is_available": result.is_available,
        "processing_time": result.processing_time,
        "items_count": len(service_items),
        "terms": adapter.terms,
    }
