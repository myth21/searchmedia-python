"""Tests for service.search() using a fake HTTP client.

A failed service should not affect results from the other services.
"""

import json
import unittest
from pathlib import Path

from searchmedia import service
from searchmedia.client import HttpResponse
from searchmedia.config import Config
from searchmedia.query import SearchQuery

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "edge-cases"

CONFIG = Config(
    host="127.0.0.1",
    port=80,
    reload=False,
    specification_url="http://example.invalid/swagger/",
    documentation_url="http://example.invalid/doc/",
    giphy_key="giphy-key",
    klipy_key="klipy-key",
    google_key="google-key",
    google_cx="google-cx",
)


class FakeHttpClient:
    """Returns a fixture based on the service host."""

    def __init__(self, responses_by_url_substring: dict[str, HttpResponse]) -> None:
        self._responses = responses_by_url_substring

    def get(self, url: str, headers: dict[str, str] | None = None) -> HttpResponse:
        for substring, response in self._responses.items():
            if substring in url:
                return response

        raise AssertionError(f"FakeHttpClient got an unexpected url: {url}")


def _fixture_response(name: str) -> HttpResponse:
    body = (FIXTURES_DIR / f"{name}-search.json").read_text()
    return HttpResponse(200, body)


def _fixture_items(name: str) -> list[dict]:
    return json.loads((FIXTURES_DIR / f"{name}-items.json").read_text())


class SearchMixedAvailabilityTest(unittest.TestCase):
    def test_one_failed_service_does_not_affect_the_others(self) -> None:
        client = FakeHttpClient(
            {
                "api.klipy.com": _fixture_response("klipy"),
                "googleapis.com": _fixture_response("google"),
                # Giphy times out: no response at all.
                "giphy.com": HttpResponse.none(),
            }
        )
        query = SearchQuery(text="cats", service_names=None, limit=10, offset=0)

        items, meta = service.search(client, CONFIG, query, service.IMPLEMENTED_SERVICES)

        self.assertEqual(meta["giphy"]["is_available"], False)
        self.assertEqual(meta["giphy"]["items_count"], 0)

        self.assertEqual(meta["klipy"]["is_available"], True)
        self.assertEqual(meta["klipy"]["items_count"], len(_fixture_items("klipy")))

        self.assertEqual(meta["google"]["is_available"], True)
        self.assertEqual(meta["google"]["items_count"], len(_fixture_items("google")))

        # The failed service contributes nothing to the merged item list; the other two do.
        expected_items = _fixture_items("klipy") + _fixture_items("google")
        self.assertEqual(len(items), len(expected_items))
        for item in _fixture_items("klipy") + _fixture_items("google"):
            self.assertIn(item, items)

    def test_a_non_200_answer_is_also_unavailable(self) -> None:
        client = FakeHttpClient(
            {
                "api.klipy.com": HttpResponse(500, ""),
                "googleapis.com": _fixture_response("google"),
                # Not checked below - an empty but valid body is enough.
                "giphy.com": HttpResponse(200, "{}"),
            }
        )
        query = SearchQuery(text="cats", service_names=None, limit=10, offset=0)

        _, meta = service.search(client, CONFIG, query, service.IMPLEMENTED_SERVICES)

        self.assertEqual(meta["klipy"]["is_available"], False)
        self.assertEqual(meta["klipy"]["items_count"], 0)
        self.assertEqual(meta["google"]["is_available"], True)


if __name__ == "__main__":
    unittest.main()
