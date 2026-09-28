"""Builds Google Custom Search request URLs and maps its JSON response into searchmedia items."""

from typing import Any
from urllib.parse import urlencode

from searchmedia.mapping import iterable_items, nested

SERVICE_NAME = "google"
SITE = "googleapis.com"
LINK_TO_TERMS = "https://developers.google.com/terms"

_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
SEARCH_ITEMS_LIMIT = 10

# Custom Search returns at most 10 results, regardless of num.
_LIMIT_MAX = 10
_SEARCH_TYPE_IMAGE = "image"
_IMG_SIZE_LARGE = "large"


def build_search_url(
    auth_key: str,
    client_key: str,
    search_text: str,
    limit: int = SEARCH_ITEMS_LIMIT,
    offset: int = 0,
) -> str:
    return _SEARCH_URL + "?" + urlencode(
        {
            "q": search_text,
            "searchType": _SEARCH_TYPE_IMAGE,
            "imgSize": _IMG_SIZE_LARGE,
            "key": auth_key,
            "cx": client_key,
            "num": min(limit, _LIMIT_MAX),
            "start": offset,
        },
    )


def map_items(decoded_response: dict[str, Any]) -> list[dict[str, Any]]:
    items = []

    for response_item in iterable_items(decoded_response.get("items")):
        if not isinstance(response_item, dict):
            continue

        # The original image first, Google thumbnail as a fallback.
        url = response_item.get("link")

        if not isinstance(url, str) or url == "":
            continue

        title = response_item.get("title")
        desc = response_item.get("snippet")
        mime_type = response_item.get("mime")
        author = response_item.get("displayLink")

        items.append(
            {
                "url": url,
                # Always include the key, even when the value is null.
                "fallback_url": nested(response_item, "image", "thumbnailLink"),
                "mime_type": "" if mime_type is None else str(mime_type),
                "title": "" if title is None else str(title),
                "desc": "" if desc is None else str(desc),
                "tags": [],
                "author": "" if author is None else author,
                "source": SITE,
                "html_tag_name": "img",
                "type": "image",
            }
        )

    return items
