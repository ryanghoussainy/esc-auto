import pandas as pd

from .read_sign_in import read_sign_in_sheet
from discrepancies import display_discrepancies
from reusables.entry import Entry
from discrepancies import EmptyTimesheet, InvalidName, TimesheetExtraEntry, SignInExtraEntry


DATE_COL = "Date"
WEEKDAY_COL = "Week day"
RATE_COL = "Rate of pay (see table below)"
COL_NAMES = ["Acton hours", "Admin hours", "Safeguarding hours", "GALA day rate", "House Event day rate"]

def read_timesheet(df) -> tuple[str, list[Entry]]:
    """
    Read a timesheet excel file and return a set of entries
    """
    # Get the name
    first_name = str(df.iloc[3, 2]).strip()
    last_name = str(df.iloc[4, 2]).strip()
    name = first_name + " " + last_name
    
    # Get the row index of the header
    header_row_index = df[df.iloc[:, 0] == DATE_COL].index[0]

    # From df, get all rows after the header row, including the header row
    table_df = df.iloc[header_row_index:]
    
    # Reset the index of the dataframe
    table_df.reset_index(drop=True, inplace=True)
    table_df.columns = table_df.iloc[0]
    table_df = table_df[1:]

    # Filter rows by those that have a date
    table_df.dropna(subset=[DATE_COL, WEEKDAY_COL], inplace=True)
    table_df.reset_index(drop=True, inplace=True)
    
    # Create a tuple of (number of hours, start time, end time, rate)
    timesheet_data = []
    
    for _, row in table_df.iterrows():
        hours_worked = [col_name for col_name in COL_NAMES if pd.notna(row[col_name])]

        if not hours_worked:
            raise ValueError(f"No hours found for {name} on {row[DATE_COL]}")
        if len(hours_worked) > 1:
            raise ValueError(f"Multiple hours found in a single row for {name} on {row[DATE_COL]}")
        
        entry = Entry(
            date=row[DATE_COL].date(),
            hours=float(row[hours_worked[0]]),
            rate=row[RATE_COL],
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
                df = pd.read_excel(xls, sheet_name=sheet_name)
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
        progress_callback(f"\nChecking timesheet for {name}...\n")
        for entry in timesheet_entries:
            if entry not in sign_in_set:
                discrepancies.append(TimesheetExtraEntry(name=name, entry=entry))
            else:
                # Successfully matched entry
                sign_in_set.remove(entry)
                timesheet_set.remove(entry)
