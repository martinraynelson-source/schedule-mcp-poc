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


# Simulated academic sections for multiple tenants.
SECTIONS = [
    {
        "tenant_id": "university_a",
        "term_id": "2027-SPRING",
        "id": "BIO101-01",
        "course": "BIO101",
        "instructor": "I001",
        "room": "R101",
        "day": "MON",
        "start": "09:00",
        "end": "10:15",
        "enrollment": 35,
    },
    {
        "tenant_id": "university_a",
        "term_id": "2027-SPRING",
        "id": "CHEM101-01",
        "course": "CHEM101",
        "instructor": "I002",
        "room": "R101",
        "day": "MON",
        "start": "09:30",
        "end": "10:45",
        "enrollment": 28,
    },
    {
        "tenant_id": "university_a",
        "term_id": "2027-SPRING",
        "id": "BIO201-01",
        "course": "BIO201",
        "instructor": "I001",
        "room": "R102",
        "day": "MON",
        "start": "10:00",
        "end": "11:15",
        "enrollment": 25,
    },
    {
        "tenant_id": "university_a",
        "term_id": "2027-SPRING",
        "id": "ENG101-01",
        "course": "ENG101",
        "instructor": "I003",
        "room": "R201",
        "day": "MON",
        "start": "11:00",
        "end": "12:15",
        "enrollment": 45,
    },
    {
        "tenant_id": "university_b",
        "term_id": "2027-SPRING",
        "id": "MATH101-01",
        "course": "MATH101",
        "instructor": "I101",
        "room": "R205",
        "day": "TUE",
        "start": "09:00",
        "end": "10:15",
        "enrollment": 32,
    },
]


def get_sections_by_term(context: RequestContext, term_id: str):
    """Return sections belonging to the authorized tenant and term."""

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

    sections = [
        {
            key: value
            for key, value in record.items()
            if key != "tenant_id"
        }
        for record in SECTIONS
        if record["tenant_id"] == context.tenant_id
        and record["term_id"] == term_id
    ]

    return {
        "status": "success",
        "term_id": term_id,
        "count": len(sections),
        "sections": sections,
    }


# Simulated room inventory scoped to each institution.
ROOMS = [
    {"tenant_id": "university_a", "id": "R101", "capacity": 40},
    {"tenant_id": "university_a", "id": "R102", "capacity": 30},
    {"tenant_id": "university_a", "id": "R201", "capacity": 60},
    {"tenant_id": "university_b", "id": "R205", "capacity": 40},
    {"tenant_id": "university_b", "id": "R206", "capacity": 50},
]


def find_available_rooms(
    context: RequestContext,
    term_id: str,
    day: str,
    start: str,
    end: str,
    minimum_capacity: int = 0,
):
    """Find available rooms belonging to the authorized tenant."""

    from datetime import datetime

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

    if day not in {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}:
        raise SchedulingAPIError(
            "INVALID_ARGUMENT",
            "Invalid day of week.",
        )

    try:
        start_time = datetime.strptime(start, "%H:%M").time()
        end_time = datetime.strptime(end, "%H:%M").time()
    except (ValueError, TypeError):
        raise SchedulingAPIError(
            "INVALID_ARGUMENT",
            "Times must use HH:MM format.",
        )

    if start_time >= end_time:
        raise SchedulingAPIError(
            "INVALID_ARGUMENT",
            "Start time must precede end time.",
        )

    if (
        not isinstance(minimum_capacity, int)
        or isinstance(minimum_capacity, bool)
        or minimum_capacity < 0
    ):
        raise SchedulingAPIError(
            "INVALID_ARGUMENT",
            "Minimum capacity must be a nonnegative integer.",
        )

    def overlaps(a_start, a_end, b_start, b_end):
        return a_start < b_end and b_start < a_end

    occupied = {
        section["room"]
        for section in SECTIONS
        if section["tenant_id"] == context.tenant_id
        and section["term_id"] == term_id
        and section["day"] == day
        and overlaps(start, end, section["start"], section["end"])
    }

    available = [
        {
            "id": room["id"],
            "capacity": room["capacity"],
        }
        for room in ROOMS
        if room["tenant_id"] == context.tenant_id
        and room["id"] not in occupied
        and room["capacity"] >= minimum_capacity
    ]

    return {
        "status": "success",
        "term_id": term_id,
        "day": day,
        "start": start,
        "end": end,
        "rooms": available,
        "count": len(available),
    }
