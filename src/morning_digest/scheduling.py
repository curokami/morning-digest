from __future__ import annotations

from datetime import datetime


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def source_is_due(schedule: dict | None, now: datetime) -> bool:
    """Return whether a source should be polled at this invocation."""
    schedule = schedule or {"frequency": "daily"}
    frequency = str(schedule.get("frequency", "daily")).casefold()
    if frequency == "daily":
        return True
    if frequency == "weekly":
        weekday = str(schedule.get("weekday", "")).casefold()
        if weekday not in WEEKDAYS:
            raise ValueError("A weekly source schedule requires a valid weekday")
        return now.weekday() == WEEKDAYS[weekday]
    raise ValueError(f"Unsupported source frequency: {frequency}")
