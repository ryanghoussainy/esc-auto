def display_discrepancies(discrepancies, progress_callback):
    # sort discrepancies by 1. if there is no name/names attribute, 2. by name/names attribute, 3. by entry date if applicable
    def get_name(d):
        if hasattr(d, 'name'):
            return d.name
        elif hasattr(d, 'names'):
            return d.names
        return ''
    
    discrepancies.sort(key=lambda d: (not (hasattr(d, 'name') or hasattr(d, 'names')), get_name(d), d.entry.date if hasattr(d, 'entry') else None))

    if discrepancies:

        progress_callback(f"Mismatches found: {len(discrepancies)}", "red")

        for d in discrepancies:
            progress_callback(str(d))
    else:
        progress_callback("No mismatches found.", "green")
