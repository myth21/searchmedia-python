"""The query string as this endpoint reads it."""

from collections.abc import Sequence
from dataclasses import dataclass

from starlette.datastructures import QueryParams

MIN_SEARCH_TEXT_LENGTH = 1
MAX_SEARCH_TEXT_LENGTH = 32


class InvalidSearchQuery(Exception):
    """Its message goes into error.message of the response."""


@dataclass(frozen=True)
class SearchQuery:
    text: str
    # None means all available services.
    service_names: tuple[str, ...] | None
    limit: int
    offset: int


def read_query(
    params: QueryParams, available_service_names: Sequence[str], max_limit: int
) -> SearchQuery:
    return SearchQuery(
        text=_read_text(params),
        service_names=_read_service_names(params, available_service_names),
        limit=_read_limit(params, max_limit),
        offset=_read_offset(params),
    )


def _read_text(params: QueryParams) -> str:
    given = params.getlist("text")

    if not given:
        raise InvalidSearchQuery("The `text` parameter is missing.")

    if len(given) > 1:
        raise InvalidSearchQuery("The `text` parameter must be given once.")

    text = given[0].strip()

    if text == "":
        raise InvalidSearchQuery("The `text` parameter is empty.")

    if not MIN_SEARCH_TEXT_LENGTH <= len(text) <= MAX_SEARCH_TEXT_LENGTH:
        raise InvalidSearchQuery(
            f"The `text` must be between {MIN_SEARCH_TEXT_LENGTH} and "
            f"{MAX_SEARCH_TEXT_LENGTH} characters long."
        )

    return text


def _read_service_names(
    params: QueryParams, available_service_names: Sequence[str]
) -> tuple[str, ...] | None:
    values = params.getlist("service")

    if not values:
        return None

    requested = tuple(values)

    if set(requested) - set(available_service_names):
        raise InvalidSearchQuery(
            "The value of the `service` parameter must be one of the allowed values: "
            + ", ".join(available_service_names)
            + "."
        )

    return requested


def _read_limit(params: QueryParams, max_limit: int) -> int:
    raw = _read_single_value(params, "limit")
    value = _read_integer(raw, "limit")

    if value is None:
        return max_limit

    if value < 1:
        raise InvalidSearchQuery(
            "The value of the `limit` parameter must be greater than 0."
        )

    return min(value, max_limit)


def _read_offset(params: QueryParams) -> int:
    raw = _read_single_value(params, "offset")
    value = _read_integer(raw, "offset")

    return 0 if value is None else value


def _read_single_value(params: QueryParams, name: str) -> str | None:
    values = params.getlist(name)

    if not values:
        return None

    if len(values) > 1:
        raise InvalidSearchQuery(
            f"The `{name}` parameter must be given once."
        )

    return values[0]


def _read_integer(raw: str | None, name: str) -> int | None:
    if raw is None:
        return None

    # isdigit() alone also accepts digits like "²" that int() can't parse.
    if not (raw.isascii() and raw.isdigit()):
        raise InvalidSearchQuery(
            f"The value of the `{name}` parameter must be an integer."
        )

    return int(raw)