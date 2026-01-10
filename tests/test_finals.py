import pandas as pd
from reusables.finals import is_final, rename_final_column


def test_main_events():
    assert not is_final("25m Free")
    assert not is_final("100m IM")


def test_non_main_events():
    assert is_final("200m Free")
    assert is_final("200m IM")


def test_rename_final_column():
    df = pd.DataFrame(columns=["Lane", "Name", "Team", "ASA", "DOB", "Finals"])
    tables = [df.copy()]
    rename_final_column(tables, "Time")
    assert "Time" in tables[0].columns
    assert "Finals" not in tables[0].columns
