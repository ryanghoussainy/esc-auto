from pypdf import PdfReader


KEYWORDS = ['NT', 'NS', 'DQ']

# Check for dots because times are stored in 'xx:xx.xx' or 'xx.xx' format
def is_time(s):
    return '.' in s


def contains_digit(x):
    for c in x:
        if c.isdigit():
            return True
    return False


def extract_keyword(x):
    for kw in KEYWORDS:
        if kw in x:
            return kw
    return None


def parse_swimmer(_line):
    def loop(line, first_name, last_name, prev_time, time):
        match line:
            # No more tokens
            case []:
                # Error: we could not extract at least one of: first name, last name, previous time, current time
                if not first_name or not last_name or not prev_time or not time:
                    print(_line.split(' '), first_name, last_name, prev_time, time)
                    raise Exception("Could not parse swimmer times. It is possible that the pdf format may have changed. Error code: 1")
                return first_name, last_name, prev_time, time
            
            # Skip empty lines or lines with just 'Esc'
            case [token, *rest] if token in ('Esc', ''):
                return loop(rest, first_name, last_name, prev_time, time)
            
            case [token, *rest]:
                # Ignore numbers that are before the last name
                if not last_name and contains_digit(token):
                    return loop(rest, first_name, last_name, prev_time, time)
                
                kw = extract_keyword(token)
                if is_time(token) or kw:
                    # Normalise keyword token ('DQ', 'NS', 'NT', ...)
                    if kw is not None:
                        token = kw

                    # It's only a time if we have already parsed the first name and last name
                    if first_name and last_name:
                        # Is 'x' the previous time or achieved time?
                        if time:
                            return first_name, last_name, token, time
                        else:
                            return loop(rest, first_name, last_name, prev_time, token)
                    else:
                        print(line)
                        raise Exception("Could not parse swimmer times. It is possible that the pdf format may have changed. Error code: 2")
                else:
                    # Skip rogue letters: there are sometimes 'q' or 'F', etc.
                    if last_name and first_name:
                        return loop(rest, first_name, last_name, prev_time, time)
                    
                    # Is it the first or last name?
                    if last_name:
                        return loop(rest, token, last_name, prev_time, time)
                    else:
                        return loop(rest, first_name, token.replace(',', ''), prev_time, time)
    return loop(_line.split(' '), None, None, None, None)

def check_qualifiers(pdf_path):
    reader = PdfReader(pdf_path)
    
    # Extract text from each page and split into lines
    lines = []
    for page in reader.pages:
        lines += page.extract_text().split('\n')

    idx = 0
    while idx < len(lines):
        if lines[idx].startswith("Event"):
            event_name = lines[idx]
            print(event_name)

            idx += 2
            
            # Get whether the event is a prelims or a final
            if "Prelim" in lines[idx]:
                event_type = False
                idx += 1
                print("Prelim")
            elif "Final" in lines[idx]:
                event_type = True
                idx += 1
                print("Finals")
            else:
                event_type = None
                print("Other")

            while idx < len(lines) and not lines[idx].startswith("Event"):
                if lines[idx].startswith("Esc"):
                    print(parse_swimmer(lines[idx]))
                idx += 1

        else:
            # Skip other lines
            idx += 1

if __name__ == "__main__":
    check_qualifiers("examples/results.pdf")
