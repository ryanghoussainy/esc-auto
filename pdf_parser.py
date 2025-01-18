from pypdf import PdfReader

reader = PdfReader("results.pdf")

KEYWORDS = ['NT', 'NS', 'DQ']

# Check for dots because times are stored in 'xx:xx.xx' or 'xx.xx' format
def is_time(s):
    return '.' in s


def contains_digit(x):
    for c in x:
        if c.isdigit():
            return True
    return False


def keywords(x):
    for kw in KEYWORDS:
        if kw in x:
            return kw
    return None


def parse_swimmer(_line):
    def loop(line, first_name, last_name, prev_time, time):
        match line:
            case []:
                if not first_name or not last_name or not prev_time or not time:
                    print(_line.split(' '), first_name, last_name, prev_time, time)
                    raise Exception("Could not parse swimmer times. It is possible that the pdf format may have changed. Error code: 1")
                return first_name, last_name, prev_time, time
            case ['Esc', *xs]:
                return loop(xs, first_name, last_name, prev_time, time)
            case ['', *xs]:
                return loop(xs, first_name, last_name, prev_time, time)
            case [x, *xs]:
                if not last_name and contains_digit(x):
                    return loop(xs, first_name, last_name, prev_time, time)
                
                kws_x = keywords(x)
                if is_time(x) or kws_x:
                    # Adjust for keywords, e.g. 'DQ', 'NT', etc.
                    if kws_x:
                        x = kws_x

                    # It's only a time if we haven't gotten the name yet
                    if first_name and last_name:
                        # Is 'x' the previous time or achieved time?
                        if time:
                            return first_name, last_name, x, time
                        else:
                            return loop(xs, first_name, last_name, prev_time, x)
                    else:
                        print(line)
                        raise Exception("Could not parse swimmer times. It is possible that the pdf format may have changed. Error code: 2")
                else:
                    # Skip rogue letters: there are sometimes 'q' or 'F', etc.
                    if last_name and first_name:
                        return loop(xs, first_name, last_name, prev_time, time)
                    
                    # Is it the first or last name?
                    if last_name:
                        return loop(xs, x, last_name, prev_time, time)
                    else:
                        return loop(xs, first_name, x.replace(',', ''), prev_time, time)
    return loop(_line.split(' '), None, None, None, None)
                

number_of_pages = len(reader.pages)

lines = []

for pageIdx in range(number_of_pages):
    page = reader.pages[pageIdx]
    text = page.extract_text()
    lines += text.split('\n')

for line in lines:
    print(line)

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
