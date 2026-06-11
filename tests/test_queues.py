"""Tests for dbzero-backed FIFO queue utilities."""

from __future__ import annotations

import dbzero as db0

from dbzero_modelkit.queues import FQ_Item, FiFoQueue


def test_queue_model_type_ids(db0_fixture):
    queue = FiFoQueue()
    item = FQ_Item(0)

    assert db0.get_type_stats(type(queue))["type_id"] == "/dbzero/dbzero-modelkit/FiFoQueue"
    assert db0.get_type_stats(type(item))["type_id"] == "/dbzero/dbzero-modelkit/FQ_Item"


def test_fifo_queue_accepts_keyword_only_prefix(db0_fixture):
    db0.open("queue_prefix", "rw")

    queue = FiFoQueue(prefix="queue_prefix")

    assert db0.get_prefix_of(queue).name == "queue_prefix"
    assert db0.get_prefix_of(queue._FiFoQueue__items).name == "queue_prefix"


def test_fifo_queue_items_use_queue_prefix(db0_fixture):
    db0.open("queue_prefix", "rw")
    queue = FiFoQueue(prefix="queue_prefix")

    queue.push_back(value=1)
    item = next(iter(queue._FiFoQueue__items.select()))

    assert db0.get_prefix_of(item).name == "queue_prefix"


def test_fifo_queue_can_be_created(db0_fixture):
    queue = FiFoQueue()
    assert queue is not None
    assert queue.is_empty() is True


def test_push_back_adds_element(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(first=123, second="my item")
    result = queue.pop_front(1)
    assert len(result) == 1
    assert queue.is_empty() is True


def test_pop_front_returns_correct_kwargs(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(first=123, second="my item")

    assert queue.pop_front(10) == [{"first": 123, "second": "my item"}]


def test_pop_front_respects_count(db0_fixture):
    queue = FiFoQueue()
    for i in range(5):
        queue.push_back(value=i)

    result = queue.pop_front(3)

    assert len(result) == 3


def test_pop_front_returns_fifo_order(db0_fixture):
    queue = FiFoQueue()
    for i in range(5):
        queue.push_back(value=i)

    result = queue.pop_front(5)

    assert [item["value"] for item in result] == [0, 1, 2, 3, 4]


def test_pop_front_removes_elements(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(value=1)
    queue.push_back(value=2)

    assert queue.pop_front(1) == [{"value": 1}]
    assert queue.pop_front(1) == [{"value": 2}]


def test_pop_front_on_empty_queue_returns_empty_list(db0_fixture):
    queue = FiFoQueue()

    assert not queue.pop_front(10)


def test_pop_front_with_count_exceeding_queue_size(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(value=1)

    assert len(queue.pop_front(100)) == 1


def test_pop_front_returns_memo_object_value(db0_fixture):
    @db0.memo
    class SampleMemoObj:
        def __init__(self, val):
            self.val = val

    obj = SampleMemoObj(99)
    queue = FiFoQueue()
    queue.push_back(item=obj)
    result = queue.pop_front(1)

    assert len(result) == 1
    assert result[0]["item"].val == 99


def test_multiple_pushes_after_pops(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(value=1)
    queue.push_back(value=2)
    queue.pop_front(2)
    queue.push_back(value=3)
    queue.push_back(value=4)

    result = queue.pop_front(10)

    assert [item["value"] for item in result] == [3, 4]


def test_pop_front_leaves_remaining_elements(db0_fixture):
    queue = FiFoQueue()
    for i in range(5):
        queue.push_back(value=i)
    queue.pop_front(2)

    result = queue.pop_front(10)

    assert [item["value"] for item in result] == [2, 3, 4]


def test_pop_front_filter_selects_matching_items(db0_fixture):
    queue = FiFoQueue()
    for i in range(5):
        queue.push_back(value=i)

    result = queue.pop_front(10, filter=lambda value: value % 2 == 0)

    assert [item["value"] for item in result] == [0, 2, 4]


def test_pop_front_filter_non_matching_items_stay_in_queue(db0_fixture):
    queue = FiFoQueue()
    for i in range(4):
        queue.push_back(value=i)

    queue.pop_front(10, filter=lambda value: value % 2 == 0)
    result = queue.pop_front(10)

    assert [item["value"] for item in result] == [1, 3]


def test_pop_front_filter_respects_count(db0_fixture):
    queue = FiFoQueue()
    for i in range(6):
        queue.push_back(value=i)

    result = queue.pop_front(2, filter=lambda value: value % 2 == 0)

    assert [item["value"] for item in result] == [0, 2]


def test_pop_front_filter_count_limited_items_stay_in_queue(db0_fixture):
    queue = FiFoQueue()
    for i in range(6):
        queue.push_back(value=i)

    queue.pop_front(2, filter=lambda value: value % 2 == 0)
    result = queue.pop_front(10)

    assert [item["value"] for item in result] == [1, 3, 4, 5]


def test_pop_front_filter_none_behaves_like_no_filter(db0_fixture):
    queue = FiFoQueue()
    for i in range(3):
        queue.push_back(value=i)

    result = queue.pop_front(10, filter=None)

    assert [item["value"] for item in result] == [0, 1, 2]


def test_pop_front_filter_all_rejected_returns_empty_and_queue_unchanged(db0_fixture):
    queue = FiFoQueue()
    for i in range(3):
        queue.push_back(value=i)

    assert not queue.pop_front(10, filter=lambda value: False)
    result = queue.pop_front(10)
    assert [item["value"] for item in result] == [0, 1, 2]


def test_pop_front_filter_receives_all_kwargs(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(a=1, b=2)
    queue.push_back(a=10, b=20)

    result = queue.pop_front(10, filter=lambda a, b: a + b > 10)

    assert result == [{"a": 10, "b": 20}]


def test_has_item_returns_true_when_match_exists(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(job_uuid="a", message="first")
    queue.push_back(job_uuid="b", message="second")

    assert queue.has_item(lambda **kwargs: kwargs.get("job_uuid") == "b") is True


def test_has_item_returns_false_when_no_match_exists(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(job_uuid="a", message="first")

    assert queue.has_item(lambda **kwargs: kwargs.get("job_uuid") == "b") is False


def test_has_item_returns_none_when_scan_budget_exhausted(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(job_uuid="a", message="first")
    queue.push_back(job_uuid="b", message="second")

    assert queue.has_item(lambda **kwargs: kwargs.get("job_uuid") == "b", max_scan=0) is None


def test_has_item_does_not_remove_items(db0_fixture):
    queue = FiFoQueue()
    queue.push_back(job_uuid="a", message="first")
    queue.push_back(job_uuid="b", message="second")

    assert queue.has_item(lambda **kwargs: kwargs.get("job_uuid") == "a") is True
    assert queue.pop_front(10) == [
        {"job_uuid": "a", "message": "first"},
        {"job_uuid": "b", "message": "second"},
    ]
