"""Tests google.map_items against a recorded Google Custom Search fixture."""

import json
import unittest
from pathlib import Path

from searchmedia.google import map_items

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "recorded"


class GoogleMapperTest(unittest.TestCase):
    def test_matches_the_recorded_fixture(self) -> None:
        fixture = json.loads((FIXTURES_DIR / "google-search.json").read_text())
        expected = json.loads((FIXTURES_DIR / "google-items.json").read_text())

        self.assertEqual(map_items(fixture), expected)


if __name__ == "__main__":
    unittest.main()
