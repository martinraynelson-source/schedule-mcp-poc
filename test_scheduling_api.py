import unittest

from scheduling_api import (
    RequestContext,
    SchedulingAPIError,
    get_schedule_conflicts,
)


class TestSchedulingAPI(unittest.TestCase):

    def test_university_a_isolation(self):
        context = RequestContext(
            user_id="user-a",
            tenant_id="university_a",
            permissions=frozenset({"schedule:read"}),
        )

        result = get_schedule_conflicts(context, "2027-SPRING")

        self.assertEqual(result["total_count"], 2)
        self.assertEqual(
            {c["conflict_id"] for c in result["conflicts"]},
            {"conflict-001", "conflict-002"},
        )

    def test_university_b_isolation(self):
        context = RequestContext(
            user_id="user-b",
            tenant_id="university_b",
            permissions=frozenset({"schedule:read"}),
        )

        result = get_schedule_conflicts(context, "2027-SPRING")

        self.assertEqual(result["total_count"], 1)
        self.assertEqual(
            result["conflicts"][0]["conflict_id"],
            "conflict-003",
        )

    def test_unauthorized_user(self):
        context = RequestContext(
            user_id="user-a",
            tenant_id="university_a",
            permissions=frozenset(),
        )

        with self.assertRaises(SchedulingAPIError) as error:
            get_schedule_conflicts(context, "2027-SPRING")

        self.assertEqual(
            error.exception.code,
            "PERMISSION_DENIED",
        )


if __name__ == "__main__":
    unittest.main()
