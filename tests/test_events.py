from constants import RATE_LEVELS, EVENTS
from reusables.events import is_event


def test_events():
    for event in EVENTS:
        assert is_event(event)


def test_non_events():
    for level in RATE_LEVELS:
        if level not in EVENTS:
            assert not is_event(level)
