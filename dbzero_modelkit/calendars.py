"""Sparse calendar model primitives backed by dbzero."""

from __future__ import annotations

from calendar import monthrange
from datetime import date as Date, timedelta
from typing import Any, Iterable, Iterator

import dbzero as db0


def get_month_index(base_year: int, date: Date) -> int:
    """Return the zero-based month index relative to base_year."""
    return (date.year * 12 + date.month - base_year * 12) - 1


def get_date_from_month_index(base_year: int, month_index: int) -> Date:
    """Return the first day of the month for a zero-based month index."""
    return Date(base_year + month_index // 12, month_index % 12 + 1, 1)


@db0.memo(id="/dbzero/dbzero-modelkit/MonthCalendar", no_default_tags=True)
class MonthCalendar:
    """Single sparse month view for Calendar."""

    def __init__(self, calendar: "Calendar", month_index: int, prefix: str | None = None) -> None:
        db0.set_prefix(self, prefix)
        self.__calendar = calendar
        self.__index = month_index
        self.__days = []
        self.__max_days = monthrange(
            calendar.base_year + month_index // 12,
            month_index % 12 + 1,
        )[1]

    def __validate_date(self, date: Date) -> None:
        month_index = get_month_index(self.__calendar.base_year, date)
        if month_index != self.__index:
            raise ValueError("Date is not in the month")
        if self.__max_days < date.day:
            raise ValueError("Date is out of range")

    def set(self, date: Date, value: Any) -> None:
        """Set a value for a date in this month."""
        self.__validate_date(date)
        if len(self.__days) <= date.day:
            self.__days.extend([None] * (date.day - len(self.__days)))
        self.__days[date.day - 1] = value

    def get(self, date: Date) -> Any | None:
        """Return the stored value for date, or None when unset."""
        self.__validate_date(date)
        if len(self.__days) >= date.day:
            return self.__days[date.day - 1]
        return None

    def range(self, from_date: Date | None, to_date: Date | None = None) -> Iterator[Any | None]:
        """Yield values from from_date through to_date within this month."""
        start_day = 0
        if from_date is not None:
            self.__validate_date(from_date)
            start_day = from_date.day - 1
        end_day = self.__max_days
        if to_date is not None:
            self.__validate_date(to_date)
            end_day = to_date.day
        if start_day > end_day:
            raise ValueError("Invalid range. 'from_date' must be before 'to_date'")
        while start_day <= end_day - 1:
            if start_day < len(self.__days):
                yield self.__days[start_day]
            else:
                yield None
            start_day += 1

    def __iter__(self):
        """Yield `(date, value)` pairs for set non-None days."""
        actual_day = get_date_from_month_index(self.__calendar.base_year, self.__index)
        for day in self.__days:
            if day is not None:
                yield actual_day, day
            actual_day += timedelta(days=1)


@db0.memo(id="/dbzero/dbzero-modelkit/Calendar", no_default_tags=True)
class Calendar:
    """Sparse date calendar with lazy month creation."""

    def __init__(self, base_year: int = 2025, prefix: str | None = None) -> None:
        db0.set_prefix(self, prefix)
        self.__months = []
        self.__base_year = base_year

    def get_month(self, date: Date, create: bool = False) -> MonthCalendar | None:
        """Retrieve or create the MonthCalendar associated with date."""
        self.__validate_date(date)
        month_index = get_month_index(self.base_year, date)
        if len(self.__months) <= month_index:
            if create:
                self.__months.extend([None] * (month_index - len(self.__months) + 1))
            else:
                return None
        if self.__months[month_index] is None and create is True:
            self.__months[month_index] = MonthCalendar(
                self,
                month_index,
                prefix=db0.get_prefix_of(self).name,
            )
        return self.__months[month_index]

    def date_range(
        self,
        from_date: Date | None = None,
        to_date: Date | None = None,
        reverse: bool = False,
    ) -> Iterable[tuple[Date, Any | None]]:
        """Yield `(date, value)` pairs for consecutive dates."""
        if from_date is None:
            from_date = Date(self.base_year, 1, 1)
        else:
            self.__validate_date(from_date)
        if to_date is not None:
            self.__validate_date(to_date)
            if from_date > to_date:
                raise ValueError("from_date should be less than to_date")

        if reverse:
            if to_date is None:
                raise ValueError("to_date is required when iterating in reverse")
            actual_date = to_date
            end_date = from_date
            delta = timedelta(days=-1)
        else:
            actual_date = from_date
            end_date = to_date
            delta = timedelta(days=1)

        while True:
            yield actual_date, self.get(actual_date)
            if actual_date == end_date:
                break
            actual_date += delta

    def range(
        self,
        from_date: Date | None = None,
        to_date: Date | None = None,
        reverse: bool = False,
    ) -> Iterable[Any | None]:
        """Yield only values from date_range."""
        return (value for _date, value in self.date_range(from_date, to_date, reverse))

    def get(self, date: Date) -> Any | None:
        """Return the stored value for date, or None when unset."""
        month = self.get_month(date)
        return month.get(date) if month is not None else None

    def set(self, date: Date, value: Any) -> None:
        """Set the value for date, creating its month when needed."""
        self.get_month(date, create=True).set(date, value)

    @property
    def base_year(self) -> int:
        """Return the base year for this calendar."""
        return self.__base_year

    def __validate_date(self, date: Date) -> None:
        if date.year < self.base_year:
            raise ValueError(
                f"Date is out of range. Date must be after year {self.base_year}. Got: {date}"
            )

    def __iter__(self):
        """Yield `(date, value)` pairs for all set non-None days."""
        for month in self.__months:
            if month is not None:
                yield from month

    def is_set(self, date: Date) -> bool:
        """Return True when the calendar value at date is truthy."""
        return bool(self.get(date))

    def find_not_set(self, dates: Iterable[Date]) -> Iterable[Date]:
        """Yield dates that do not have a truthy calendar value."""
        for date in dates:
            if not self.is_set(date):
                yield date
