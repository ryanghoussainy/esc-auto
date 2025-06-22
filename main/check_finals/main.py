import pandas as pd
from reusables import print_discrepancies, TIME_DISCREPANCY, SWIMMER_NOT_FOUND_DISCREPANCY
from reusables import match_swimmer, parse_name, normalise_time, read_pdf

def get_finals_tables(finals_file):
    """
    Read the finals excel file and return the tables.
    """
    # Load the Excel file
    df = pd.read_excel(finals_file, sheet_name="Finals", header=None)
    # Prepare to hold each table
    tables = []
    # Find rows where any cell starts with "Event"
    event_indices = df.apply(lambda row: row.astype(str).str.startswith("Event").any(), axis=1)
    event_starts = df[event_indices].index.tolist()
    # Add artificial end index to help slice the blocks
    event_starts.append(len(df))
    # Split the DataFrame into a list of tables based on event starts
    tables = []
    for i in range(len(event_starts) - 1):
        start_idx = event_starts[i]
        end_idx = event_starts[i + 1]
        block = df.iloc[start_idx:end_idx].reset_index(drop=True)
        header_row = block.iloc[1] # Skip the first row which is the event name
        data = block[2:]
        data.columns = header_row
        data = data.dropna(how='all')  # Remove fully empty rows
        # Remove first row
        data = data.reset_index(drop=True)
        tables.append(data.reset_index(drop=True))
    return tables

def get_event_name_from_finals(finals_table):
    """
    Extract event name from finals table.
    The event name is in the first row, first column in format like "Event 1 25m back 2016 & under girls (8 & under)"
    """
    # We get the index 7 column because that header is just the event name in the finals excel
    return str(finals_table.columns[7])

def check_finals(finals_file, pdf_file):
    """
    Check the finals results against the full results PDF.
    """
    # Read the finals results from the Excel file
    # We have 45 tables, each with shape (7 rows, 9 columns)
    finals_tables = get_finals_tables(finals_file)
   
    # Read pdf
    pdf_tables = read_pdf(pdf_file, isQualifiers=False)
    
    # Compare finals table and pdf data and alert user of any differences
    
    # List to hold any discrepancies found
    # This is a list of (type of mismatch (int/enum), swimmer name, event name, pdf time, finals time)
    discrepancies = []
    
    # Define automatic and manual matches
    manual_matches = {}
    automatic_matches = {}
    
    for tableIdx in range(len(finals_tables)):
        # Get event name from finals table
        event_name = get_event_name_from_finals(finals_tables[tableIdx])
        
        # Get the finals table
        finals_df = pd.DataFrame(finals_tables[tableIdx])
        
        # Remove rows where both First name and Surname are NaN
        finals_df = finals_df.dropna(subset=["First name", "Surname"])

        # Get pdf table
        pdf_table = pdf_tables[tableIdx]
        
        # Swimmers in finals table are in Sammy's format.
        # So we need to manually match those that don't match automatically
        for _, pdf_row in pdf_table.iterrows():
            # Get swimmer name and times from PDF table
            pdf_name = pdf_row["Name"]
            pdf_qualifier_time = pdf_row["Qualifiers Time"]
            pdf_finals_time = pdf_row["Finals Time"]

            # Extract swimmer's first name and surname from PDF name
            pdf_first_names, pdf_surname = parse_name(pdf_name)
            pdf_first_name = pdf_first_names.split()[0]

            # Find the swimmer in the finals table
            swimmer = match_swimmer(
                pdf_first_name, # In Leah's format
                pdf_surname, # In Leah's format
                finals_df, # In Sammy's format
                automatic_matches,
                manual_matches,
            )

            if len(swimmer) > 0:
                # Get full name
                full_name = f"{swimmer['First name'].iloc[0]} {swimmer['Surname'].iloc[0]}"

                # Compare qualifier times
                finals_qualifier_time = swimmer[f"Qualifier {event_name}"].iloc[0]

                # If we have NS in the PDF and DNS in the finals, we consider it a match
                if pdf_qualifier_time == "NS" and finals_qualifier_time == "DNS":
                    continue
                
                # Normalise times for comparison
                finals_qualifier_time_normalised = normalise_time(finals_qualifier_time)
                pdf_qualifier_time_normalised = normalise_time(pdf_qualifier_time)
                
                if pdf_qualifier_time_normalised != finals_qualifier_time_normalised:
                    discrepancies.append((TIME_DISCREPANCY, full_name, event_name, pdf_qualifier_time, finals_qualifier_time))
                
                # Compare finals times
                finals_finals_time = swimmer.iloc[0][event_name]

                # If we have NS in the PDF and DNS in the finals, we consider it a match
                if pdf_finals_time == "NS" and finals_finals_time == "DNS":
                    continue

                # Normalise finals times for comparison
                finals_finals_time_normalised = normalise_time(finals_finals_time)
                pdf_finals_time_normalised = normalise_time(pdf_finals_time)

                if pdf_finals_time_normalised != finals_finals_time_normalised:
                    discrepancies.append((TIME_DISCREPANCY, full_name, event_name, pdf_finals_time, finals_finals_time))
                
                # SUCCESSFUL MATCH
            else:
                # If no swimmer was found, we have a discrepancy
                # We don't have the swimmer's name in Sammy's format so we use the pdf name.
                discrepancies.append((SWIMMER_NOT_FOUND_DISCREPANCY, pdf_name, event_name, pdf_finals_time, ""))

    # Print discrepancies
    print_discrepancies(discrepancies, isQualifiers=False)
