from __future__ import annotations

from datetime import date, datetime


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


def select_rotating_feeds(feeds: list[str | dict], day: date,
                          rotation_days: int = 3) -> list[str | dict]:
    """Keep preferred feeds daily and rotate ordinary feeds in stable groups."""
    if rotation_days < 1:
        raise ValueError("Medium feed rotation_days must be at least one")
    selected: list[str | dict] = []
    ordinary_index = 0
    group = day.toordinal() % rotation_days
    for feed in feeds:
        daily = isinstance(feed, dict) and (
            bool(feed.get("daily", False)) or float(feed.get("weight", 1.0)) > 1.0
        )
        if daily or rotation_days == 1:
            selected.append(feed)
        else:
            if ordinary_index % rotation_days == group:
                selected.append(feed)
            ordinary_index += 1
    return selected
