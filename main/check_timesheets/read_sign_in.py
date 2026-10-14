import pandas as pd
from collections import defaultdict

from reusables.entry import Entry
from reusables.events import is_event, event_rate_key

NAME_COL = "Name"
LEVEL_COL = "Level"


def _lookup_rate(rate_table: dict[str, float], key: str, name: str, date, after_change: bool) -> float:
    """Look up a rate, explaining exactly what is missing if it isn't there."""
    if key not in rate_table:
        which = " (the 'after rate change' rates)" if after_change else ""
        raise ValueError(
            f"No rate is set for '{key}'{which}, needed for {name} on {date} in the sign in sheet. "
            f"Add it in the Rates tab."
        )
    return rate_table[key]


def read_sign_in_sheet(
    month: str,
    file_path: str,
    rates: dict[str, float],
    rates_after: dict[str, float] | None,
    rate_change_date: str | None
) -> dict[str, set[Entry]]:
    """
    Read a sign in sheet excel file and return a map from name to set of entries
    """
    with pd.ExcelFile(file_path) as workbook:
        if month not in workbook.sheet_names:
            raise ValueError(
                f"The sign in sheet has no tab called '{month}'. "
                f"Tabs found: {', '.join(workbook.sheet_names)}. The tab name must match the selected month exactly."
            )
        sign_df = workbook.parse(month, header=0)

    missing_cols = [c for c in (NAME_COL, LEVEL_COL) if c not in sign_df.columns]
    if missing_cols:
        raise ValueError(
            f"The '{month}' tab of the sign in sheet is missing the column(s): {', '.join(missing_cols)}. "
            f"Columns found: {', '.join(str(c) for c in sign_df.columns[:6])}..."
        )

    # Parse the rate change date once, up front, so a bad date is reported as such
    change_date = None
    if rate_change_date and rates_after:
        try:
            change_date = pd.to_datetime(rate_change_date, format="%d/%m/%Y").date()
        except ValueError:
            raise ValueError(f"Rate change date '{rate_change_date}' is in invalid format. It must be in DD/MM/YYYY format.")

    sign_in_sheet_data = defaultdict(set)

    for idx, row in sign_df.iterrows():
        # Skip rows below the table and LHC rows
        if pd.isna(row[LEVEL_COL]) or row[LEVEL_COL] == "LHC":
            continue

        if pd.isna(row[NAME_COL]) or not str(row[NAME_COL]).strip():
            # idx + 2: the header is row 1 in Excel and pandas is 0-indexed
            raise ValueError(f"Row {idx + 2} of the '{month}' tab has level '{row[LEVEL_COL]}' but no name.")
        name = str(row[NAME_COL]).strip()

        for col in sign_df.columns[3:]:
            # Skip empty cells
            if pd.isna(row[col]):
                continue

            if not hasattr(col, "date"):
                raise ValueError(
                    f"Unexpected column '{col}' in the '{month}' tab of the sign in sheet "
                    f"(found a value for {name}, but the column header is not a date)."
                )

            # Determine which rate table to use based on the date and rate change date
            after_change = change_date is not None and col.date() >= change_date
            rate_table = rates_after if after_change else rates

            if is_event(row[col]):
                rate = _lookup_rate(rate_table, event_rate_key(row[col]), name, col.date(), after_change)
                entry = Entry(
                    date=col.date(),
                    hours=0.0,
                    rate=rate,
                    is_event=True
                )
            else:
                rate = _lookup_rate(rate_table, row[LEVEL_COL], name, col.date(), after_change)
                try:
                    hours = float(row[col])
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Invalid hours '{row[col]}' for {name} on {col.date()} in the sign in sheet "
                        f"(expected a number, or a gala/house event)."
                    )
                entry = Entry(
                    date=col.date(),
                    hours=hours,
                    rate=rate,
                    is_event=False
                )
            sign_in_sheet_data[name].add(entry)

    return sign_in_sheet_data
