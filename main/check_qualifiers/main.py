import pandas as pd
from leahify_qualifiers import get_leah_tables, TIME_COLUMN_INDEX
from reusables import print_discrepancies, TIME_DISCREPANCY, SWIMMER_NOT_FOUND_DISCREPANCY
from reusables import match_swimmer, get_event_name, parse_name, normalise_time, read_pdf


def clean_name(name):
    """
    Removes dashes at the end of the swimmer's name.
    """
    return name.replace(" -", "").strip()

def split_extra_rows(leah_table):
    # Extra rows are those that are below the EXTRA header
    leah_normal_rows = []
    for _, row in leah_table.iterrows():
        if row['Lane'].lower() == 'extra':
            break
        leah_normal_rows.append(row)

    # Add the rest of the rows as extra rows. (+1 to skip the 'EXTRA' header row)
    leah_extra_df = leah_table.iloc[len(leah_normal_rows) + 1:].reset_index(drop=True)
    leah_normal_df = pd.DataFrame(leah_normal_rows)
    leah_normal_df = leah_normal_df.dropna(subset=["Name"])

    return leah_normal_df, leah_extra_df


def check_qualifiers(output_table_path, pdf_path, user_input_callback=None):
    """
    Check the qualifiers excel sheet against the heat results PDF.
    """
    # Extract the tables using the get_leah_tables function
    # EXTRA rows will just be added at the end of each event table, so we can re-use the same function
    leah_tables, _, _ = get_leah_tables(output_table_path, None)

    # Get time column name
    time_column_name = leah_tables[0].columns[TIME_COLUMN_INDEX]

    # Read the PDF file
    pdf_tables = read_pdf(pdf_path, isQualifiers=True)

    # Compare output table and pdf data and alert user of any differences

    # List to hold any discrepancies found
    # This is a list of (type of mismatch (int/enum), swimmer name, pdf time, leah time)
    discrepancies = []

    # Define automatic and manual matches
    manual_matches = {}
    automatic_matches = {}

    for tableIdx in range(len(leah_tables)):
        # Get event name
        event_name = get_event_name(leah_tables[tableIdx].iloc[0]['Lane'])

        # Split table into normal and extra rows
        leah_normal_df, leah_extra_df = split_extra_rows(leah_tables[tableIdx])
        
        # For normal rows, match swimmer names and times directly
        for _, row in leah_normal_df.iterrows():
            name = clean_name(row['Name']) # Remove garbage pdf-read dashes
            time = row[time_column_name]

            # Match only with the corresponding event table
            pdf_table = pdf_tables[tableIdx]

            clean_pdf_names = [clean_name(n) for n in pdf_table['Name'].values]

            if name in clean_pdf_names:
                matched_pdf_row = pdf_table[pdf_table['Name'].apply(clean_name) == name]
                if not matched_pdf_row.empty:
                    # If we have NS in PDF and DNS in Leah, we consider them equal
                    if matched_pdf_row['Time'].values[0] == "NS" and row[time_column_name] == "DNS":
                        pdf_table.drop(matched_pdf_row.index, inplace=True)
                        continue
                    
                    # If we have DQ with explanation, we consider them equal
                    if "DQ" in matched_pdf_row['Time'].values[0] and "DQ" in row[time_column_name]:
                        pdf_table.drop(matched_pdf_row.index, inplace=True)
                        continue

                    # Compare times
                    pdf_time_normalised = normalise_time(matched_pdf_row['Time'].values[0])
                    leah_time_normalised = normalise_time(time)

                    if pdf_time_normalised != leah_time_normalised:
                        discrepancies.append((TIME_DISCREPANCY, name, event_name, matched_pdf_row['Time'].values[0], time))

                    # SUCCESSFUL MATCH
                    # Remove matched row from pdf table
                    pdf_table.drop(matched_pdf_row.index, inplace=True)

                # If the swimmer is not found in the PDF results
                else:
                    discrepancies.append((SWIMMER_NOT_FOUND_DISCREPANCY, name, event_name, "", "")) 
            else:
                discrepancies.append((SWIMMER_NOT_FOUND_DISCREPANCY, name, event_name, "", ""))

        # Reset indexes of the table
        pdf_table.reset_index(drop=True, inplace=True)

        # For this bit, it's a bit weird because Leah's extra rows are stored in
        # Sammy's format, and the pdf tables are in Leah's format.
        # So we use the match_swimmer function but "flip" the arguments.
        # For each row left in the pdf table (extra rows), we try to match it with a swimmer in Leah's extra rows.
        for _, pdf_row in pdf_table.iterrows():
            # Match name and time
            pdf_name = pdf_row['Name']
            pdf_time = pdf_row['Time']

            # Extract the swimmer's first name and surname from the PDF name
            pdf_first_names, pdf_surname = parse_name(pdf_name)
            pdf_first_name = pdf_first_names.split()[0]

            # Find the swimmer in Leah's extra rows
            # Why are the arguments flipped? See comment above
            swimmer = match_swimmer(
                pdf_first_name,
                pdf_surname,
                leah_extra_df,
                automatic_matches,
                manual_matches,
                sfirst_name_col="Lane",
                ssurname_col="Name",
                user_input_callback=user_input_callback,
            )

            if len(swimmer) > 0:
                # Get full name
                full_name = f"{swimmer['Lane'].iloc[0]} {swimmer['Name'].iloc[0]}"
                
                # If we found a swimmer, check if the times match
                leah_time = swimmer[time_column_name].iloc[0]

                # If we have NS in PDF and DNS in Leah, we consider them equal
                if pdf_time == "NS" and leah_time == "DNS":
                    pdf_table.drop(pdf_row.name, inplace=True)
                    continue
                
                # If we have DQ with explanation, we consider them equal
                if "DQ" in pdf_time and "DQ" in leah_time:
                    pdf_table.drop(pdf_row.name, inplace=True)
                    continue

                # Compare times
                pdf_time_normalised = normalise_time(pdf_time)
                leah_time_normalised = normalise_time(leah_time)
                if pdf_time_normalised != leah_time_normalised:
                    discrepancies.append((TIME_DISCREPANCY, full_name, event_name, pdf_time, leah_time))
                
                # SUCCESSFUL MATCH
                # Remove matched row from pdf table
                pdf_table.drop(pdf_row.name, inplace=True)
            else:
                # If we didn't find a swimmer, we have a mismatch
                # We don't know the name of the swimmer, so we just use the PDF name
                discrepancies.append((SWIMMER_NOT_FOUND_DISCREPANCY, pdf_name, event_name, pdf_time, ""))
        # If there are any swimmers left in the pdf table, they are extra rows
        # We can just add them to the leah_extra_rows DataFrame
        if not pdf_table.empty:
            raise Exception(f"Some swimmers were not matched in the PDF table for event {event_name}. This is likely due to a mismatch in the swimmer's name or time. Please check the PDF results and the Leah output table.")

    # Print discrepancies
    print_discrepancies(discrepancies, isQualifiers=True)
