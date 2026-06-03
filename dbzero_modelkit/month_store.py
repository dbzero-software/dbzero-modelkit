"""Sparse month-indexed object store backed by dbzero."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

import dbzero as db0

from dbzero_modelkit.rpc_integration import rpc as db0_rpc


@db0.memo(no_default_tags=True)
class MonthStore:
    """General-purpose container for storing one object per month."""

    def __init__(self, item_type: type, base_year: int = 2025) -> None:
        self.__item_type = item_type
        self.__base_year = base_year
        self.__months = []

    def __str__(self) -> str:
        """Return a YYYY-MM span for stored months, or an empty string."""
        span = self.get_span()
        if not span:
            return ""
        start, end = span
        return f"{start.year:04d}-{start.month:02d} - {end.year:04d}-{end.month:02d}"

    def __get_index(self, month: date) -> int:
        """Return the month index relative to the base year."""
        return (month.year * 12 + month.month - self.__base_year * 12) - 1

    @db0_rpc.remote
    def get_month(self, month: date, create: bool = False) -> Any:
        """Return the stored month object, optionally creating it when missing."""
        index = self.__get_index(month)

        if index < 0:
            raise ValueError(
                f"Month {month.year}-{month.month:02d} is before base year "
                f"{self.__base_year}"
            )

        if index < len(self.__months):
            existing_item = self.__months[index]
            if existing_item is not None:
                return existing_item

        if not create:
            raise ValueError(
                f"No item found for month {month.year}-{month.month:02d} and create=False"
            )

        while len(self.__months) <= index:
            self.__months.append(None)

        new_item = self.__item_type()
        self.__months[index] = new_item
        return new_item

    @db0.immutable
    def try_get_existing_month(self, month: date) -> Optional[Any]:
        """Return an existing month object, or None when absent."""
        index = self.__get_index(month)

        if index < 0:
            return None

        if index < len(self.__months):
            existing_item = self.__months[index]
            if existing_item is not None:
                return existing_item

        return None

    @db0.immutable
    def get_existing_month(self, month: date) -> Any:
        """Return an existing month object, raising if absent."""
        return self.get_month(month, create=False)

    @db0_rpc.remote
    def set_month(self, month: date, value: Any) -> None:
        """Set or clear the object at a specific month."""
        index = self.__get_index(month)

        if index < 0:
            raise ValueError(
                f"Month {month.year}-{month.month:02d} is before base year "
                f"{self.__base_year}"
            )

        while len(self.__months) <= index:
            self.__months.append(None)

        if value is not None and not isinstance(value, self.__item_type):
            raise TypeError(
                "Invalid value type for MonthStore: expected "
                f"{self.__item_type.__name__} or None, got {type(value).__name__}"
            )

        self.__months[index] = value

    def get_span(self) -> tuple[date, date] | None:
        """Return the first and last stored month dates, or None when empty."""
        if not self.__months:
            return None

        first_index = next((i for i, item in enumerate(self.__months) if item is not None), None)
        if first_index is None:
            return None

        last_index = next(i for i, item in enumerate(reversed(self.__months)) if item is not None)
        last_index = len(self.__months) - 1 - last_index

        def index_to_date(idx: int) -> date:
            year = self.__base_year + (idx // 12)
            month = (idx % 12) + 1
            return date(year, month, 1)

        start_date = index_to_date(first_index)
        end_date = index_to_date(last_index)
        return start_date, end_date

    def get_recent(self, count: int = 12) -> list[Any]:
        """Return up to count stored items in reverse chronological order."""
        recent_items = []
        for i in range(len(self.__months) - 1, -1, -1):
            if len(recent_items) >= count:
                break
            item = self.__months[i]
            if item is not None:
                recent_items.append(item)
        return recent_items

    @property
    def recent(self) -> list[Any]:
        """Return up to 12 most recent stored items."""
        return self.get_recent(12)
