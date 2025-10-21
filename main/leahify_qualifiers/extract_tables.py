'''
Read the qualifiers excel sheet and store the data.
'''

import pandas as pd
import re
from reusables import is_final

REGEX_AGE_RANGE_SAMMY = r"\b\d{1,2}\s*&\s*(Under|Over|under|over)|\b\d{1,2}\s*(-|/)\s*\d{1,2}"


def extract_tables(
        file: str,
        sheet_name: str,
        header_identifiers: list[(str, int)],
        get_events: bool = False,
        is_leah: bool = False,
) -> tuple[list[pd.DataFrame], list[str], dict[str, (int, int, str)]]:
    '''
    Extracts all tables from the given excel sheet.
    Each table must have a row where the first cell contains "first" and "name".
    This is how we identify the start of a new table.
    The end of a table is identified by an empty row.
    '''

    def is_header(row: pd.Series) -> bool:
        '''
        Returns true if and only if the row is a header.
        '''
        for identifier, col in header_identifiers:
            cell = str(row.iloc[col]).lower()
            if identifier.lower() in cell:
                return True
        return False
    
    # Read the excel file
    df = pd.read_excel(file, sheet_name=sheet_name or 0, header=None)

    tables: list[pd.DataFrame] = []  # To store individual tables
    current_table = []  # Temporary storage for the current table
    events = []  # To store the event names

    swimmer_info = {} # To store swimmer info (age from, age to, gender)

    headers_found = False

    # Iterate through each row
    for idx, row in df.iterrows():
        # If we are looking for events and the line contains "Event", then extract the event names
        first_cell_str = str(row.iloc[0])
        if get_events and first_cell_str.startswith("Event"):
            events.append(first_cell_str)

            # If we have found the headers, then add the row to the current table.
            if current_table:
                tables.append(pd.DataFrame(current_table[1:], columns=current_table[0]))
            current_table = [row.to_list()]
            headers_found = False
        # If the row is a header, then put it at the start of the current table.
        elif is_header(row):
            current_table.insert(0, row.to_list())
            headers_found = True

            if idx > 0:
                # Look at the row above to extract the gender
                cell = df.iloc[idx - 1][0]
                if "boys" in str(cell).lower():
                    current_gender = "boys"
                elif "girls" in str(cell).lower():
                    current_gender = "girls"
                else:
                    raise ValueError(f"Could not extract gender \"boys\" or \"girls\": {cell}")
                
                # Extract the age range from the row above
                age_range = re.search(REGEX_AGE_RANGE_SAMMY, cell)
                if age_range:
                    age_range = age_range.group(0)
                    if "under" in age_range.lower():
                        current_age_from = 0
                        current_age_to = int(age_range.split("&")[0].strip())
                    elif "over" in age_range.lower():
                        current_age_from = int(age_range.split("&")[0].strip())
                        current_age_to = 99
                    else:
                        if "-" in age_range:
                            current_age_from, current_age_to = map(int, age_range.split("-"))
                        elif "/" in age_range:
                            current_age_from, current_age_to = map(int, age_range.split("/"))
                        else:
                            raise ValueError(f"Could not extract age range. Did not find - or /: {cell}")
                # Finals don't have age ranges
                elif is_final(cell):
                    current_age_from = 0
                    current_age_to = 99
                else:
                    raise ValueError(f"Could not extract age range: {cell}")
                
        # If we have found the headers, then add the swimmer row to the current table.
        elif headers_found and not row.isnull().all():
            # Do not add Northolt swimmers for Leah's tables
            if is_leah and str(row[3]) in ["Northolt", "St Helens"]:
                continue

            current_table.append(row.to_list())
            # Also add it to the swimmer info
            first_name, surname = row[0], row[1]
            swimmer_info[(first_name, surname)] = (current_age_from, current_age_to, current_gender)

        # If the row is empty, then we have reached the end of the table.
        elif row.isnull().all() and current_table:
            tables.append(pd.DataFrame(current_table[1:], columns=current_table[0]))
            current_table = []
            headers_found = False
        

    # Save the last table
    if current_table:
        tables.append(pd.DataFrame(current_table[1:], columns=current_table[0]))

    # Filter out empty tables
    tables = [table for table in tables if not table.empty]

    return tables, events, swimmer_info


def concat_tables(tables: list[pd.DataFrame]) -> pd.DataFrame:
    '''
    Concatenate all tables into a single table.
    '''
    return pd.concat(tables, ignore_index=True)


def print_first_rows(table: pd.DataFrame, n: int):
    '''
    Pretty print the first n rows of the table.
    '''
    pd.set_option('display.max_columns', None)
    print(table.head(n))
    pd.reset_option('display.max_columns')

def print_tables(tables: list[pd.DataFrame]):
    '''
    Pretty print the tables.
    '''
    for i in range(len(tables)):
        print(f"Table {i + 1}")
        print(tables[i])
        print()
