"""Tests google.map_items with missing and null fields."""

import json
import unittest
from pathlib import Path

from searchmedia.google import map_items

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "edge-cases"


class GoogleDefaultsTest(unittest.TestCase):
    def test_matches_the_hand_built_fixture(self) -> None:
        fixture = json.loads((FIXTURES_DIR / "google-search.json").read_text())
        expected = json.loads((FIXTURES_DIR / "google-items.json").read_text())

        self.assertEqual(map_items(fixture), expected)


if __name__ == "__main__":
    unittest.main()
