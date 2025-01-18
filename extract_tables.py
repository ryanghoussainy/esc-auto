'''
Read the qualifiers excel sheet and store the data.
'''

import pandas as pd


def extract_tables(file: str, sheet_name: str, header_identifiers: list[(str, int)]) -> list[pd.DataFrame]:
    '''
    Extracts all tables from the given excel sheet.
    Each table must have a row where the first cell contains "first" and "name".
    This is how we identify the start of a new table.
    The end of a table is identified by an empty row.
    '''

    def is_header(row: str) -> bool:
        '''
        Returns true if and only if the row is a header.
        '''
        for identifier, col in header_identifiers:
            cell = str(row.iloc[col]).lower()
            if identifier.lower() in cell:
                return True
        return False
    
    # Read the excel file
    df = pd.read_excel(file, sheet_name=sheet_name or 0)

    tables = []  # To store individual tables
    current_table = []  # Temporary storage for the current table
    headers_found = False

    # Iterate through each row
    for _, row in df.iterrows():
        # If the row is a header, then start a new table.
        if is_header(row):
            # If we have already started a previous table, then save it to the list of tables.
            if current_table:
                tables.append(pd.DataFrame(current_table[1:], columns=current_table[0]))

            # Start a new table
            current_table = [row.to_list()]
            headers_found = True
        # If we have found the headers, then add the row to the current table.
        elif headers_found and not row.isnull().all():
            current_table.append(row.to_list())
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

    return tables


def print_tables(tables: list[pd.DataFrame]):
    '''
    Pretty print the tables.
    '''
    for i in range(len(tables)):
        print(f"Table {i + 1}")
        print(tables[i])
        print()
