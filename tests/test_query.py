"""read_query() and the InvalidSearchQuery cases it raises."""

import unittest

from starlette.datastructures import QueryParams

from searchmedia.query import InvalidSearchQuery, SearchQuery, read_query

AVAILABLE = ("klipy", "google", "giphy")
MAX_LIMIT = 30


def _query(pairs: list[tuple[str, str]]) -> QueryParams:
    return QueryParams(pairs)


class TextTest(unittest.TestCase):
    def test_missing_text_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([]), AVAILABLE, MAX_LIMIT)

    def test_repeated_text_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([("text", "cats"), ("text", "dogs")]), AVAILABLE, MAX_LIMIT)

    def test_blank_text_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([("text", "   ")]), AVAILABLE, MAX_LIMIT)

    def test_text_longer_than_32_characters_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([("text", "a" * 33)]), AVAILABLE, MAX_LIMIT)

    def test_text_is_trimmed(self) -> None:
        query = read_query(_query([("text", "  cats  ")]), AVAILABLE, MAX_LIMIT)

        self.assertEqual(query.text, "cats")


class ServiceNamesTest(unittest.TestCase):
    def test_missing_service_means_every_available_service(self) -> None:
        query = read_query(_query([("text", "cats")]), AVAILABLE, MAX_LIMIT)

        self.assertIsNone(query.service_names)

    def test_one_requested_service_is_kept(self) -> None:
        query = read_query(
            _query([("text", "cats"), ("service", "klipy")]), AVAILABLE, MAX_LIMIT
        )

        self.assertEqual(query.service_names, ("klipy",))

    def test_unknown_service_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([("text", "cats"), ("service", "imgur")]), AVAILABLE, MAX_LIMIT)


class LimitTest(unittest.TestCase):
    def test_missing_limit_defaults_to_the_max(self) -> None:
        query = read_query(_query([("text", "cats")]), AVAILABLE, MAX_LIMIT)

        self.assertEqual(query.limit, MAX_LIMIT)

    def test_limit_above_the_max_is_capped(self) -> None:
        query = read_query(_query([("text", "cats"), ("limit", "1000")]), AVAILABLE, MAX_LIMIT)

        self.assertEqual(query.limit, MAX_LIMIT)

    def test_limit_within_the_max_is_kept(self) -> None:
        query = read_query(_query([("text", "cats"), ("limit", "5")]), AVAILABLE, MAX_LIMIT)

        self.assertEqual(query.limit, 5)

    def test_zero_limit_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([("text", "cats"), ("limit", "0")]), AVAILABLE, MAX_LIMIT)

    def test_non_integer_limit_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([("text", "cats"), ("limit", "abc")]), AVAILABLE, MAX_LIMIT)

    def test_negative_limit_is_invalid(self) -> None:
         # Negative values are rejected as non-integers.
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([("text", "cats"), ("limit", "-5")]), AVAILABLE, MAX_LIMIT)

    def test_non_ascii_digit_limit_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([("text", "cats"), ("limit", "²")]), AVAILABLE, MAX_LIMIT)

    def test_repeated_limit_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(
                _query([("text", "cats"), ("limit", "5"), ("limit", "6")]), AVAILABLE, MAX_LIMIT
            )


class OffsetTest(unittest.TestCase):
    def test_missing_offset_defaults_to_zero(self) -> None:
        query = read_query(_query([("text", "cats")]), AVAILABLE, MAX_LIMIT)

        self.assertEqual(query.offset, 0)

    def test_given_offset_is_kept(self) -> None:
        query = read_query(_query([("text", "cats"), ("offset", "10")]), AVAILABLE, MAX_LIMIT)

        self.assertEqual(query.offset, 10)

    def test_non_integer_offset_is_invalid(self) -> None:
        with self.assertRaises(InvalidSearchQuery):
            read_query(_query([("text", "cats"), ("offset", "abc")]), AVAILABLE, MAX_LIMIT)


class ReadQueryResultTest(unittest.TestCase):
    def test_full_query_is_assembled_into_one_object(self) -> None:
        query = read_query(
            _query(
                [
                    ("text", "cats"),
                    ("service", "klipy"),
                    ("service", "google"),
                    ("limit", "7"),
                    ("offset", "3"),
                ]
            ),
            AVAILABLE,
            MAX_LIMIT,
        )

        self.assertEqual(
            query, SearchQuery(text="cats", service_names=("klipy", "google"), limit=7, offset=3)
        )


if __name__ == "__main__":
    unittest.main()
