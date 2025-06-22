from reusables.printing import print_colour, RED, YELLOW, GREEN

TIME_DISCREPANCY = 0
SWIMMER_NOT_FOUND_DISCREPANCY = 1

def print_discrepancies(discrepancies, isQualifiers):
    print(f"Finished checking {'qualifiers' if isQualifiers else 'finals'}.", end='')
    if discrepancies:

        print("Mismatches found:")
        for d in discrepancies:
            # Extract information
            discrepancy_type, name, event_name, pdf_time, excel_time = d

            print("- ", end='')
            # Print type of mismatch in red
            if discrepancy_type == TIME_DISCREPANCY:
                print_colour(RED, "Time mismatch ", end='')
                print("for ", end='')
                print_colour(YELLOW, name, end=' - ')
                print(f"Event: {event_name}, ", end='')
                print(f"PDF: {pdf_time}, EXCEL: {excel_time}")
            elif discrepancy_type == SWIMMER_NOT_FOUND_DISCREPANCY:
                print_colour(RED, f"Swimmer {name} not found in PDF")
    else:
        print_colour(GREEN, "No mismatches found.")
