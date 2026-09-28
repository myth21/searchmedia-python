"""ServiceLimitPlan.for_request(): how a requested limit is split across services."""

import unittest

from searchmedia.plan import ServiceLimitPlan

AVAILABLE = ("klipy", "google", "giphy")


class ServiceLimitPlanTest(unittest.TestCase):
    def test_splits_evenly_when_the_limit_divides_cleanly(self) -> None:
        plan = ServiceLimitPlan.for_request(AVAILABLE, None, 9)

        self.assertEqual(plan.limit_for("klipy"), 3)
        self.assertEqual(plan.limit_for("google"), 3)
        self.assertEqual(plan.limit_for("giphy"), 3)

    def test_gives_the_remainder_to_the_first_services_in_available_order(self) -> None:
        plan = ServiceLimitPlan.for_request(AVAILABLE, None, 10)

        self.assertEqual(plan.limit_for("klipy"), 4)
        self.assertEqual(plan.limit_for("google"), 3)
        self.assertEqual(plan.limit_for("giphy"), 3)

    def test_none_means_every_available_service(self) -> None:
        plan = ServiceLimitPlan.for_request(AVAILABLE, None, 3)

        self.assertEqual(plan.limit_for("klipy"), 1)
        self.assertEqual(plan.limit_for("google"), 1)
        self.assertEqual(plan.limit_for("giphy"), 1)

    def test_only_requested_services_get_a_share(self) -> None:
        plan = ServiceLimitPlan.for_request(AVAILABLE, ("giphy", "klipy"), 10)

        self.assertEqual(plan.limit_for("klipy"), 5)
        self.assertEqual(plan.limit_for("giphy"), 5)
        self.assertEqual(plan.limit_for("google"), 0)

    def test_requested_order_does_not_affect_who_gets_the_remainder(self) -> None:
         # Remainder follows AVAILABLE, not the requested service order.
        plan = ServiceLimitPlan.for_request(AVAILABLE, ("giphy", "klipy"), 5)

        self.assertEqual(plan.limit_for("klipy"), 3)
        self.assertEqual(plan.limit_for("giphy"), 2)

    def test_a_requested_service_that_is_not_available_is_ignored(self) -> None:
        plan = ServiceLimitPlan.for_request(AVAILABLE, ("klipy", "imgur"), 4)

        self.assertEqual(plan.limit_for("klipy"), 4)

    def test_no_overlap_between_requested_and_available_gives_every_service_zero(self) -> None:
        plan = ServiceLimitPlan.for_request(AVAILABLE, ("imgur",), 10)

        self.assertEqual(plan.limit_for("klipy"), 0)
        self.assertEqual(plan.limit_for("google"), 0)
        self.assertEqual(plan.limit_for("giphy"), 0)

    def test_an_unknown_service_name_gets_zero(self) -> None:
        plan = ServiceLimitPlan.for_request(AVAILABLE, None, 9)

        self.assertEqual(plan.limit_for("imgur"), 0)


if __name__ == "__main__":
    unittest.main()
