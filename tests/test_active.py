"""Tests for active-window model primitives."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import patch

import dbzero as db0

from dbzero_modelkit.active import ActiveBase, ActiveIndex


def test_active_model_type_ids(db0_fixture):
    active_base = ActiveBase()
    active_index = ActiveIndex()

    assert (
        db0.get_type_stats(type(active_base))["type_id"]
        == "/dbzero/dbzero-modelkit/ActiveBase"
    )
    assert (
        db0.get_type_stats(type(active_index))["type_id"]
        == "/dbzero/dbzero-modelkit/ActiveIndex"
    )


def test_active_models_accept_keyword_only_prefix(db0_fixture):
    db0.open("alternate_prefix", "rw")

    active_base = ActiveBase(prefix="alternate_prefix")
    active_index = ActiveIndex(prefix="alternate_prefix")

    assert db0.get_prefix_of(active_base).name == "alternate_prefix"
    assert db0.get_prefix_of(active_index).name == "alternate_prefix"
    assert db0.get_prefix_of(active_index.active_from_index).name == "alternate_prefix"
    assert db0.get_prefix_of(active_index.expires_on_index).name == "alternate_prefix"


def test_active_base_subclass_without_prefix_remains_compatible(db0_fixture):
    @db0.memo(no_default_tags=True)
    class TimedThing(ActiveBase):
        def __init__(self, name: str) -> None:
            super().__init__()
            self.name = name

    thing = TimedThing("night shift")

    assert thing.name == "night shift"
    assert thing.active is True


class DatetimeMock:
    """Deterministic datetime replacement for active-window tests."""

    min = datetime.min
    max = datetime.max

    @staticmethod
    def now(_tz=None):
        return datetime(2025, 12, 12)

    @staticmethod
    def combine(date_value, time_value):
        return datetime.combine(date_value, time_value)


@patch("dbzero_modelkit.active.datetime", DatetimeMock)
def test_active_base_is_active(db0_fixture):
    now = DatetimeMock.now()
    active_base_1 = ActiveBase()
    assert active_base_1.active_from is None
    assert active_base_1.expires_on is None
    assert active_base_1.is_active() is True
    assert active_base_1.is_active(now - timedelta(days=1)) is True

    active_base_2 = ActiveBase(active_from=datetime(2025, 1, 1))
    assert active_base_2.is_active() is True
    assert active_base_2.is_active(now) is True
    assert active_base_2.is_active(datetime(2024, 12, 12)) is False

    active_base_3 = ActiveBase(expires_on=now + timedelta(days=14))
    assert active_base_3.is_active() is True
    assert active_base_3.is_active(datetime(2026, 12, 12)) is False

    active_base_4 = ActiveBase(
        active_from=datetime(2024, 6, 30),
        expires_on=datetime(2026, 6, 30),
    )
    assert active_base_4.is_active() is True
    assert active_base_4.is_active(datetime(2024, 12, 12)) is True
    assert active_base_4.is_active(datetime(2024, 1, 12)) is False
    assert active_base_4.is_active(datetime(2026, 12, 12)) is False


def test_active_base_accepts_date_bounds(db0_fixture):
    active_base = ActiveBase(active_from=date(2025, 1, 1), expires_on=date(2025, 1, 1))

    assert active_base.is_active(datetime(2025, 1, 1, 0, 0)) is True
    assert active_base.is_active(datetime(2025, 1, 1, 23, 59)) is True
    assert active_base.is_active(datetime(2025, 1, 2, 0, 0)) is False


def test_active_base_active_property(db0_fixture):
    now = datetime.now()
    assert ActiveBase().active is True
    assert ActiveBase(active_from=datetime(2025, 1, 1)).active is True
    assert ActiveBase(expires_on=now + timedelta(days=14)).active is True
    assert ActiveBase(expires_on=datetime.now() - timedelta(days=10)).active is False


def test_active_base_does_not_expose_normalization_helpers(db0_fixture):
    assert not hasattr(ActiveBase, "normalize_start")
    assert not hasattr(ActiveBase, "normalize_end")


def test_active_index_adds_objects(db0_fixture):
    active_base_1 = ActiveBase()
    active_index = ActiveIndex()
    active_index.add(active_base_1)
    assert active_base_1.active_from is None
    assert active_base_1.expires_on is None

    active_base_2 = ActiveBase(active_from=datetime(2024, 1, 1))
    active_index.add(active_base_2)
    assert active_base_2.active_from == datetime(2024, 1, 1)
    assert active_base_2.expires_on is None

    active_base_3 = ActiveBase(
        active_from=datetime(2025, 12, 1),
        expires_on=datetime(2026, 6, 30),
    )
    active_index.add(active_base_3)
    assert active_base_3.active_from == datetime(2025, 12, 1)
    assert active_base_3.expires_on == datetime(2026, 6, 30)


@patch("dbzero_modelkit.active.datetime", DatetimeMock)
def test_active_index_find_sorts_by_selected_index(db0_fixture):
    active_index = ActiveIndex()
    active_base_1 = ActiveBase()
    active_base_2 = ActiveBase(active_from=datetime(2024, 1, 1))
    active_base_3 = ActiveBase(
        active_from=datetime(2026, 12, 15),
        expires_on=datetime(2028, 6, 30),
    )
    active_base_4 = ActiveBase(
        active_from=datetime(2025, 12, 15),
        expires_on=datetime(2027, 6, 30),
    )
    active_base_5 = ActiveBase(
        active_from=datetime(2024, 12, 15),
        expires_on=datetime(2026, 6, 30),
    )

    for active_base in [active_base_1, active_base_2, active_base_3, active_base_4, active_base_5]:
        active_index.add(active_base)

    active_from_asc = list(active_index.find(active_from=False))
    assert set(active_from_asc) == {
        active_base_2,
        active_base_5,
        active_base_4,
        active_base_3,
        active_base_1,
    }

    active_from_desc = list(active_index.find(active_from=True))
    assert set(active_from_desc) == {
        active_base_1,
        active_base_3,
        active_base_4,
        active_base_5,
        active_base_2,
    }

    expires_on_desc = list(active_index.find())
    assert set(expires_on_desc) == {
        active_base_2,
        active_base_1,
        active_base_3,
        active_base_4,
        active_base_5,
    }

    expires_on_asc = list(active_index.find(expires_on=False))
    assert set(expires_on_asc) == {
        active_base_5,
        active_base_4,
        active_base_3,
        active_base_2,
        active_base_1,
    }


@patch("dbzero_modelkit.active.datetime", DatetimeMock)
def test_active_index_find_active(db0_fixture):
    now = DatetimeMock.now()
    active_index = ActiveIndex()
    active_base_1 = ActiveBase()

    assert not list(active_index.find_active())

    active_index.add(active_base_1)
    assert list(active_index.find_active()) == [active_base_1]

    active_base_2 = ActiveBase(active_from=now - timedelta(days=365))
    active_base_3 = ActiveBase(
        active_from=now + timedelta(days=365),
        expires_on=now + timedelta(days=900),
    )
    active_base_4 = ActiveBase(
        active_from=now + timedelta(days=3),
        expires_on=now + timedelta(days=600),
    )
    active_base_5 = ActiveBase(
        active_from=now - timedelta(days=365),
        expires_on=now + timedelta(days=600),
    )
    active_base_6 = ActiveBase(
        active_from=now - timedelta(days=365),
        expires_on=now - timedelta(days=100),
    )
    active_base_7 = ActiveBase(expires_on=now - timedelta(days=175))

    for active_base in [
        active_base_2,
        active_base_3,
        active_base_4,
        active_base_5,
        active_base_6,
        active_base_7,
    ]:
        active_index.add(active_base)

    assert list(active_index.find_active(as_of=now + timedelta(days=900), active_from=True)) == [
        active_base_1,
        active_base_3,
        active_base_2,
    ]
    assert list(active_index.find_active(active_from=True)) == [
        active_base_1,
        active_base_5,
        active_base_2,
    ]
    assert list(active_index.find_active(active_from=False)) == [
        active_base_2,
        active_base_5,
        active_base_1,
    ]
    assert set(active_index.find_active()) == {active_base_2, active_base_1, active_base_5}

    active_base_8 = ActiveBase(expires_on=now + timedelta(days=1))
    active_index.add(active_base_8)
    assert set(active_index.find_active()) == {
        active_base_2,
        active_base_1,
        active_base_5,
        active_base_8,
    }


@patch("dbzero_modelkit.active.datetime", DatetimeMock)
def test_active_index_update(db0_fixture):
    now = DatetimeMock.now()
    active_base = ActiveBase(expires_on=now)
    active_index = ActiveIndex()
    active_index.add(active_base)

    active_index.update(active_base, expires_on=active_base.expires_on + timedelta(days=3))
    assert active_base.active_from is None
    assert active_base.expires_on == now + timedelta(days=3)

    active_index.update(
        active_base,
        active_from=now - timedelta(days=7),
        expires_on=now + timedelta(days=7),
    )
    assert active_base.active_from == now - timedelta(days=7)
    assert active_base.expires_on == now + timedelta(days=7)

    active_index.update(active_base, active_from=None, expires_on=None)
    assert active_base.active_from is None
    assert active_base.expires_on is None


def test_overlaps_detects_intersection(db0_fixture):
    first = ActiveBase(
        active_from=datetime(2025, 1, 1, 8, 0),
        expires_on=datetime(2025, 1, 10, 16, 0),
    )
    second = ActiveBase(
        active_from=datetime(2025, 1, 5, 8, 0),
        expires_on=datetime(2025, 1, 15, 16, 0),
    )

    assert first.overlaps(second)


def test_can_merge_true_for_touching_boundary(db0_fixture):
    first = ActiveBase(
        active_from=datetime(2025, 1, 1, 8, 0),
        expires_on=datetime(2025, 1, 31, 22, 0),
    )
    second = ActiveBase(
        active_from=datetime(2025, 1, 31, 22, 0),
        expires_on=datetime(2025, 2, 5, 8, 0),
    )

    assert first.can_merge(second)


def test_is_adjacent_false_for_positive_gap_with_default(db0_fixture):
    first = ActiveBase(
        active_from=datetime(2025, 1, 31, 8, 0),
        expires_on=datetime(2025, 1, 31, 22, 0),
    )
    second = ActiveBase(
        active_from=datetime(2025, 2, 1, 0, 0),
        expires_on=datetime(2025, 2, 1, 12, 0),
    )

    assert not first.is_adjacent(second)


def test_is_adjacent_true_when_gap_within_max_gap(db0_fixture):
    first = ActiveBase(
        active_from=datetime(2025, 1, 31, 8, 0),
        expires_on=datetime(2025, 1, 31, 22, 0),
    )
    second = ActiveBase(
        active_from=datetime(2025, 2, 1, 0, 0),
        expires_on=datetime(2025, 2, 1, 12, 0),
    )

    assert first.is_adjacent(second, max_gap=timedelta(hours=2))


def test_merge_returns_combined_bounds_for_adjacent_periods(db0_fixture):
    first = ActiveBase(
        active_from=datetime(2025, 4, 1, 0, 0),
        expires_on=datetime(2025, 4, 30, 0, 0),
    )
    second = ActiveBase(
        active_from=datetime(2025, 4, 30, 0, 0),
        expires_on=datetime(2025, 5, 15, 0, 0),
    )

    assert first.merge(second) == (
        datetime(2025, 4, 1, 0, 0),
        datetime(2025, 5, 15, 0, 0),
    )


def test_merge_supports_infinite_end(db0_fixture):
    finite = ActiveBase(
        active_from=datetime(2025, 1, 1, 0, 0),
        expires_on=datetime(2025, 1, 31, 23, 0),
    )
    infinite = ActiveBase(active_from=datetime(2025, 1, 15, 0, 0), expires_on=None)

    assert finite.merge(infinite) == (datetime(2025, 1, 1, 0, 0), None)


def test_merge_returns_none_for_non_mergeable_periods(db0_fixture):
    first = ActiveBase(
        active_from=datetime(2025, 1, 1, 0, 0),
        expires_on=datetime(2025, 1, 10, 0, 0),
    )
    second = ActiveBase(
        active_from=datetime(2025, 1, 10, 0, 1),
        expires_on=datetime(2025, 1, 20, 0, 0),
    )

    assert first.merge(second) is None
