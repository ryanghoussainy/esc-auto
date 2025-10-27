
def display_discrepancies(discrepancies, progress_callback):
    # sort discrepancies by 1. if there is no name attribute, 2. by name attribute, 3. by entry date if applicable
    discrepancies.sort(key=lambda d: (not hasattr(d, 'name'), d.name, d.entry.date if hasattr(d, 'entry') else None))

    if discrepancies:

        progress_callback(f"Mismatches found: {len(discrepancies)}", "red")

        for d in discrepancies:
            progress_callback(str(d))
    else:
        progress_callback("No mismatches found.", "green")
