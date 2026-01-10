import pytest
from reusables.parsing import get_event_name, parse_name, parse_swimmer, is_time, extract_keyword, REGEX_EVENT_NAME


def test_get_event_name():
    src = "Event  21   Girls 8 & Under 25 SC Meter Breaststroke"
    assert get_event_name(src) == "25m Breast"


def test_get_event_name_invalid():
    with pytest.raises(ValueError):
        get_event_name("Event X something invalid")


def test_parse_name():
    assert parse_name("Doe, Jane") == ("jane", "doe")
    assert parse_name("O'Neil, Sam") == ("sam", "o'neil")


def test_parse_name_invalid():
    with pytest.raises(ValueError):
        parse_name("NoComma Name")


def test_is_time():
    assert is_time("1:23.45")
    assert is_time("59.99")
    assert is_time("9:09")
    assert is_time("12:34.56")


def test_is_time_invalid():
    assert not is_time("abc")
    assert not is_time("123")
    assert not is_time("1:2")
    assert not is_time("1.2.3")


def test_extract_keyword():
    assert extract_keyword("NS") == "NS"
    assert extract_keyword("DQ (turn early)") == "DQ"
    assert extract_keyword("NT") == "NT"
    assert extract_keyword("some") is None


def test_parse_swimmer_with_seed_time():
    line = "Acton 107 LastNames, FirstName M 56.30  52.10"
    name, seed, time = parse_swimmer(line)
    assert name == "LastNames, FirstName M"
    assert time == "56.30"
    assert seed == "52.10"

def test_parse_swimmer_without_seed_time():
    line = "Acton 107 Last, First 59.99 q"
    name, seed, time = parse_swimmer(line)
    assert name == "Last, First"
    assert time == "59.99"
    assert seed is None


def test_parse_swimmer_invalid_club_name():
    with pytest.raises(ValueError):
        parse_swimmer("OtherClub 100 Doe, John 55.00  55.50")


def test_parse_swimmer_invalid():
    with pytest.raises(ValueError):
        parse_swimmer("Acton 107 Last, First foo bar")
