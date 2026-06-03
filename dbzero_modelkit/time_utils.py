"""Reusable date and datetime helpers for dbzero model utilities."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional


def normalize_start(value: Optional[datetime | date]) -> datetime:
    """Normalize a start value to datetime, treating None as datetime.min."""
    if value is None:
        return datetime.min
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())
    return value


def normalize_end(value: Optional[datetime | date]) -> datetime:
    """Normalize an end value to datetime, treating None as datetime.max."""
    if value is None:
        return datetime.max
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.max.time())
    return value
