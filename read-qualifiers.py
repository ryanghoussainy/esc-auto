'''
Read the qualifiers excel sheet and store the data.
'''

import pandas as pd

# Read the data
df = pd.read_excel('HouseChamps/examples/1_doc.xlsx', sheet_name="Dolphins")

# Initialize variables
tables = []  # To store individual tables
current_table = []  # Temporary storage for the current table
headers_found = False

# Iterate through each row
for _, row in df.iterrows():
    # Check if the first column of the second row is "First name"
    if "first" in str(row.iloc[0]).lower() and "name" in str(row.iloc[0]).lower():
        if current_table:
            tables.append(pd.DataFrame(current_table[1:], columns=current_table[0]))
        current_table = [row.to_list()]
        headers_found = True
    elif headers_found and not row.isnull().all():
        current_table.append(row.to_list())
    elif row.isnull().all():
        if current_table:
            tables.append(pd.DataFrame(current_table[1:], columns=current_table[0]))
            current_table = []
            headers_found = False
    

# Add the last table if the sheet doesn't end with a blank row
if current_table:
    tables.append(pd.DataFrame(current_table[1:], columns=current_table[0]))

# Filter out empty tables
tables = [table for table in tables if not table.empty]

# Process or save the tables
for i, table in enumerate(tables):
    print(f"Table {i+1}:")
    print(table)
    print()
