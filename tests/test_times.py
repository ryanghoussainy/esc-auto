from reusables.times import normalise_time, is_disqualification


def test_normalise_time():
    assert normalise_time("1:23.45") == "1.23.45"
    assert normalise_time("1,23.45") == "1.23.45"
    assert normalise_time("59.99") == "59.99"
    assert normalise_time(59.99) == "59.99"


def test_is_disqualification():
    assert is_disqualification("DQ")
    assert is_disqualification("dq")
    assert is_disqualification("2.24.34dq 7.5")
    assert not is_disqualification("1:23.45")
