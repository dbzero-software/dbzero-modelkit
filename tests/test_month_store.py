"""Tests for MonthStore."""

from __future__ import annotations

from datetime import date

import dbzero as db0
import pytest

from dbzero_modelkit.month_store import MonthStore


def test_month_store_can_be_created(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem)
    assert month_store is not None


def test_month_store_with_custom_base_year(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2020)
    assert month_store is not None


def test_month_store_get_index_basic_cases(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)

    assert month_store._MonthStore__get_index(date(2025, 1, 15)) == 0
    assert month_store._MonthStore__get_index(date(2025, 2, 10)) == 1
    assert month_store._MonthStore__get_index(date(2025, 12, 31)) == 11
    assert month_store._MonthStore__get_index(date(2026, 1, 1)) == 12
    assert month_store._MonthStore__get_index(date(2028, 12, 31)) == 47


def test_month_store_get_month_without_create_raises_exception(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)

    with pytest.raises(ValueError, match="No item found for month 2025-01"):
        month_store.get_month(date(2025, 1, 15), create=False)


def test_month_store_get_month_with_create_returns_new_item(db0_fixture):
    @db0.memo
    class TestItem:
        def __init__(self):
            self.created = True

    month_store = MonthStore(TestItem, base_year=2025)

    item = month_store.get_month(date(2025, 3, 15), create=True)

    assert isinstance(item, TestItem)
    assert item.created is True


def test_month_store_get_month_returns_same_item_for_same_month(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)
    item1 = month_store.get_month(date(2025, 5, 1), create=True)
    item2 = month_store.get_month(date(2025, 5, 31), create=False)

    assert item1 is item2


def test_month_store_get_month_different_months_different_items(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)

    item_jan = month_store.get_month(date(2025, 1, 15), create=True)
    item_feb = month_store.get_month(date(2025, 2, 15), create=True)
    item_mar = month_store.get_month(date(2025, 3, 15), create=True)

    assert item_jan is not item_feb
    assert item_feb is not item_mar
    assert item_jan is not item_mar


def test_month_store_get_month_handles_list_expansion(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)
    far_future_item = month_store.get_month(date(2027, 12, 15), create=True)
    earlier_item = month_store.get_month(date(2025, 1, 15), create=True)

    assert far_future_item is not earlier_item


def test_month_store_get_existing_month_success(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)
    original_item = month_store.get_month(date(2025, 4, 15), create=True)

    assert month_store.get_existing_month(date(2025, 4, 15)) is original_item


def test_month_store_get_existing_month_raises_exception(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)

    with pytest.raises(ValueError):
        month_store.get_existing_month(date(2025, 7, 15))


def test_month_store_negative_index_raises_exception(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)
    date_before_base = date(2024, 12, 15)

    with pytest.raises(ValueError, match="Month 2024-12 is before base year 2025"):
        month_store.get_month(date_before_base, create=False)
    with pytest.raises(ValueError, match="Month 2024-12 is before base year 2025"):
        month_store.get_month(date_before_base, create=True)
    with pytest.raises(ValueError, match="Month 2024-12 is before base year 2025"):
        month_store.get_existing_month(date_before_base)
    assert month_store.try_get_existing_month(date_before_base) is None


def test_month_store_set_month_functionality(db0_fixture):
    @db0.memo
    class TestItem:
        def __init__(self, value=None):
            self.value = value

    @db0.memo
    class WrongItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)
    test_date = date(2025, 6, 15)

    item1 = TestItem(value="first")
    month_store.set_month(test_date, item1)
    assert month_store.get_existing_month(test_date) is item1

    item2 = TestItem(value="second")
    month_store.set_month(test_date, item2)
    assert month_store.get_existing_month(test_date) is item2

    item_future = TestItem(value="future")
    future_date = date(2027, 12, 15)
    month_store.set_month(future_date, item_future)
    assert month_store.get_existing_month(future_date) is item_future

    with pytest.raises(ValueError, match="Month 2024-12 is before base year 2025"):
        month_store.set_month(date(2024, 12, 15), TestItem())

    with pytest.raises(TypeError, match="expected .*TestItem or None"):
        month_store.set_month(test_date, WrongItem())

    month_store.set_month(test_date, None)
    assert month_store.try_get_existing_month(test_date) is None


def test_month_store_get_span_and_string(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)
    assert month_store.get_span() is None
    assert str(month_store) == ""

    month_store.get_month(date(2025, 3, 1), create=True)
    month_store.get_month(date(2026, 7, 1), create=True)

    assert month_store.get_span() == (date(2025, 3, 1), date(2026, 7, 1))
    assert str(month_store) == "2025-03 - 2026-07"


def test_month_store_get_recent_empty(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)

    assert month_store.get_recent() == []
    assert month_store.get_recent(5) == []


def test_month_store_get_recent_multiple_items(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)
    item_jan = month_store.get_month(date(2025, 1, 1), create=True)
    item_jun = month_store.get_month(date(2025, 6, 1), create=True)
    item_mar = month_store.get_month(date(2025, 3, 1), create=True)
    item_dec = month_store.get_month(date(2025, 12, 1), create=True)

    assert month_store.get_recent() == [item_dec, item_jun, item_mar, item_jan]
    assert month_store.get_recent(2) == [item_dec, item_jun]


def test_month_store_recent_property_returns_12_items(db0_fixture):
    @db0.memo
    class TestItem:
        pass

    month_store = MonthStore(TestItem, base_year=2025)
    items = []
    for month in range(1, 16):
        year = 2025 if month <= 12 else 2026
        month_in_year = month if month <= 12 else month - 12
        items.append(month_store.get_month(date(year, month_in_year, 1), create=True))

    expected_items = items[-12:]
    expected_items.reverse()
    assert month_store.recent == expected_items


def test_month_store_get_recent_uses_set_month(db0_fixture):
    @db0.memo
    class TestItem:
        def __init__(self, value=None):
            self.value = value or "default"

    month_store = MonthStore(TestItem, base_year=2025)
    item1 = TestItem("item1")
    item2 = TestItem("item2")
    item3 = TestItem("item3")

    month_store.set_month(date(2025, 2, 1), item1)
    month_store.set_month(date(2025, 5, 1), item2)
    month_store.set_month(date(2025, 8, 1), item3)

    assert month_store.get_recent() == [item3, item2, item1]
