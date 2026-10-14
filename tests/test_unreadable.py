from discrepancies import display_discrepancies, UnreadableTimesheet, UnparsedPdfLine
from reusables import read_pdf
import reusables.parsing as parsing


def _collect():
    lines = []
    return lines, lambda message, color=None: lines.append(message)


def test_unreadable_timesheets_are_listed():
    lines, callback = _collect()
    display_discrepancies([UnreadableTimesheet("Bob.xlsx", "Bob.xlsx: bad template")], callback)
    text = "\n".join(lines)
    assert "Unreadable timesheets: 1" in text
    assert "Bob.xlsx: bad template" in text


def test_unparsed_pdf_lines_are_listed():
    lines, callback = _collect()
    display_discrepancies([UnparsedPdfLine("Event 1", "Acton 1 Bad Line", "No comma")], callback)
    text = "\n".join(lines)
    assert "Unreadable PDF lines: 1" in text
    assert "Acton 1 Bad Line" in text


def test_read_pdf_skips_bad_lines_when_asked_and_raises_otherwise(monkeypatch):
    class Page:
        def extract_text(self):
            return "Event 1 Girls 25 SC Meter Freestyle\nName Team\nActon 1 Smith, Jo 30.00 NT\nActon 2 Broken 30.00 NT\n"

    class Reader:
        pages = [Page()]

    monkeypatch.setattr(parsing, "PdfReader", lambda path: Reader())

    skipped = []
    tables = read_pdf("x.pdf", isQualifiers=True, skipped_lines=skipped)
    assert len(tables) == 1 and len(tables[0]) == 1
    assert skipped and "Acton 2 Broken" in skipped[0][1]

    import pytest
    with pytest.raises(ValueError, match="Event 1"):
        read_pdf("x.pdf", isQualifiers=True)
