import pandas as pd
from datetime import datetime
from openpyxl import load_workbook

from .read_sign_in import read_sign_in_sheet
from discrepancies import display_discrepancies
from reusables.entry import Entry
from reusables.events import is_event
from discrepancies import EmptyTimesheet, InvalidName, TimesheetExtraEntry, SignInExtraEntry


NAME_CELL = (2, 2)
DATE_COL = "Date"
START_TIME_COL = "Start"
END_TIME_COL = "End"
HOUSE_COL = "House"
LEVEL_COL = "Level"
RATE_INCREASE_COL_IDX = 6
ADMIN_RATE_INCREASE = 1.05

def read_timesheet(df) -> tuple[str, list[Entry]]:
    """
    Read a timesheet excel file and return a set of entries
    """
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
    timesheet_data = []
    
    for _, row in table_df.iterrows():
        # Get start time and end time
        start_time = row[START_TIME_COL]
        end_time = row[END_TIME_COL]
        if pd.isna(start_time) or pd.isna(end_time):
            raise ValueError(f"Missing start or end time for {name} on {row[DATE_COL]}")
        
        # Calculate hours worked
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
        timesheet_data.append(entry)

    return name, timesheet_data


def check_timesheets(
    amindefied_excel_path,
    sign_in_sheet_path, rates,
    rates_after,
    rate_change_date,
    month,
    progress_callback,
    error_callback
):
    try:
        # Check for discrepancies
        discrepancies = []

        # Read sign in sheet
        sign_in_data = read_sign_in_sheet(month, sign_in_sheet_path, rates, rates_after, rate_change_date)

        with pd.ExcelFile(amindefied_excel_path) as xls:
            for sheet_name in xls.sheet_names:
                # Read individual timesheet
                wb = load_workbook(amindefied_excel_path, read_only=True, data_only=False)
                ws = wb[sheet_name]
                df = pd.DataFrame(ws.values)
                if df.empty:
                    discrepancies.append(EmptyTimesheet(sheet_name=sheet_name))

                check_timesheet(df, sign_in_data, discrepancies, progress_callback)
        
        # Check for remaining entries in sign in data
        for name, entries in sign_in_data.items():
            for entry in entries:
                discrepancies.append(SignInExtraEntry(name=name, entry=entry))

        display_discrepancies(discrepancies, progress_callback)
    
    except Exception as e:
        error_callback(f"❌ ERROR: {str(e)}", "red")


def check_timesheet(df, sign_in_data: dict[str, set[Entry]], discrepancies, progress_callback):
    """
    Check a single timesheet against the sign in data and display any discrepancies found.
    """
    # Read the timesheet
    name, timesheet_entries = read_timesheet(df)

    # Check if timesheet name is correct
    if name not in sign_in_data:
        sign_in_names = list(sign_in_data.keys())
        discrepancies.append(InvalidName(name=name, sign_in_names=sign_in_names))
    else:
        # Make sets for comparison to not modify the original data
        timesheet_set = set(timesheet_entries)
        sign_in_set = sign_in_data[name]

        # For each entry in the timesheet data, match and remove from the sign in data
        progress_callback(f"Checking timesheet for {name}...\n")
        for entry in timesheet_entries:
            if entry not in sign_in_set:
                discrepancies.append(TimesheetExtraEntry(name=name, entry=entry))
            else:
                # Successfully matched entry
                sign_in_set.remove(entry)
                timesheet_set.remove(entry)


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
        
