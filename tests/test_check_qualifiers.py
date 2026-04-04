import pandas as pd

from check_qualifiers.main import has_recorded_time


def test_has_recorded_time():
    assert has_recorded_time("59.99")
    assert has_recorded_time("DQ")
    assert not has_recorded_time("DNS")
    assert not has_recorded_time(" dns ")
    assert not has_recorded_time("")
    assert not has_recorded_time("   ")
    assert not has_recorded_time(float("nan"))
    assert not has_recorded_time(pd.NA)
