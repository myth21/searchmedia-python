"""Builds Giphy search request URLs and maps its JSON response into searchmedia items."""

from typing import Any
from urllib.parse import urlencode

from searchmedia.mapping import iterable_items, nested

SERVICE_NAME = "giphy"
SITE = "giphy.com"
LINK_TO_TERMS = (
    "https://support.giphy.com/hc/en-us/articles/"
    "360020027752-GIPHY-User-Terms-of-Service"
)

_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"
_LIMIT_MAX = 100


def build_search_url(auth_key: str, search_text: str, limit: int, offset: int = 0) -> str:
    return _SEARCH_URL + "?" + urlencode(
        {
            "q": search_text,
            "api_key": auth_key,
            "limit": min(limit, _LIMIT_MAX),
            "offset": offset,
        },
    )


def map_items(decoded_response: dict[str, Any]) -> list[dict[str, Any]]:
    items = []

    for response_item in iterable_items(decoded_response.get("data")):
        if not isinstance(response_item, dict):
            continue

        url = nested(response_item, "images", "original", "url")

        if not isinstance(url, str) or url == "":
            continue

        title = response_item.get("title")
        author = nested(response_item, "user", "display_name")

        items.append(
            {
                "url": url,
                # Giphy doesn't send a mime type, and search only returns gifs.
                "mime_type": "image/gif",
                "title": "" if title is None else str(title),
                "desc": "",
                "tags": [],
                "source": SITE,
                # Preserve the original value.
                "author": "" if author is None else author,
                "html_tag_name": "img",
                "type": "image",
            }
        )

    return items
