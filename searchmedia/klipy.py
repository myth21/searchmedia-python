"""Builds Klipy search request URLs and maps its JSON response into searchmedia items."""

from typing import Any
from urllib.parse import urlencode

from searchmedia.mapping import iterable_items, nested

SERVICE_NAME = "klipy"
SITE = "api.klipy.com"
LINK_TO_TERMS = "https://klipy.com/support/terms-services"
# Only Klipy requires a request header.
REQUEST_HEADERS = {"Content-Type": "application/json"}

_SEARCH_URL = "https://api.klipy.com/v2/search"
SEARCH_ITEMS_LIMIT = 20


def build_search_url(
    auth_key: str, search_text: str, limit: int = SEARCH_ITEMS_LIMIT, offset: int = 0
) -> str:
    return _SEARCH_URL + "?" + urlencode(
        {
            "key": auth_key,
            "q": search_text,
            "limit": limit,
            "pos": offset,
        },
    )


def map_items(decoded_response: dict[str, Any]) -> list[dict[str, Any]]:
    items = []

    for response_item in iterable_items(decoded_response.get("results")):
        if not isinstance(response_item, dict):
            continue

        url = nested(response_item, "media_formats", "gif", "url")

        if not isinstance(url, str) or url == "":
            continue

        title = response_item.get("title")
        desc = response_item.get("content_description")
        user = response_item.get("user")
        author = user.get("profile_url", "") if isinstance(user, dict) else ""

        items.append(
            {
                "url": url,
                "mime_type": "image/gif",
                "title": "" if title is None else str(title),
                "desc": "" if desc is None else str(desc),
                "tags": iterable_items(response_item.get("tags")),
                "source": SITE,
                # Preserve the original value.
                "author": "" if author is None else author,
                "html_tag_name": "img",
                "type": "image",
            }
        )

    return items
