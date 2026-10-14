import zipfile

import pytest

import error_reporting
from check_timesheets import check_timesheets


def test_value_errors_are_shown_as_is_and_expected():
    assert error_reporting.friendly_message(ValueError("Bad thing in file.xlsx")) == ("Bad thing in file.xlsx", True)


@pytest.mark.parametrize("exc, expected_text", [
    (FileNotFoundError(2, "No such file", "a.xlsx"), "a.xlsx"),
    (PermissionError(13, "denied", "b.xlsx"), "close it"),
    (zipfile.BadZipFile("File is not a zip file"), "not a valid Excel"),
])
def test_common_file_errors_are_translated(exc, expected_text):
    message, expected = error_reporting.friendly_message(exc)
    assert expected_text in message and expected


def test_unexpected_errors_show_type_and_traceback_via_callback():
    shown = []
    try:
        raise KeyError("House")
    except KeyError as e:
        error_reporting.report_error(e, lambda message, color=None: shown.append((message, color)))
    message, color = shown[0]
    assert "KeyError" in message and "Traceback" in message and color == "red"


def test_expected_errors_have_no_traceback():
    shown = []
    error_reporting.report_error(ValueError("Bad file"), lambda message, color=None: shown.append(message))
    assert shown == ["❌ ERROR: Bad file"]


def test_backends_raise_instead_of_swallowing(tmp_path):
    with pytest.raises(Exception):
        check_timesheets(str(tmp_path), str(tmp_path / "missing.xlsx"), {}, None, None, "September", lambda *a: None)
