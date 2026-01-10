import pytest
from datetime import date
from reusables.entry import Entry


def test_entry_equality():
    a = Entry(date=date(2024, 1, 1), hours=2.0, rate=10.0, is_event=False)
    b = Entry(date=date(2024, 1, 1), hours=2.0, rate=10.0, is_event=False)
    assert a == b


def test_events_entry_equality():
    a = Entry(date=date(2024, 1, 1), hours=0.0, rate=20.0, is_event=True)
    b = Entry(date=date(2024, 1, 1), hours=5.0, rate=20.0, is_event=True)
    assert a == b


def test_entry_inequality_different_rate():
    a = Entry(date=date(2024, 1, 1), hours=2.0, rate=10.0, is_event=False)
    b = Entry(date=date(2024, 1, 1), hours=2.0, rate=12.0, is_event=False)
    assert a != b


def test_entry_compare_with_non_entry():
    a = Entry(date=date(2024, 1, 1), hours=2.0, rate=10.0, is_event=False)
    with pytest.raises(NotImplementedError):
        _ = (a == "not-an-entry")
