from pypdf import PdfReader
import pandas as pd
from leahify_qualifiers import get_leah_tables, match_swimmer, get_event_name, parse_name
from leahify_qualifiers import print_colour, YELLOW, RED, GREEN
import re


KEYWORDS = ['NT', 'NS', 'DQ']

TIME_DISCREPANCY = 0
SEED_TIME_DISCREPANCY = 1
SWIMMER_NOT_FOUND_DISCREPANCY = 2


# Check for dots because times are stored in 'xx:xx.xx' or 'xx.xx' format
def is_time(s):
    return re.match(r'^\d{1,2}[:.]\d{2}([:.]\d{2})?$', s) is not None or re.match(r'^\d{1,2}[:.]\d{2}$', s) is not None

def normalise_time(t):
    return str(t).replace(':', '.').replace(',', '.')


def contains_digit(x):
    return any(c.isdigit() for c in x)


def extract_keyword(x):
    for kw in KEYWORDS:
        if kw in x:
            return kw
    return None

def parse_swimmer(line):
    """
    Takes a string of this form "Esc 107 LastNames, FirstName MiddleNameInitials 56.30  NT".
    Returns a tuple of (Name, Seed Time, Time).
    The name is in the format "LastNames, FirstName"
    """
    # Split by spaces or commas
    tokens = re.split(r' |,', line.strip())
    
    # Skip "Esc"
    if tokens[0] == "Esc":
        tokens.pop(0)
    else:
        raise ValueError("Line does not start with 'Esc'")
    
    # Skip all ' ' tokens and numbers until we hit a name
    while tokens and (tokens[0] == '' or contains_digit(tokens[0])):
        tokens.pop(0)
    
    # Extract last names until we hit ' ' token (meaning we hit the comma)
    last_names = []
    while tokens and tokens[0] != '':
        last_names.append(tokens.pop(0))
    
    if not last_names:
        raise ValueError("No last names found in line")
    
    # Extract first name (and possibly middle name or initials) until we hit a time or keyword
    first_name = []
    while tokens and not is_time(tokens[0]) and extract_keyword(tokens[0]) is None:
        first_name.append(tokens.pop(0))
    
    if not first_name:
        raise ValueError("No first name found in line")
    
    # Join last names and first name
    name = f"{' '.join(last_names)},{' '.join(first_name)}"

    # Now we should have a time or keyword left
    if not tokens:
        raise ValueError("No time or keyword found in line")
    
    # Extract the achieved time
    if not tokens or (not is_time(tokens[0]) and extract_keyword(tokens[0]) is None):
        raise ValueError("Expected a time or keyword after seed time")
    achieved_time = tokens.pop(0)
    
    # Skip space if it exists
    if tokens and tokens[0] == '':
        tokens.pop(0)

    # Extract the seed time
    if not tokens or (not is_time(tokens[0]) and extract_keyword(tokens[0]) is None):
        raise ValueError("Expected a time or keyword after name")
    seed_time = tokens.pop(0)

    return name, seed_time, achieved_time

def clean_name(name):
    """
    Removes dashes at the end of the swimmer's name.
    """
    return name.replace(" -", "").strip()


def check_qualifiers(output_table_path, pdf_path):
    # print(parse_swimmer("Esc  826 Blacker, Beatrix F 4:20.75  NT"))
    # Extract the tables using the get_leah_tables function
    # EXTRA rows will just be added at the end of each event table, so we can re-use the same function
    leah_tables, _, _ = get_leah_tables(output_table_path, None)

    # Put it in the right format
    # Remove rows where Name is NaN
    # print(leah_tables[1][["Name", "Seed Time", "Time"]].dropna(subset=["Name"]))

    # Read the qualifiers results PDF

    # Compare output table and pdf data and alert user of any differences

    reader = PdfReader(pdf_path)
    
    # Extract text from each page and split into lines
    lines = []
    for page in reader.pages:
        text = page.extract_text() or ""
        lines += text.split('\n')

    pdf_tables = []  # This will hold a DataFrame per event
    idx = 0

    while idx < len(lines):
        if lines[idx].strip().startswith("Event"):
            idx += 2
            
            # Skip event details
            if idx < len(lines) and "Prelim" in lines[idx]:
                idx += 1
            
            # Collect swimmer data for this event
            swimmers = []
            while idx < len(lines) and not lines[idx].strip().startswith("Event"):
                if lines[idx].strip().startswith("Esc"):
                    name, seed_time, time = parse_swimmer(lines[idx])
                    swimmers.append({
                        "Name": name,
                        "Seed Time": seed_time,
                        "Time": time
                    })
                idx += 1

            # If any swimmers were found, make a DataFrame
            if swimmers:
                df = pd.DataFrame(swimmers)
                pdf_tables.append(df)
        else:
            idx += 1

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
        # Extra rows are those that are below the EXTRA header
        leah_normal_rows = []
        for _, row in leah_tables[tableIdx].iterrows():
            if row['Lane'] == 'EXTRA':
                break
            leah_normal_rows.append(row)

        # Add the rest of the rows as extra rows. (+1 to skip the 'EXTRA' header row)
        leah_extra_rows = leah_tables[tableIdx].iloc[len(leah_normal_rows) + 1:].reset_index(drop=True)
        leah_normal_df = pd.DataFrame(leah_normal_rows)
        leah_normal_df = leah_normal_df.dropna(subset=["Name", "Seed Time", "Time"])
        
        # For normal rows, match swimmer names and times directly
        for _, row in leah_normal_df.iterrows():
            name = clean_name(row['Name']) # Remove garbage pdf-read dashes
            seed_time = row['Seed Time']
            time = row['Time']

            # Match only with the corresponding event table
            pdf_table = pdf_tables[tableIdx]

            if name in pdf_table['Name'].values:
                matched_pdf_row = pdf_table[pdf_table['Name'] == name]
                if not matched_pdf_row.empty:
                    # If we have NS in PDF and DNS in Leah, we consider them equal
                    if matched_pdf_row['Time'].values[0] == "NS" and row['Time'] == "DNS":
                        pdf_table.drop(matched_pdf_row.index, inplace=True)
                        continue
                    
                    # If we have DQ with explanation, we consider them equal
                    if "DQ" in matched_pdf_row['Time'].values[0] and "DQ" in row['Time']:
                        pdf_table.drop(matched_pdf_row.index, inplace=True)
                        continue

                    # Compare times
                    pdf_time = normalise_time(matched_pdf_row['Time'].values[0])
                    leah_time = normalise_time(time)

                    if pdf_time != leah_time:
                        discrepancies.append((TIME_DISCREPANCY, name, event_name, matched_pdf_row['Time'].values[0], time))

                    # Compare seed times
                    pdf_seed = normalise_time(matched_pdf_row['Seed Time'].values[0])
                    leah_seed = normalise_time(seed_time)
                    if pdf_seed != leah_seed:
                        discrepancies.append((SEED_TIME_DISCREPANCY, name, event_name, matched_pdf_row['Seed Time'].values[0], seed_time))

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
            # We only match name and time (not seed time, since Sammy's format doesn't have it)
            pdf_name = pdf_row['Name']
            pdf_time = pdf_row['Time']

            # Extract the swimmer's first name and surname from the PDF name
            pdf_first_names, pdf_surname = parse_name(pdf_name)
            pdf_first_name = pdf_first_names.split()[0]

            # Find the swimmer in Leah's extra rows
            swimmer = match_swimmer(
                pdf_first_name,
                pdf_surname,
                leah_extra_rows,
                automatic_matches,
                manual_matches,
                sfirst_name_col="Lane",
                ssurname_col="Name",
            )

            if swimmer is not None:
                # If we found a swimmer, check if the times match
                leah_time = swimmer['Time'].iloc[0]

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
                    discrepancies.append((TIME_DISCREPANCY, swimmer['Name'].iloc[0], event_name, pdf_time, leah_time))
                
                # SUCCESSFUL MATCH
                # Remove matched row from pdf table
                pdf_table.drop(pdf_row.name, inplace=True)
            else:
                # If we didn't find a swimmer, we have a mismatch
                # We don't know the name of the swimmer, so we just use the PDF name
                discrepancies.append((SWIMMER_NOT_FOUND_DISCREPANCY, pdf_row['Name'], event_name, pdf_time, ""))
        # If there are any swimmers left in the pdf table, they are extra rows
        # We can just add them to the leah_extra_rows DataFrame
        if not pdf_table.empty:
            raise Exception(f"Some swimmers were not matched in the PDF table for event {event_name}. This is likely due to a mismatch in the swimmer's name or time. Please check the PDF results and the Leah output table.")

    # Print discrepancies
    if discrepancies:
        
        print("Finished checking qualifiers. Mismatches found:")
        for d in discrepancies:
            print("- ", end='')
            # Print type of mismatch in red
            if d[0] == TIME_DISCREPANCY:
                print_colour(RED, "Time mismatch ", end='')
                print("for ", end='')
                print_colour(YELLOW, d[1], end=' - ')
                print(f"Event: {d[2]}, ", end='')
                print(f"PDF: {d[3]}, LEAH: {d[4]}")
            elif d[0] == SEED_TIME_DISCREPANCY:
                print_colour(RED, "Seed time mismatch ", end='')
                print("for ", end='')
                print_colour(YELLOW, d[1], end=' - ')
                print(f"Event: {d[2]}, ", end='')
                print(f"PDF: {d[3]}, LEAH: {d[4]}")
            elif d[0] == SWIMMER_NOT_FOUND_DISCREPANCY:
                print_colour(RED, f"Swimmer {d[1]} not found in PDF")
    else:
        print_colour(GREEN, "Finished checking qualifiers. No mismatches found.")
