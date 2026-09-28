"""Tests klipy.map_items with missing and null fields."""

import json
import unittest
from pathlib import Path

from searchmedia.klipy import map_items

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "edge-cases"


class KlipyDefaultsTest(unittest.TestCase):
    def test_matches_the_hand_built_fixture(self) -> None:
        fixture = json.loads((FIXTURES_DIR / "klipy-search.json").read_text())
        expected = json.loads((FIXTURES_DIR / "klipy-items.json").read_text())

        self.assertEqual(map_items(fixture), expected)


if __name__ == "__main__":
    unittest.main()
