"""Tests for RequestThrottle windowing and cleanup.

Time and randomness are patched to keep the tests deterministic.
"""

import unittest
from unittest import mock

from searchmedia.throttle import ENTRY_TTL_SECONDS, RequestThrottle, RequestTooSoon


class ThrottleWindowTest(unittest.TestCase):
    def test_first_request_for_an_ip_passes(self) -> None:
        throttle = RequestThrottle(seconds=5.0)

        throttle.throttle_by_ip("1.1.1.1")  # does not raise

    def test_second_request_within_the_window_is_too_soon(self) -> None:
        throttle = RequestThrottle(seconds=5.0)

        with mock.patch("searchmedia.throttle.time.monotonic", side_effect=[0.0, 1.0]):
            throttle.throttle_by_ip("1.1.1.1")

            with self.assertRaises(RequestTooSoon):
                throttle.throttle_by_ip("1.1.1.1")

    def test_a_request_after_the_window_passes(self) -> None:
        throttle = RequestThrottle(seconds=5.0)

        with mock.patch("searchmedia.throttle.time.monotonic", side_effect=[0.0, 5.0]):
            throttle.throttle_by_ip("1.1.1.1")
            throttle.throttle_by_ip("1.1.1.1")  # does not raise

    def test_different_ips_are_throttled_independently(self) -> None:
        throttle = RequestThrottle(seconds=5.0)

        with mock.patch("searchmedia.throttle.time.monotonic", side_effect=[0.0, 0.1]):
            throttle.throttle_by_ip("1.1.1.1")
            throttle.throttle_by_ip("2.2.2.2")  # does not raise


class ThrottleGarbageCollectionTest(unittest.TestCase):
    def test_evicts_only_entries_older_than_the_ttl(self) -> None:
        throttle = RequestThrottle()

        with (
            mock.patch("searchmedia.throttle.time.monotonic", return_value=0.0),
            mock.patch("searchmedia.throttle.random.random", return_value=0.5),
        ):
            throttle.throttle_by_ip("1.1.1.1")

        with (
            mock.patch(
                "searchmedia.throttle.time.monotonic",
                return_value=ENTRY_TTL_SECONDS + 1,
            ),
            mock.patch("searchmedia.throttle.random.random", return_value=0.0),
        ):
            throttle.throttle_by_ip("2.2.2.2")

        self.assertNotIn("1.1.1.1", throttle._last_request_at)
        self.assertIn("2.2.2.2", throttle._last_request_at)

    def test_no_eviction_when_the_random_roll_misses(self) -> None:
        throttle = RequestThrottle()

        with (
            mock.patch("searchmedia.throttle.time.monotonic", return_value=0.0),
            mock.patch("searchmedia.throttle.random.random", return_value=0.5),
        ):
            throttle.throttle_by_ip("1.1.1.1")

        with (
            mock.patch(
                "searchmedia.throttle.time.monotonic",
                return_value=ENTRY_TTL_SECONDS + 1,
            ),
            mock.patch("searchmedia.throttle.random.random", return_value=0.5),
        ):
            throttle.throttle_by_ip("2.2.2.2")

        self.assertIn("1.1.1.1", throttle._last_request_at)


if __name__ == "__main__":
    unittest.main()
