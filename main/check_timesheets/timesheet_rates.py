"""
Reading the rate table out of a timesheet.

The timesheet template has changed over time, so there is one reader per template and
`read_rates` picks the right one from the rate table's title:

  - legacy template ("exclusive of holiday pay"): one rate per level for the whole
    timesheet, worked out as last year's rate * the percentage increase above the table.
  - current template ("before holiday pay"): the new and previous year's rates are both
    listed, and the date the rates changed is written in the "TOTALS FOR PRE <MONTH YEAR>"
    label, so entries before that date use the previous rates.
"""
import re
from datetime import date, datetime

import pandas as pd

LEGACY_RATE_TABLE_HEADER = "Standard rates of pay (exclusive of holiday pay)"
CURRENT_RATE_TABLE_HEADER = "Standard rates of pay (before holiday pay)"

RATE_INCREASE_COL_IDX = 6
ADMIN_RATE_INCREASE = 1.05
EVENTS_LEVELS_COL = 9
LEGACY_LEVELS_COL = 4
FIRST_LEVEL = "Lifeguard"
CHANGE_DATE_LABEL = re.compile(r"\bpre\s+([A-Za-z]+)\s+(\d{4})\b", re.IGNORECASE)


class TimesheetRates:
    """The rate for each level, which may change on `change_date` (entries on or after it use `rates_from`)."""

    def __init__(self, rates_before: dict[str, float], rates_from: dict[str, float] | None = None, change_date: date | None = None):
        self.rates_before = rates_before
        self.rates_from = rates_from if rates_from is not None else rates_before
        self.change_date = change_date

    def table_for(self, on: date) -> dict[str, float]:
        if self.change_date is not None and on >= self.change_date:
            return self.rates_from
        return self.rates_before

    def levels(self) -> list[str]:
        return sorted(set(self.rates_before) | set(self.rates_from))

    def rate_for(self, level: str, on: date) -> float | None:
        return self.table_for(on).get(level)


def read_rates(df: pd.DataFrame, who: str) -> TimesheetRates:
    """Read the rates from a timesheet dataframe, using whichever template it was made from."""
    legacy_row = _find_row(df, LEGACY_RATE_TABLE_HEADER)
    if legacy_row is not None:
        return _read_legacy_rates(df, legacy_row, who)

    current_row = _find_row(df, CURRENT_RATE_TABLE_HEADER)
    if current_row is not None:
        return _read_current_rates(df, current_row, who)

    raise ValueError(
        f"{who}: could not find the rate table header "
        f"('{CURRENT_RATE_TABLE_HEADER}'). Is this the current timesheet template?"
    )


def _find_row(df: pd.DataFrame, header: str) -> int | None:
    for idx, row in df.iterrows():
        for value in row.values:
            if isinstance(value, str) and value.strip() == header:
                return idx
    return None


# ---------------------------------------------------------------- legacy template

def _read_legacy_rates(df, header_row, who) -> TimesheetRates:
    raw_rate_increase = df.iloc[header_row - 1, RATE_INCREASE_COL_IDX]
    if not pd.api.types.is_number(raw_rate_increase) or pd.isna(raw_rate_increase):
        raise ValueError(f"{who}: the rate increase cell above the rate table is not a number (found {raw_rate_increase!r})")
    rate_increase = 1 + raw_rate_increase

    level_to_rate = {}
    read_rates_table(df, start_row=header_row + 1, levels_col=LEGACY_LEVELS_COL, is_events_table=False, level_to_rate=level_to_rate)
    _apply_legacy_increase(level_to_rate, rate_increase)
    read_rates_table(df, start_row=header_row + 1, levels_col=EVENTS_LEVELS_COL, is_events_table=True, level_to_rate=level_to_rate)
    return TimesheetRates(level_to_rate)


def _apply_legacy_increase(level_to_rate, rate_increase):
    for lvl in level_to_rate:
        if lvl in ("admin", "training"):
            level_to_rate[lvl] = round(level_to_rate[lvl] * ADMIN_RATE_INCREASE, 2)
        elif lvl != "other":
            level_to_rate[lvl] = round(level_to_rate[lvl] * rate_increase, 2)


# ---------------------------------------------------------------- current template

def _read_current_rates(df, header_row, who) -> TimesheetRates:
    levels_col = _find_levels_col(df, header_row, who)
    new_col, previous_col = levels_col + 1, levels_col + 2

    new_rates, previous_rates = {}, {}
    row = header_row + 1
    while row < len(df):
        level = df.iloc[row, levels_col]
        if pd.isna(level) or not str(level).strip():
            break
        key = str(level).strip().lower()
        # "Other" has no standard rate
        if key != "other":
            new_rates[key] = _read_rate(df.iloc[row, new_col], level, who)
            previous_rates[key] = _read_rate(df.iloc[row, previous_col], level, who)
        row += 1

    # Gala / house event rates are the same before and after
    event_rates = {}
    read_rates_table(df, start_row=header_row + 1, levels_col=EVENTS_LEVELS_COL, is_events_table=True, level_to_rate=event_rates)
    new_rates.update(event_rates)
    previous_rates.update(event_rates)

    return TimesheetRates(previous_rates, new_rates, _read_change_date(df, who))


def _find_levels_col(df, header_row, who) -> int:
    """The levels column is the one holding "Lifeguard", the first level, just under the header."""
    for col in range(df.shape[1]):
        value = df.iloc[header_row + 1, col] if header_row + 1 < len(df) else None
        if isinstance(value, str) and value.strip() == FIRST_LEVEL:
            return col
    raise ValueError(f"{who}: could not find the '{FIRST_LEVEL}' level just under the rate table header")


def _read_rate(value, level, who) -> float:
    if not pd.api.types.is_number(value) or pd.isna(value):
        raise ValueError(f"{who}: the rate for '{level}' in the rate table is not a number (found {value!r})")
    return round(float(value), 2)


def _read_change_date(df, who) -> date:
    """The date the rates changed, from a label like "TOTALS FOR PRE OCTOBER 2026" (meaning rates change on 1 October 2026)."""
    for value in df.values.flatten():
        if not isinstance(value, str):
            continue
        match = CHANGE_DATE_LABEL.search(value)
        if match:
            try:
                return datetime.strptime(f"{match.group(1)} {match.group(2)}", "%B %Y").date()
            except ValueError:
                continue
    raise ValueError(f"{who}: could not find the rate change date (a label like 'TOTALS FOR PRE OCTOBER 2026')")


# ---------------------------------------------------------------- shared

def read_rates_table(df, start_row, levels_col, is_events_table, level_to_rate):
    """Read rates table (normal or events) and populate level_to_rate dictionary. Used by the legacy template and for events."""
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
