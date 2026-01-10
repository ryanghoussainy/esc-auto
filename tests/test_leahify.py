import pandas as pd
from leahify_qualifiers import TIME_COLUMN_INDEX
from leahify_qualifiers.main import add_time_column, combine_tables, restore_final_column, get_extras_per_event, add_extras_to_leah_tables


def test_add_time_column():
    table = pd.DataFrame(columns=["Lane", "Name", "Age", "Team", "Seed Time", ""])
    tables = [table.copy()]
    add_time_column(tables)
    assert tables[0].columns[TIME_COLUMN_INDEX] in ("Time", "Finals")


def test_combine_tables():
    t1 = pd.DataFrame([
        ["Event 1 Boys 8 & Under 25 SC Meter Free", "", "", "", "", "Time"],
        ["Lane", "Name", "Team", "ASA", "DOB", "Time"],
        ["1", "John, Doe", "Acton", "123", "2001-01-01", "nan"],
    ], columns=["Lane", "Name", "Team", "ASA", "DOB", "Time"])
    t2 = pd.DataFrame([
        ["Event 2 Girls 8 & Under 25 SC Meter Free", "", "", "", "", "Time"],
        ["Lane", "Name", "Team", "ASA", "DOB", "Time"],
        ["1", "Jane, Doe", "Acton", "456", "2002-02-02", "19.50"],
    ], columns=["Lane", "Name", "Team", "ASA", "DOB", "Time"])
    out = combine_tables([t1, t2], "Time")
    assert "Time" in out.columns
    assert "" in out["Time"].values
    assert "19.50" in out["Time"].values


def test_restore_final_column():
    # Prepare a combined table where a finals event header exists
    finals_event_header = ["Event 99 Girls Open 200 SC Meter IM", "", "", "", "", "Time"]
    t = pd.DataFrame([
        finals_event_header,
        ["Lane", "Name", "Team", "ASA", "DOB", "Time"],
        ["1", "Jane, Doe", "Acton", "456", "2002-02-02", "19.50"],
    ], columns=["Lane", "Name", "Team", "ASA", "DOB", "Time"])
    out = combine_tables([t], "Time")
    restore_final_column(out)
    # After restore, header-row below finals event should read "Finals"
    # Find the first header row and check the next row's TIME_COLUMN_INDEX value
    assert out.iloc[1, TIME_COLUMN_INDEX] == "Finals"


def test_get_extras_per_event():
    # Qualifiers with swimmer who swam both events but only matched in one
    qualifiers = pd.DataFrame([
        {"First name": "jane", "Surname": "doe", "ASA": "A1", "DOB": "2002-02-02", "Group": "Dolphins", "25m Free": "19.50", "25m Breast": "22.10"},
    ])
    events = ["25m Free", "25m Breast"]
    swimmer_info = {("jane", "doe"): (0, 8, "girls")}
    # Jane matched only in Free, missing Breast
    matched_events = {("jane", "doe"): ["25m Free"]}

    extras = get_extras_per_event(qualifiers, events, swimmer_info, matched_events)

    # Expect Jane to be in extras for Breast event with correct age/gender
    assert ("25m Breast", 0, 8, "girls") in extras
    assert len(extras[("25m Breast", 0, 8, "girls")]) == 1


def test_add_extras_to_leah_tables_no_extras():
    # Verify add_extras_to_leah_tables processes tables without error
    leah_tables = [
        pd.DataFrame([
            ["Event 21 Girls 8 & Under 25 SC Meter Freestyle", "", "", "", "", "Time"],
            ["Lane", "Name", "Team", "ASA", "DOB", "Time"],
        ], columns=["Lane", "Name", "Team", "ASA", "DOB", "Time"]),
    ]
    extras = {}  # No extras in this case

    # Should not raise and should preserve table structure
    result = add_extras_to_leah_tables(leah_tables, extras)
    assert len(result) == 1
    assert result[0].columns.tolist() == leah_tables[0].columns.tolist()


def test_add_extras_to_leah_tables_with_extras():
    leah_tables = [
        pd.DataFrame([
            ["Event 21 Girls 8 & Under 25 SC Meter Freestyle", "", "", "", "", "Time"],
            ["Lane", "Name", "Team", "ASA", "DOB", "Time"],
            ["1", "Alice, Smith", "Acton", "A2", "2003-03-03", "20.00"],
        ], columns=["Lane", "Name", "Team", "ASA", "DOB", "Time"]),
    ]
    swimmer_df = pd.DataFrame([
        {"First name": "jane", "Surname": "doe", "ASA": "A1", "DOB": "2002-02-02", "Group": "Dolphins", "25m Free": "21.00"}
    ])
    extras = {
        ("25m Free", 0, 8, "girls"): [swimmer_df.iloc[0]],
    }
    result = add_extras_to_leah_tables(leah_tables, extras)
    # Verify that Jane Doe was added to the appropriate event table
    added = False
    for row in result[0].itertuples(index=False):
        if row.Lane == "jane" and row.Name == "doe":
            added = True
            break
    assert added
