import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import os

from .read_sign_in import read_sign_in_sheet
from discrepancies import display_discrepancies
from reusables.entry import Entry
from reusables.events import is_event
from discrepancies import EmptyTimesheet, InvalidName, TimesheetExtraEntry, SignInExtraEntry, Discrepancy


NAME_CELL = (2, 2)
DATE_COL = "Date"
START_TIME_COL = "Start"
END_TIME_COL = "End"
HOUSE_COL = "House"
LEVEL_COL = "Level"
RATE_INCREASE_COL_IDX = 6
ADMIN_RATE_INCREASE = 1.05

def _read_timesheet(timesheet_path) -> tuple[str, set[Entry]]:
    """
    Read a timesheet excel file and return a set of entries
    """
    # Get dataframe from excel file
    wb = load_workbook(timesheet_path, read_only=True, data_only=False)
    ws = wb.active
    df = pd.DataFrame(ws.values)

    # Get the name
    name = str(df.iloc[NAME_CELL]).strip()
    
    # Get the row index of the header
    header_row_index = df[df.iloc[:, 0] == DATE_COL].index[0]

    # From df, get all rows after the header row, including the header row
    table_df = df.iloc[header_row_index:]
    
    # Reset the index of the dataframe
    table_df.reset_index(drop=True, inplace=True)
    table_df.columns = table_df.iloc[0]
    table_df = table_df[1:]

    # Filter rows by those that have a date
    table_df = table_df[table_df[DATE_COL].apply(lambda x: isinstance(x, datetime))]
    table_df.reset_index(drop=True, inplace=True)
    
    # Find the rate table header
    rate_table_header = "Standard rates of pay (exclusive of holiday pay) "
    header_row = None
    for idx, row in df.iterrows():
        if rate_table_header in row.values:
            header_row = idx
            break
    
    if header_row is None:
        raise ValueError(f"Could not find rate table header '{rate_table_header}' in timesheet for {name}")
    
    # Get rate of increase
    rate_increase = 1 + df.iloc[header_row - 1, RATE_INCREASE_COL_IDX]
    
    # Read normal rates table (levels and rates)
    level_to_rate = {}
    read_rates_table(df, start_row=header_row + 1, levels_col=4, is_events_table=False, level_to_rate=level_to_rate, rate_increase=rate_increase)
    read_rates_table(df, start_row=header_row + 1, levels_col=9, is_events_table=True, level_to_rate=level_to_rate, rate_increase=rate_increase)

    # Create list of entries
    entries = set()
    
    for _, row in table_df.iterrows():
        # Get start time and end time
        start_time = row[START_TIME_COL]
        end_time = row[END_TIME_COL]
        # error if either is nan and we are not a house event
        if (pd.isna(start_time) or pd.isna(end_time)) and not is_event(row[LEVEL_COL]):
            raise ValueError(f"Missing start or end time for {name} on {row[DATE_COL]}")
        
        # Calculate hours worked
        if is_event(row[LEVEL_COL]):
            hours_worked = 0.0
        else:
            end_hours = end_time.hour + end_time.minute / 60
            start_hours = start_time.hour + start_time.minute / 60
            hours_worked = end_hours - start_hours
            if hours_worked <= 0:
                raise ValueError(f"End time must be after start time for {name} on {row[DATE_COL]}")

        # Get house - if it's not acton then skip
        house = row[HOUSE_COL]
        if house != "Acton":
            continue

        # Get level
        level = row[LEVEL_COL].lower()

        # Get rate
        if level not in level_to_rate:
            raise ValueError(f"Invalid level '{level}' for {name} on {row[DATE_COL]}")
        rate = level_to_rate[level]

        # Create entry
        entry = Entry(
            date=row[DATE_COL].date(),
            hours=hours_worked,
            rate=rate,
            is_event=is_event(level)
        )
        entries.add(entry)

    return name, entries


def check_timesheets(
    timesheets_folder_path,
    sign_in_sheet_path,
    rates,
    rates_after,
    rate_change_date,
    month,
    progress_callback,
    error_callback
):
    try:
        # Check for discrepancies
        discrepancies = []

        # Map from name to set of entries from the sign in sheet
        sign_in_data = read_sign_in_sheet(month, sign_in_sheet_path, rates, rates_after, rate_change_date)

        # This will hold a map from name to a set of entries (same structure as sign_in_data)
        timesheets_data = {}

        timesheets_filenames = sorted([f for f in os.listdir(timesheets_folder_path) if _is_valid_xlsx(f)], key=_clean_filename)
        for timesheet_filename in timesheets_filenames:
            timesheet_path = os.path.join(timesheets_folder_path, timesheet_filename)

            name, entries = _read_timesheet(timesheet_path)
            if not entries:
                discrepancies.append(EmptyTimesheet(name=name))
            timesheets_data[name] = entries

        # Compare timesheets data with sign in data
        for name, timesheet_entries in timesheets_data.items():
            if name not in sign_in_data:
                discrepancies.append(InvalidName(name=name, sign_in_names=list(sign_in_data.keys())))
                continue

            check_timesheet(name, timesheet_entries, sign_in_data[name], discrepancies, progress_callback)
        
        # Check for remaining entries in sign in data
        for name, sign_in_entries in sign_in_data.items():
            for sign_in_entry in sign_in_entries:
                discrepancies.append(SignInExtraEntry(name=name, entry=sign_in_entry))

        display_discrepancies(discrepancies, progress_callback)
    
    except Exception as e:
        error_callback(f"❌ ERROR: {str(e)}", "red")


def check_timesheet(
    name: str,
    timesheet_entries: set[Entry],
    sign_in_entries: set[Entry],
    discrepancies: list[Discrepancy],
    progress_callback
):
    """
    Check a single timesheet against the sign in data and append any discrepancies found.
    """
    # For each entry in the timesheet data, match and remove from the sign in data
    progress_callback(f"Checking timesheet for {name}...\n")
    for entry in list(timesheet_entries):
        if entry not in sign_in_entries:
            discrepancies.append(TimesheetExtraEntry(name=name, entry=entry))
            continue

        # Successfully matched entry
        sign_in_entries.remove(entry)


def read_rates_table(df, start_row, levels_col, is_events_table, level_to_rate, rate_increase):
    """Read rates table (normal or events) and populate level_to_rate dictionary."""
    current_row = start_row
    rates_col = levels_col + 2 if not is_events_table else levels_col + 1

    while current_row < len(df):
        level = df.iloc[current_row, levels_col]

        # If the level is not other, read the hidden column for this rate, otherwise read the visible column
        if level != "Other":
            rate = df.iloc[current_row, rates_col]
        else:
            rate = df.iloc[current_row, rates_col - 1]

        # Stop at empty row
        if pd.isna(level) or level == "":
            break
        
        # Only add if rate is not empty
        if not pd.isna(rate) and rate != "":
            level_to_rate[level.lower()] = rate
        
        current_row += 1
    
    # Apply rate increase if normal rates table
    if not is_events_table:
        for lvl in level_to_rate:
            if lvl in ("admin", "training"):
                level_to_rate[lvl] = round(level_to_rate[lvl] * ADMIN_RATE_INCREASE, 2)
            elif lvl != "other":
                level_to_rate[lvl] = round(level_to_rate[lvl] * rate_increase, 2)

def _clean_filename(filename: str):
    """Remove useless info from timesheet file name attempt to sort by employee name"""
    to_delete = ["L1", "ENL2", "NQL2", "L2", "and", "&"] # Note: L2 must be after NQL2 and ENL2
    
    sort_key = filename
    for item in to_delete:
        sort_key = sort_key.replace(item, "")

    return sort_key.strip().lower()

def _is_valid_xlsx(filename: str) -> bool:
    """Check if a file is a valid xlsx file (not temporary or hidden)"""
    return filename.endswith(".xlsx") and not filename.startswith("~$")
