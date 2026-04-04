import re
import pandas as pd
from pypdf import PdfReader


REGEX_EVENT_NAME = r"\b(25|50|100|200)\s*SC\s*Meter\s*(Freestyle|Backstroke|Breaststroke|Butterfly|IM)"

KEYWORDS = ['NT', 'NS', 'DQ']


def get_event_name(row_str) -> str:
    '''
    Extract the event name from the input string.
    e.g. "Event  21   Girls 8 & Under 25 SC Meter Breaststroke" -> "25m Breast"
    '''
    match = re.search(REGEX_EVENT_NAME, row_str, re.IGNORECASE)

    if match:
        distance = match.group(1)
        stroke = match.group(2)

        stroke_map = {
            "Freestyle": "Free",
            "Backstroke": "Back",
            "Breaststroke": "Breast",
            "Butterfly": "Fly",
            "IM": "IM"
        }
        formatted_stroke = stroke_map[stroke]
        return f"{distance}m {formatted_stroke}"
    else:
        raise ValueError(f"Invalid event name: {row_str}")    

def parse_name(name: str) -> tuple[str, str]:
    '''
    Parse the name into first name and surname.
    '''
    names = str(name).split(",")

    if len(names) == 2:
        surname, first_name = names
        
        # Format the names
        first_name = first_name.strip().lower()
        surname = surname.strip().lower()

        return first_name, surname
    else:
        raise ValueError(f"Invalid name: {name}")
    
def get_tokens(line):
    """
    Split a line into tokens, where tokens are separated by spaces or commas.
    """
    # Use regex to split by spaces or commas, but keep the delimiters as tokens
    return re.split(r'(\s+|,)', line)
    
def is_swimmer_line(line):
    """
    Check if a line represents a swimmer entry.
    We can do this by checking if there is a number after "Acton" or "Ealing".
    """
    tokens = get_tokens(line)
    return len(tokens) > 1 and (tokens[0] == "Acton" or tokens[0] == "Ealing") and contains_digit(tokens[2])

def parse_swimmer(line):
    """
    Takes a string of this form "Acton 107 LastNames, FirstName MiddleNameInitials 56.30  NT".
    We skip swimmers from Northolt or St Helens.
    Returns a tuple of (Name, Seed Time, Time).
    The name is in the format "LastNames, FirstName"
    """
    # Split by spaces or commas
    tokens = get_tokens(line)

    # Skip "Acton" or "Ealing"
    if tokens[0] == "Acton" or tokens[0] == "Ealing":
        tokens.pop(0)
    else:
        raise ValueError(f"Line does not start with 'Acton'\n{line}")
    
    # Skip garbage tokens
    while tokens and not re.search(r'[A-Za-z]', tokens[0]):
        tokens.pop(0)
    
    # Extract last names up to the comma delimiter.
    if "," not in tokens:
        raise ValueError("No comma found between last and first names")
    comma_index = tokens.index(",")
    last_names = [token.strip() for token in tokens[:comma_index] if re.search(r'[A-Za-z]', token)]
    if not last_names:
        raise ValueError("No last names found in line")
    tokens = tokens[comma_index + 1:]
    
    # Extract first name (and possibly middle name or initials) until we hit a time or keyword
    first_name = []
    while tokens and not is_time(tokens[0]) and extract_keyword(tokens[0]) is None:
        token = tokens.pop(0).strip()
        if token:
            first_name.append(token)
    
    if not first_name:
        raise ValueError("No first name found in line")
    
    # Join last names and first name
    name = f"{' '.join(last_names)}, {' '.join(first_name)}"

    # Now we should have a time or keyword left
    if not tokens:
        raise ValueError("No time or keyword found in line")
    
    # Remove garbage tokens
    while tokens and not is_time(tokens[0]) and extract_keyword(tokens[0]) is None:
        tokens.pop(0)
    
    # Extract the achieved time
    if not tokens:
        raise ValueError("Expected a time or keyword after name")
    achieved_time = tokens.pop(0).strip()
    
    # Remove garbage tokens
    while tokens and not is_time(tokens[0]) and extract_keyword(tokens[0]) is None:
        tokens.pop(0)

    seed_time = tokens.pop(0).strip() if tokens else None

    return name, seed_time, achieved_time

def contains_digit(x):
    return any(c.isdigit() for c in x)

def is_time(s):
    """
    Times are stored in 'xx:xx.xx' or 'xx.xx' format
    """
    return re.match(r'^\d{1,2}[:.]\d{2}([:.]\d{2})?$', s) is not None or re.match(r'^\d{1,2}[:.]\d{2}$', s) is not None

def extract_keyword(x):
    for kw in KEYWORDS:
        if kw in x:
            return kw
    return None

def read_pdf(pdf_path, isQualifiers: bool):
    """
    Read a PDF file (either heat results of full results) and return the list of pdf tables.
    - For heat results (qualifiers), this will return all of the tables.
    - For finals, this will return only the finals tables (since there are also prelim tables which are not necessary).
      The finals tables contain both the prelim time and the finals time.
    """
    # Define column name for times in resulting DataFrame
    if isQualifiers:
        prev_time = "Seed Time"
        cur_time = "Time"
    else:
        prev_time = "Qualifiers Time"
        cur_time = "Finals Time"

    # Read the results PDF
    # Read the qualifiers results PDF
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
                if is_swimmer_line(lines[idx]):
                    name, seed_time, time = parse_swimmer(lines[idx])
                    swimmers.append({
                        "Name": name,
                        prev_time: seed_time, # Here we take the seed time as the qualifier time
                        cur_time: time # This is the finals time
                    })
                idx += 1
            # If any swimmers were found, make a DataFrame
            if swimmers:
                df = pd.DataFrame(swimmers)
                pdf_tables.append(df)
        else:
            idx += 1
    
    if isQualifiers:
        return pdf_tables
    else:
        # Only keep even tables (index-wise) because odd ones are qualifiers
        return pdf_tables[::2]
