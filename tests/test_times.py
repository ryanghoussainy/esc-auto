from reusables.times import normalise_time


def test_normalise_time():
    assert normalise_time("1:23.45") == "1.23.45"
    assert normalise_time("1,23.45") == "1.23.45"
    assert normalise_time("59.99") == "59.99"
    assert normalise_time(59.99) == "59.99"
