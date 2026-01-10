import pandas as pd
from collections import defaultdict

from reusables.entry import Entry, is_event_sign_in

NAME_COL = "Name"
LEVEL_COL = "Level"


def read_sign_in_sheet(month: str, file_path: str, rates: dict[str, float], rates_after: dict[str, float] | None, rate_change_date: str | None) -> dict[str, set[Entry]]:
    """
    Read a sign in sheet excel file and return a dictionnary from name to set of entries
    """
    sign_df = pd.read_excel(file_path, month, header=0)

    sign_in_sheet_data = defaultdict(set)

    for _, row in sign_df.iterrows():
        # Skip rows below the table and LHC rows
        if pd.isna(row[LEVEL_COL]) or row[LEVEL_COL] == "LHC":
            continue

        name = row[NAME_COL].strip()

        for col in sign_df.columns[3:]:
            # Skip empty cells
            if pd.isna(row[col]):
                continue
                
            # Determine which rate to use based on the date and rate change date
            if rate_change_date and rates_after:
                try:
                    if col.date() >= pd.to_datetime(rate_change_date, format="%d/%m/%Y").date():
                        # if it's a house event, then use the house event rate
                        if is_event_sign_in(row[col]):
                            rate = rates_after["House Event"]
                        else:
                            rate = rates_after[row[LEVEL_COL]]
                    else:
                        # if it's a house event, then use the house event rate
                        if is_event_sign_in(row[col]):
                            rate = rates["House Event"]
                        else:
                            rate = rates[row[LEVEL_COL]]
                except ValueError:
                    raise ValueError(f"Rate change date {rate_change_date} is in invalid format. It must be in DD/MM/YYYY format.")
            else:
                # if it's a house event, then use the house event rate
                if is_event_sign_in(row[col]):
                    rate = rates["House Event"]
                else:
                    rate = rates[row[LEVEL_COL]]

            if is_event_sign_in(row[col]):
                # handle house events ('House Event' in the hours cell)
                entry = Entry(
                    date=col.date(),
                    hours=0.0, # does not matter
                    rate=rate,
                    is_event=True
                )
            else:
                # non house event entry
                entry = Entry(
                    date=col.date(),
                    hours=float(row[col]),
                    rate=rate,
                    is_event=False
                )
            sign_in_sheet_data[name].add(entry)

    return sign_in_sheet_data