from reusables.printing import print_colour, GREEN


def print_discrepancies(discrepancies, isQualifiers):
    print(f"Finished checking {'qualifiers' if isQualifiers else 'finals'}.", end='')
    if discrepancies:

        print("Mismatches found:")
        for d in discrepancies:
            print(d)
    else:
        print_colour(GREEN, "No mismatches found.")
