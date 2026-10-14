from datetime import datetime

import pandas as pd
import pytest

from check_timesheets import check_timesheets
from check_timesheets.main import _read_month_label
from discrepancies import display_discrepancies, TimesheetMonthMismatch
from input_validation import require_file, require_folder, require_writable_output, EXCEL_EXTENSIONS, PDF_EXTENSIONS


def test_require_file_accepts_a_valid_file(tmp_path):
    f = tmp_path / "a.XLSX"  # extension check is case-insensitive
    f.write_text("x")
    require_file(str(f), "sign in sheet", EXCEL_EXTENSIONS)


def test_require_file_rejects_missing_none_folder_and_wrong_type(tmp_path):
    with pytest.raises(ValueError, match="No sign in sheet selected"):
        require_file(None, "sign in sheet")
    with pytest.raises(ValueError, match="could not be found"):
        require_file(str(tmp_path / "nope.xlsx"), "sign in sheet")
    with pytest.raises(ValueError, match="is a folder"):
        require_file(str(tmp_path), "sign in sheet")
    wrong = tmp_path / "results.docx"
    wrong.write_text("x")
    with pytest.raises(ValueError, match=r"\.pdf file, but 'results.docx' is not"):
        require_file(str(wrong), "results PDF", PDF_EXTENSIONS)


def test_require_folder(tmp_path):
    require_folder(str(tmp_path), "timesheets folder")
    with pytest.raises(ValueError, match="No timesheets folder selected"):
        require_folder("", "timesheets folder")
    with pytest.raises(ValueError, match="could not be found"):
        require_folder(str(tmp_path / "gone"), "timesheets folder")


def test_require_writable_output(tmp_path):
    require_writable_output(str(tmp_path / "out.xlsx"))
    with pytest.raises(ValueError, match="does not exist"):
        require_writable_output(str(tmp_path / "missing_dir" / "out.xlsx"))


def test_empty_timesheets_folder_is_an_error_not_a_false_pass(tmp_path):
    sign_in = tmp_path / "sign.xlsx"
    pd.DataFrame({"Name": []}).to_excel(sign_in, sheet_name="September", index=False)
    folder = tmp_path / "timesheets"
    folder.mkdir()
    (folder / "~$lock.xlsx").write_text("x")  # Excel lock files don't count
    (folder / "notes.txt").write_text("x")
    with pytest.raises(ValueError, match="No .xlsx timesheets were found"):
        check_timesheets(str(folder), str(sign_in), {}, None, None, "September", lambda *a: None)


def test_read_month_label_finds_text_and_dates():
    df = pd.DataFrame([[None, None, "Bob", None, "Payroll Month:", "September"]])
    assert _read_month_label(df) == "September"
    df = pd.DataFrame([["Employee Name:", None, "Bob", None, None, "Month:", "July"]])
    assert _read_month_label(df) is None  # old template label isn't recognised, so we don't guess
    df = pd.DataFrame([[None, "Payroll Month:", None, datetime(2026, 9, 1)]])
    assert _read_month_label(df) == "September"


def test_month_mismatch_is_displayed():
    lines = []
    display_discrepancies([TimesheetMonthMismatch("Bob", "July", "September")], lambda m, c=None: lines.append(m))
    text = "\n".join(lines)
    assert "Timesheets for the wrong month: 1" in text
    assert "Bob's timesheet says 'July' but you are checking 'September'" in text
