import pandas as pd
import pytest
from reusables.matching import get_close_matches, match_swimmer


def mock_df():
    return pd.DataFrame([
        {"First name": "jane", "Surname": "doe", "25m Free": "20.10"},
        {"First name": "john", "Surname": "smith", "25m Free": "19.50"},
        {"First name": "ann", "Surname": "o'neil", "25m Free": "22.00"},
    ])


def mock_progress_callback(*args, **kwargs):
    pass


def test_get_close_matches():
    df = mock_df()
    automatic = {}
    manual = {}
    scores = get_close_matches(df, "jane", "doe", automatic, manual)
    assert scores[0] == ("jane", "doe", 100)


def test_match_swimmer_automatic():
    df = mock_df()
    automatic = {}
    manual = {}
    swimmer = match_swimmer(
        "jane", "doe", df, automatic, manual,
        progress_callback=mock_progress_callback,
        confirm_callback=lambda data: "n"
    )
    assert not swimmer.empty
    assert swimmer.iloc[0]["First name"] == "jane"
    assert swimmer.iloc[0]["Surname"] == "doe"
    assert automatic[("jane", "doe")] == ("jane", "doe")


def test_match_swimmer_manual():
    df = mock_df()
    automatic = {}
    manual = {}
    swimmer = match_swimmer(
        "jon", "smyth", df, automatic, manual,
        progress_callback=mock_progress_callback,
        confirm_callback=lambda data: "y"
    )
    assert not swimmer.empty
    assert manual[("jon", "smyth")] == ("john", "smith")


def test_match_swimmer_ignore():
    df = mock_df()
    automatic = {}
    manual = {}
    swimmer = match_swimmer(
        "jon", "smyth", df, automatic, manual,
        progress_callback=mock_progress_callback,
        confirm_callback=lambda data: "ignore"
    )
    assert swimmer.empty


def test_match_swimmer_exit():
    df = mock_df()
    automatic = {}
    manual = {}
    with pytest.raises(KeyboardInterrupt):
        _ = match_swimmer(
            "jon", "smyth", df, automatic, manual,
            progress_callback=mock_progress_callback,
            confirm_callback=lambda data: "exit"
        )
