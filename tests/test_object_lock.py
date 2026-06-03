"""Tests for ObjectLock."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import dbzero as db0

from dbzero_modelkit.object_lock import ObjectLock


class DatetimeMock:
    """Deterministic datetime replacement for object lock tests."""

    @staticmethod
    def now(_tz=None):
        return datetime(2025, 12, 12)


@patch("dbzero_modelkit.object_lock.datetime", DatetimeMock)
def test_object_lock(db0_fixture):
    @db0.memo
    class TestObj1:
        pass

    @db0.memo
    class TestObj2:
        pass

    a = TestObj1()
    b = TestObj1()
    c = TestObj2()

    lock = ObjectLock([a, b, c], 60)

    assert lock.expires_at == DatetimeMock.now() + timedelta(seconds=60)
    assert db0.find(a, "LOCKED")
    assert db0.find(b, "LOCKED")
    assert db0.find(c, "LOCKED")
    assert list(lock.select(TestObj1)) == [a, b]
    assert list(lock.select(TestObj2)) == [c]

    lock.unlock()
    assert not db0.find(a, "LOCKED")
    assert not db0.find(b, "LOCKED")
    assert not db0.find(c, "LOCKED")


@patch("dbzero_modelkit.object_lock.datetime", DatetimeMock)
def test_object_lock_accepts_single_object(db0_fixture):
    @db0.memo
    class TestObj:
        pass

    item = TestObj()
    lock = ObjectLock(item, 60)

    assert lock.locked_objects == [item]
    assert db0.find(item, "LOCKED")


@patch("dbzero_modelkit.object_lock.datetime", DatetimeMock)
def test_object_lock_unlock_with_error_marks_all_locked_objects(db0_fixture):
    @db0.memo
    class TestObj:
        pass

    a = TestObj()
    b = TestObj()
    c = TestObj()
    db0.tags(a, b, c).add("FOR_DELIVERY")

    lock = ObjectLock([a, b, c], 60)
    lock.unlock_with_error()

    assert not db0.find(a, "LOCKED")
    assert not db0.find(b, "LOCKED")
    assert not db0.find(c, "LOCKED")
    assert db0.find(a, "ERROR")
    assert db0.find(b, "ERROR")
    assert db0.find(c, "ERROR")
    assert db0.find(a, "FOR_DELIVERY")
    assert db0.find(b, "FOR_DELIVERY")
    assert db0.find(c, "FOR_DELIVERY")


@patch("dbzero_modelkit.object_lock.datetime", DatetimeMock)
def test_object_lock_unlock_with_error_marks_only_selected_object(db0_fixture):
    @db0.memo
    class TestObj:
        pass

    a = TestObj()
    b = TestObj()
    c = TestObj()
    db0.tags(a, b, c).add("FOR_DELIVERY")

    lock = ObjectLock([a, b, c], 60)
    lock.unlock_with_error(a)

    assert not db0.find(a, "LOCKED")
    assert not db0.find(b, "LOCKED")
    assert not db0.find(c, "LOCKED")
    assert db0.find(a, "ERROR")
    assert not db0.find(b, "ERROR")
    assert not db0.find(c, "ERROR")
    assert db0.find(a, "FOR_DELIVERY")
    assert db0.find(b, "FOR_DELIVERY")
    assert db0.find(c, "FOR_DELIVERY")


@patch("dbzero_modelkit.object_lock.datetime", DatetimeMock)
def test_object_lock_unlock_with_error_marks_list_of_selected_objects(db0_fixture):
    @db0.memo
    class TestObj:
        pass

    a = TestObj()
    b = TestObj()
    c = TestObj()
    db0.tags(a, b, c).add("FOR_DELIVERY")

    lock = ObjectLock([a, b, c], 60)
    lock.unlock_with_error([a, b])

    assert not db0.find(a, "LOCKED")
    assert not db0.find(b, "LOCKED")
    assert not db0.find(c, "LOCKED")
    assert db0.find(a, "ERROR")
    assert db0.find(b, "ERROR")
    assert not db0.find(c, "ERROR")
