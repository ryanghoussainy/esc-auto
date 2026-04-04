from discrepancies.discrepancies import display_discrepancies
from discrepancies.discrepancy_types import (
    TimeDiscrepancy,
    SwimmersNotFound,
    InvalidName,
)


def collect_messages():
    messages = []

    def callback(message, color=None):
        messages.append((message, color))

    return messages, callback


def test_display_discrepancies_house_champs_summary_and_details():
    messages, callback = collect_messages()
    discrepancies = [
        TimeDiscrepancy("Jane Doe", "50m Free", "31.22", "31.44"),
        SwimmersNotFound(["Smith, John"], event_name="100m Breast"),
    ]

    display_discrepancies(discrepancies, callback)

    text_lines = [msg for msg, _ in messages]

    assert "Mismatches found: 2" in text_lines
    assert "Summary by category:" in text_lines
    assert "- Time mismatches: 1" in text_lines
    assert "- Missing swimmers: 1" in text_lines
    assert any("Time mismatch for Jane Doe" in line for line in text_lines)
    assert any("Swimmers Smith, John not found in PDF (Event: 100m Breast)" in line for line in text_lines)


def test_display_discrepancies_mixed_types_prints_both_sections():
    messages, callback = collect_messages()
    discrepancies = [
        InvalidName("Jnae", ["Jane"]),
        TimeDiscrepancy("Jane Doe", "50m Free", "31.22", "31.44"),
    ]

    display_discrepancies(discrepancies, callback)

    text_lines = [msg for msg, _ in messages]

    assert "Summary by category:" in text_lines
    assert "- Name issues: 1" in text_lines
    assert "- Time mismatches: 1" in text_lines


def test_display_discrepancies_dedupes_missing_swimmer_in_pdf():
    messages, callback = collect_messages()
    discrepancies = [
        SwimmersNotFound(["Smith, John"]),
        SwimmersNotFound(["Smith, John"]),
    ]

    display_discrepancies(discrepancies, callback)

    text_lines = [msg for msg, _ in messages]
    missing_messages = [line for line in text_lines if line == "Swimmers Smith, John not found in PDF"]

    assert "- Missing swimmers: 1" in text_lines
    assert len(missing_messages) == 1


def test_display_discrepancies_keeps_missing_swimmer_entries_for_different_events():
    messages, callback = collect_messages()
    discrepancies = [
        SwimmersNotFound(["Smith, John"], event_name="100m Breast"),
        SwimmersNotFound(["Smith, John"], event_name="200m IM"),
    ]

    display_discrepancies(discrepancies, callback)

    text_lines = [msg for msg, _ in messages]

    assert "- Missing swimmers: 2" in text_lines
    assert "Swimmers Smith, John not found in PDF (Event: 100m Breast)" in text_lines
    assert "Swimmers Smith, John not found in PDF (Event: 200m IM)" in text_lines
