"""Simulated multi-tenant scheduling SaaS API."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestContext:
    user_id: str
    tenant_id: str
    permissions: frozenset[str]


class SchedulingAPIError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# Simulated records in a shared multi-tenant database.
CONFLICTS = [
    {
        "tenant_id": "university_a",
        "term_id": "2027-SPRING",
        "conflict_id": "conflict-001",
        "type": "ROOM_OVERLAP",
        "section_ids": ["BIO101-01", "CHEM101-01"],
        "day": "MON",
        "room_id": "R101",
    },
    {
        "tenant_id": "university_a",
        "term_id": "2027-SPRING",
        "conflict_id": "conflict-002",
        "type": "INSTRUCTOR_OVERLAP",
        "section_ids": ["BIO101-01", "BIO201-01"],
        "day": "MON",
        "instructor_id": "I001",
    },
    {
        "tenant_id": "university_b",
        "term_id": "2027-SPRING",
        "conflict_id": "conflict-003",
        "type": "ROOM_OVERLAP",
        "section_ids": ["MATH101-01", "PHYS101-01"],
        "day": "TUE",
        "room_id": "R205",
    },
]


def get_schedule_conflicts(context: RequestContext, term_id: str):
    """Return only conflicts authorized for the request context."""

    if not context.user_id or not context.tenant_id:
        raise SchedulingAPIError(
            "UNAUTHENTICATED",
            "A verified user and tenant are required.",
        )

    if "schedule:read" not in context.permissions:
        raise SchedulingAPIError(
            "PERMISSION_DENIED",
            "User cannot read scheduling data.",
        )

    if not isinstance(term_id, str) or not term_id.strip():
        raise SchedulingAPIError(
            "INVALID_ARGUMENT",
            "A valid term_id is required.",
        )

    conflicts = [
        {
            key: value
            for key, value in record.items()
            if key != "tenant_id"
        }
        for record in CONFLICTS
        if record["tenant_id"] == context.tenant_id
        and record["term_id"] == term_id
    ]

    return {
        "status": "success",
        "term_id": term_id,
        "conflicts": conflicts,
        "total_count": len(conflicts),
    }
