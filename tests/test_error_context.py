import pandas as pd
import pytest

from reusables import parse_swimmer, require_columns, check_event_counts
from check_timesheets.read_sign_in import read_sign_in_sheet


def test_parse_swimmer_errors_include_the_line():
    with pytest.raises(ValueError, match="Acton 12 Smith John"):
        parse_swimmer("Acton 12 Smith John")  # no comma


def test_require_columns_lists_missing_and_found():
    df = pd.DataFrame({"a": [1], "b": [2]})
    with pytest.raises(ValueError) as exc:
        require_columns(df, ["a", "c"], "the test table")
    assert "'c'" in str(exc.value) and "the test table" in str(exc.value) and "a, b" in str(exc.value)
    require_columns(df, ["a", "b"], "the test table")  # no error


def test_check_event_counts_only_fails_when_pdf_has_fewer():
    check_event_counts(3, 3, "Excel", "PDF")
    check_event_counts(3, 4, "Excel", "PDF")
    with pytest.raises(ValueError, match="3 events but the PDF only has 2"):
        check_event_counts(3, 2, "Excel", "the PDF")


def _write_sign_in(path, rows, month="September"):
    columns = ["Name", "Level", "Rate"] + list(pd.to_datetime(["2026-09-02", "2026-09-09"]))
    pd.DataFrame(rows, columns=columns).to_excel(path, sheet_name=month, index=False)


def test_sign_in_missing_tab_lists_available_tabs(tmp_path):
    path = tmp_path / "s.xlsx"
    _write_sign_in(path, [["A B", "L1", 0, 2.0, None]])
    with pytest.raises(ValueError, match="no tab called 'October'.*September"):
        read_sign_in_sheet("October", str(path), {"L1": 10.0}, None, None)


def test_sign_in_unknown_level_names_level_person_and_date(tmp_path):
    path = tmp_path / "s.xlsx"
    _write_sign_in(path, [["A B", "L3", 0, 2.0, None]])
    with pytest.raises(ValueError, match="'L3'.*A B.*2026-09-02"):
        read_sign_in_sheet("September", str(path), {"L1": 10.0}, None, None)


def test_sign_in_bad_hours_names_person_and_date(tmp_path):
    path = tmp_path / "s.xlsx"
    _write_sign_in(path, [["A B", "L1", 0, "sick", None]])
    with pytest.raises(ValueError, match="Invalid hours 'sick' for A B on 2026-09-02"):
        read_sign_in_sheet("September", str(path), {"L1": 10.0}, None, None)


def test_sign_in_missing_name_reports_excel_row(tmp_path):
    path = tmp_path / "s.xlsx"
    _write_sign_in(path, [[None, "L1", 0, 2.0, None]])
    with pytest.raises(ValueError, match="Row 2 .* no name"):
        read_sign_in_sheet("September", str(path), {"L1": 10.0}, None, None)


def test_sign_in_bad_rate_change_date_is_reported_as_such(tmp_path):
    path = tmp_path / "s.xlsx"
    _write_sign_in(path, [["A B", "L1", 0, 2.0, None]])
    with pytest.raises(ValueError, match="DD/MM/YYYY"):
        read_sign_in_sheet("September", str(path), {"L1": 10.0}, {"L1": 11.0}, "2026-13-01")
