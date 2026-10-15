import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import os

from .read_sign_in import read_sign_in_sheet
from .timesheet_rates import read_rates
from discrepancies import display_discrepancies
from error_reporting import friendly_message
from input_validation import require_file, require_folder, EXCEL_EXTENSIONS
from constants import MONTHS
from reusables.entry import Entry
from reusables.events import is_event
from discrepancies import EmptyTimesheet, InvalidName, UnreadableTimesheet, TimesheetMonthMismatch, TimesheetExtraEntry, SignInExtraEntry, Discrepancy


NAME_CELL = (2, 2)
DATE_COL = "Date"
START_TIME_COL = "Start"
END_TIME_COL = "End"
HOUSE_COL = "House"
LEVEL_COL = "Level"
PAYROLL_MONTH_LABEL = "payroll month"
MONTH_SEARCH_ROWS = 8
MONTH_NAMES_LOWER = {m.lower() for m in MONTHS}

def _read_month_label(df) -> str | None:
    """
    Find the month written on the timesheet: the cell to the right of "Payroll Month:" near the top.
    Returns the month name (e.g. "September"), or None if it isn't there or isn't recognisable.
    """
    for _, row in df.head(MONTH_SEARCH_ROWS).iterrows():
        values = list(row.values)
        for i, value in enumerate(values):
            if isinstance(value, str) and value.strip().lower().rstrip(":").rstrip("*") == PAYROLL_MONTH_LABEL:
                for candidate in values[i + 1:]:
                    if isinstance(candidate, str) and candidate.strip():
                        return candidate.strip()
                    if isinstance(candidate, datetime):
                        return candidate.strftime("%B")
                return None
    return None


def _read_timesheet(timesheet_path) -> tuple[str, set[Entry], str | None]:
    """
    Read a timesheet excel file and return the employee name, a set of entries,
    and the month written on the timesheet (None if it couldn't be found).
    """
    filename = os.path.basename(timesheet_path)

    # Get dataframe from excel file
    wb = load_workbook(timesheet_path, read_only=True, data_only=False)
    ws = wb.active
    df = pd.DataFrame(ws.values)

    # Get the name
    raw_name = df.iloc[NAME_CELL] if df.shape[0] > NAME_CELL[0] and df.shape[1] > NAME_CELL[1] else None
    if raw_name is None or pd.isna(raw_name) or not str(raw_name).strip():
        raise ValueError(f"{filename}: could not find the employee name in cell C3. Is this the current timesheet template?")
    name = str(raw_name).strip()
    who = f"{name} ({filename})"
    
    # Get the row index of the header
    header_matches = df[df.iloc[:, 0].apply(lambda v: _clean_header(v) == DATE_COL)].index
    if len(header_matches) == 0:
        raise ValueError(f"{who}: could not find the table header (a '{DATE_COL}' cell in column A). Is this the current timesheet template?")
    header_row_index = header_matches[0]

    # From df, get all rows after the header row, including the header row
    table_df = df.iloc[header_row_index:]
    
    # Reset the index of the dataframe
    table_df.reset_index(drop=True, inplace=True)
    table_df.columns = [_clean_header(c) for c in table_df.iloc[0]]
    table_df = table_df[1:]

    missing_cols = [c for c in (DATE_COL, START_TIME_COL, END_TIME_COL, HOUSE_COL, LEVEL_COL) if c not in table_df.columns]
    if missing_cols:
        raise ValueError(f"{who}: missing expected column(s): {', '.join(missing_cols)}. Is this the current timesheet template?")

    # Filter rows by those that have a date
    table_df = table_df[table_df[DATE_COL].apply(lambda x: isinstance(x, datetime))]
    table_df.reset_index(drop=True, inplace=True)
    
    rates = read_rates(df, who)

    # Create list of entries
    entries = set()
    
    for _, row in table_df.iterrows():
        # Get start time and end time
        start_time = row[START_TIME_COL]
        end_time = row[END_TIME_COL]
        entry_date = row[DATE_COL].date()
        # error if either is nan and we are not a house event
        if (pd.isna(start_time) or pd.isna(end_time)) and not is_event(row[LEVEL_COL]):
            raise ValueError(f"{who}: missing start or end time on {entry_date}")
        
        # Calculate hours worked
        if is_event(row[LEVEL_COL]):
            hours_worked = 0.0
        else:
            for label, value in (("start", start_time), ("end", end_time)):
                if not hasattr(value, "hour"):
                    raise ValueError(f"{who}: the {label} time on {entry_date} is not a valid time (found {value!r})")
            end_hours = end_time.hour + end_time.minute / 60
            start_hours = start_time.hour + start_time.minute / 60
            hours_worked = end_hours - start_hours
            if hours_worked <= 0:
                raise ValueError(f"{who}: end time must be after start time on {entry_date} ({start_time} - {end_time})")

        # Get house - if it's not acton then skip
        house = row[HOUSE_COL]
        if house != "Acton":
            continue

        # Get level
        if not isinstance(row[LEVEL_COL], str) or not row[LEVEL_COL].strip():
            raise ValueError(f"{who}: missing level on {entry_date}")
        level = row[LEVEL_COL].lower()

        # Get rate (it can depend on the date, if the rates changed part way through the timesheet)
        rate = rates.rate_for(level, entry_date)
        if rate is None:
            raise ValueError(
                f"{who}: invalid level '{row[LEVEL_COL]}' on {entry_date}. "
                f"Valid levels are: {', '.join(rates.levels())}"
            )

        # Create entry
        entry = Entry(
            date=entry_date,
            hours=hours_worked,
            rate=rate,
            is_event=is_event(level)
        )
        entries.add(entry)

    return name, entries, _read_month_label(df)


def check_timesheets(
    timesheets_folder_path,
    sign_in_sheet_path,
    rates,
    rates_after,
    rate_change_date,
    month,
    progress_callback,
) -> None:
    """
    Check the timesheets against the sign in sheet and report any discrepancies through progress_callback.
    Raises if the sign in sheet can't be read. A problem with an individual timesheet is reported as a
    discrepancy instead, so one bad file doesn't stop the others being checked.
    """
    require_folder(timesheets_folder_path, "timesheets folder")
    require_file(sign_in_sheet_path, "sign in sheet", EXCEL_EXTENSIONS)

    # Fail fast if the folder has nothing to check, rather than reporting a misleading "No mismatches found"
    timesheets_filenames = sorted([f for f in os.listdir(timesheets_folder_path) if _is_valid_xlsx(f)], key=_clean_filename)
    if not timesheets_filenames:
        raise ValueError(
            f"No .xlsx timesheets were found in '{timesheets_folder_path}'. "
            f"Check you selected the right folder (files must end in .xlsx)."
        )

    # Check for discrepancies
    discrepancies = []

    # Map from name to set of entries from the sign in sheet
    sign_in_data = read_sign_in_sheet(month, sign_in_sheet_path, rates, rates_after, rate_change_date)

    # This will hold a map from name to a set of entries (same structure as sign_in_data)
    timesheets_data = {}

    for timesheet_filename in timesheets_filenames:
        timesheet_path = os.path.join(timesheets_folder_path, timesheet_filename)

        # A problem with one timesheet shouldn't stop us checking all the others
        try:
            name, entries, month_label = _read_timesheet(timesheet_path)
        except Exception as e:
            message, _ = friendly_message(e)
            # ValueErrors are our own readable messages, which already include the filename
            reason = message if isinstance(e, ValueError) else f"{timesheet_filename}: {message}"
            discrepancies.append(UnreadableTimesheet(filename=timesheet_filename, reason=reason))
            continue
        # Warn if the timesheet was filled in for a different month than the one being checked
        if month_label and month_label.lower() in MONTH_NAMES_LOWER and month_label.lower() != month.lower():
            discrepancies.append(TimesheetMonthMismatch(name=name, found_month=month_label, expected_month=month))
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


def _clean_header(value):
    """Column headers can be marked as required with a trailing '*' (e.g. 'Date*'); ignore it."""
    return value.strip().rstrip("*").strip() if isinstance(value, str) else value


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
