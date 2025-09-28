
def display_discrepancies(discrepancies, progress_callback):
    if discrepancies:

        progress_callback(f"Mismatches found: {len(discrepancies)}", "red")

        for d in discrepancies:
            progress_callback(str(d))
    else:
        progress_callback("No mismatches found.", "green")
