"""Tests for sparse calendar model primitives."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

import dbzero as db0
import pytest

from dbzero_modelkit.calendars import Calendar, MonthCalendar, get_month_index


class MockDate:
    """Date-like object used to test invalid day validation."""

    def __init__(self, year: int, month: int, day: int) -> None:
        self.year = year
        self.month = month
        self.day = day


def test_get_month_index():
    assert get_month_index(2025, date(2025, 1, 1)) == 0
    assert get_month_index(2025, date(2025, 1, 5)) == 0
    assert get_month_index(2025, date(2025, 5, 1)) == 4
    assert get_month_index(2025, date(2026, 1, 1)) == 12
    assert get_month_index(2025, date(2026, 5, 1)) == 16


def test_calendar_can_create_month(db0_fixture):
    calendar = Calendar()
    assert calendar.get_month(date(2025, 1, 1)) is None
    assert calendar.get_month(date(2025, 1, 1), create=True) is not None
    assert calendar.get_month(date(2025, 12, 1), create=True) is not None
    assert calendar.get_month(date(2025, 12, 1)) is not None
    month = calendar.get_month(date(2026, 12, 1), create=True)
    assert month is not None
    assert month._MonthCalendar__index == 23


def test_calendar_raises_for_invalid_date(db0_fixture):
    calendar = Calendar()
    with pytest.raises(ValueError, match="Date is out of range"):
        calendar.get_month(date(2024, 1, 1))
    with pytest.raises(ValueError, match="Date is out of range"):
        next(iter(calendar.range(from_date=date(2024, 1, 1))))
    with pytest.raises(ValueError, match="Date is out of range"):
        next(iter(calendar.range(to_date=date(2024, 1, 1))))


def test_calendar_can_return_range(db0_fixture):
    calendar = Calendar()
    for i in range(1, 8):
        calendar.set(date(2025, 1, i), i - 1)

    range_1 = calendar.range(from_date=date(2025, 1, 3), to_date=date(2025, 1, 6))
    assert list(range_1) == [2, 3, 4, 5]

    range_2 = calendar.range(from_date=date(2025, 1, 3), to_date=None)
    expected_indexes = [2, 3, 4, 5, 6] + [None for _ in range(30)]
    assert [value for _, value in zip(expected_indexes, range_2)] == expected_indexes

    range_3 = calendar.range(from_date=None, to_date=date(2025, 2, 4))
    assert len(list(range_3)) == 35


def test_calendar_can_set_and_get(db0_fixture):
    calendar = Calendar()
    assert calendar.get(date(2025, 3, 5)) is None

    calendar.set(date(2025, 1, 1), 100)
    calendar.set(date(2025, 1, 2), 200)
    calendar.set(date(2025, 1, 1), 300)
    calendar.set(date(2025, 3, 5), 400)

    assert calendar.get(date(2025, 1, 1)) == 300
    assert calendar.get(date(2025, 1, 2)) == 200
    assert calendar.get(date(2025, 3, 5)) == 400
    assert calendar.get(date(2025, 3, 15)) is None
    assert len(calendar._Calendar__months) == 3


def test_calendar_can_work_with_leap_year(db0_fixture):
    calendar = Calendar()
    for year in [2025, 2028]:
        for month in range(1, 13):
            max_day = monthrange(year, month)[1]
            calendar.set(date(year, month, max_day), 500)
            assert calendar.get(date(year, month, max_day)) == 500
            with pytest.raises(ValueError, match="Date is out of range"):
                calendar.set(MockDate(year, month, max_day + 1), 500)
    assert calendar.get(date(2028, 2, 29)) == 500


def test_month_calendar_can_only_get_from_date_in_month(db0_fixture):
    calendar = Calendar()
    month = calendar.get_month(date(2025, 1, 1), create=True)
    with pytest.raises(ValueError, match="Date is not in the month"):
        month.get(date(2025, 2, 1))


def test_month_calendar_can_return_range(db0_fixture):
    calendar = Calendar()
    month_calendar = calendar.get_month(date(2025, 1, 1), create=True)
    for i in range(1, 8):
        month_calendar.set(date(2025, 1, i), i - 1)

    assert list(month_calendar.range(from_date=date(2025, 1, 3), to_date=date(2025, 1, 6))) == [
        2,
        3,
        4,
        5,
    ]

    range_2 = month_calendar.range(from_date=date(2025, 1, 3), to_date=None)
    assert list(range_2) == [2, 3, 4, 5, 6] + [None for _ in range(24)]

    assert list(month_calendar.range(from_date=None, to_date=date(2025, 1, 4))) == [
        0,
        1,
        2,
        3,
    ]
    assert list(month_calendar.range(from_date=None, to_date=None)) == [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
    ] + [None for _ in range(24)]


def test_iterate_over_month_calendar(db0_fixture):
    calendar = MonthCalendar(Calendar(), 0)
    calendar.set(date(2025, 1, 1), 100)
    calendar.set(date(2025, 1, 5), 200)
    calendar.set(date(2025, 1, 11), 300)
    calendar.set(date(2025, 1, 31), 400)

    assert list(calendar) == [
        (date(2025, 1, 1), 100),
        (date(2025, 1, 5), 200),
        (date(2025, 1, 11), 300),
        (date(2025, 1, 31), 400),
    ]


def test_iter_over_calendar(db0_fixture):
    calendar = Calendar()
    calendar.set(date(2025, 1, 1), 100)
    calendar.set(date(2025, 1, 5), 200)
    calendar.set(date(2025, 2, 11), 300)
    calendar.set(date(2025, 4, 22), 400)

    assert list(calendar) == [
        (date(2025, 1, 1), 100),
        (date(2025, 1, 5), 200),
        (date(2025, 2, 11), 300),
        (date(2025, 4, 22), 400),
    ]


def test_calendar_iter_reverse(db0_fixture):
    calendar = Calendar()
    expected = []
    for i in range(1, 11):
        calendar.set(date(2025, 1, i), i)
        expected.append((date(2025, 1, i), i))
    expected.extend((date(2025, 1, i), None) for i in range(11, 21))

    result = calendar.date_range(date(2025, 1, 1), date(2025, 1, 20), True)
    assert list(result) == list(reversed(expected))


def test_calendar_reverse_requires_to_date(db0_fixture):
    calendar = Calendar()
    with pytest.raises(ValueError, match="to_date is required"):
        next(iter(calendar.date_range(date(2025, 1, 1), reverse=True)))


def test_calendar_is_set(db0_fixture):
    calendar = Calendar()
    for i in range(1, 11):
        calendar.set(date(2025, 1, i), i)

    assert calendar.is_set(date(2025, 1, 1)) is True
    assert calendar.is_set(date(2025, 1, 10)) is True

    calendar.set(date(2025, 1, 11), None)
    assert calendar.is_set(date(2025, 1, 11)) is False
    assert calendar.is_set(date(2025, 2, 24)) is False


def test_calendar_find_not_set(db0_fixture):
    calendar = Calendar()
    for i in range(1, 11):
        calendar.set(date(2025, 1, i), i)

    assert not list(calendar.find_not_set([date(2025, 1, i) for i in range(1, 11)]))
    assert list(calendar.find_not_set([date(2025, 2, 1), date(2025, 2, 2)])) == [
        date(2025, 2, 1),
        date(2025, 2, 2),
    ]
    assert list(calendar.find_not_set([date(2025, 1, 1), date(2025, 2, 1)])) == [date(2025, 2, 1)]


def test_get_month_beyond_existing_calendar(tmp_path):
    db0_path = tmp_path / "db0"
    db0.init(str(db0_path), read_write=True)
    db0.open("test_prefix", "rw")
    calendar = Calendar()
    obj_uuid = db0.uuid(calendar)
    db0.close()

    db0.init(str(db0_path))
    db0.open("test_prefix", "r")
    persisted_calendar = db0.fetch(obj_uuid)
    assert persisted_calendar.get_month(date(2025, 11, 1)) is None
    db0.close()
