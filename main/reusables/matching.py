import pandas as pd
from fuzzywuzzy import fuzz


def get_close_matches(
        qualifiers_table: pd.DataFrame,
        lfirst_name: str,
        lsurname: str,
        automatic_matches: dict,
        manual_matches: dict,
        sfirst_name_col: str = "First name",
        ssurname_col: str = "Surname",
) -> list[tuple[str, str, int]]:
    '''
    Get the closest matches for a swimmer in Sammy's version.
    '''
    scores = []
    for _, srow in qualifiers_table.iterrows():
        # Skip automatic and manual matches
        if (srow[sfirst_name_col], srow[ssurname_col]) in automatic_matches.values() or \
            (srow[sfirst_name_col], srow[ssurname_col]) in manual_matches.values():
            continue

        scores.append((srow[sfirst_name_col], srow[ssurname_col], fuzz.ratio(lfirst_name + " " + lsurname, srow[sfirst_name_col].lower() + " " + srow[ssurname_col].lower())))
    scores.sort(key=lambda x: x[2], reverse=True)
    return scores


def prompt_manual_match(
    lfirst_name: str,
    lsurname: str,
    scores: list[tuple[str, str, int]],
    qualifiers_table: pd.DataFrame,
    manual_matches: dict[tuple[str, str], tuple[str, str]],
    progress_callback,
    confirm_callback,
    sfirst_name_col: str = "First name",
    ssurname_col: str = "Surname",
) -> pd.DataFrame:
    """
    Prompt the user to manually confirm a match from a list of scored candidates.
    Returns the matched swimmer DataFrame.
    """
    progress_callback(f"Trying to match... {lfirst_name.capitalize()} {lsurname.capitalize()}", "yellow")

    for sfirst_name, ssurname, score in scores:
        match_data = {
            'leah_name': f"{lfirst_name.capitalize()} {lsurname.capitalize()}",
            'sammy_name': f"{sfirst_name.capitalize()} {ssurname.capitalize()}",
            'similarity': score
        }

        match = confirm_callback(match_data)
        
        # Handle response
        if match.lower() == 'exit':
            raise KeyboardInterrupt("User cancelled operation")

        if match.lower() == 'ignore':
            progress_callback(f"Ignored swimmer: {lfirst_name.capitalize()} {lsurname.capitalize()}", "yellow")
            return pd.DataFrame()

        if match.lower() == 'y':
            manual_matches[(lfirst_name, lsurname)] = (sfirst_name, ssurname)
            swimmer = qualifiers_table[
                (qualifiers_table[sfirst_name_col] == sfirst_name) &
                (qualifiers_table[ssurname_col] == ssurname)
            ]
            progress_callback(f"Manual match confirmed: {lfirst_name.capitalize()} {lsurname.capitalize()} -> {sfirst_name.capitalize()} {ssurname.capitalize()}", "green")
            return swimmer
        
        progress_callback(f"Match rejected, trying next candidate...", "yellow")
    
    # No matches found
    error_msg = f"No swimmer found: {lfirst_name.capitalize()} {lsurname.capitalize()}"
    progress_callback(error_msg, "red")
    raise ValueError(error_msg)


def match_swimmer(
    lfirst_name: str,
    lsurname: str,
    qualifiers_table: pd.DataFrame,
    automatic_matches: dict[tuple[str, str], tuple[str, str]],
    manual_matches: dict[tuple[str, str], tuple[str, str]],
    progress_callback,
    confirm_callback,
    sfirst_name_col: str = "First name",
    ssurname_col: str = "Surname",
) -> pd.DataFrame:
    """
    Find and return the swimmer row in qualifiers_table matching the given Leah swimmer.
    
    Args:
        lfirst_name: First name from Leah's file
        lsurname: Surname from Leah's file
        qualifiers_table: Sammy's qualifiers DataFrame
        automatic_matches: Dict of previously confirmed automatic matches
        manual_matches: Dict of previously confirmed manual matches
        progress_callback: Callback for progress messages (message, color)
        confirm_callback: Callback for user confirmations (message, data) -> response
        sfirst_name_col: Column name for first name in Sammy's file
        ssurname_col: Column name for surname in Sammy's file
    """
    # Check automatic matches first
    key = (lfirst_name, lsurname)
    if key in automatic_matches:
        sfirst, ssurname = automatic_matches[key]
        swimmer = qualifiers_table[
            (qualifiers_table[sfirst_name_col] == sfirst) &
            (qualifiers_table[ssurname_col] == ssurname)
        ]
        progress_callback(f"Found automatic match: {lfirst_name.capitalize()} {lsurname.capitalize()}", "green")
        return swimmer
    
    # Check manual matches already confirmed
    if key in manual_matches:
        sfirst, ssurname = manual_matches[key]
        swimmer = qualifiers_table[
            (qualifiers_table[sfirst_name_col] == sfirst) &
            (qualifiers_table[ssurname_col] == ssurname)
        ]
        progress_callback(f"Found previous manual match: {lfirst_name.capitalize()} {lsurname.capitalize()}", "green")
        return swimmer

    # Compute close matches
    scores = get_close_matches(
        qualifiers_table,
        lfirst_name,
        lsurname,
        automatic_matches,
        manual_matches,
        sfirst_name_col=sfirst_name_col,
        ssurname_col=ssurname_col
    )
    
    if not scores:
        error_msg = f"No potential matches found in qualifiers table for: {lfirst_name.capitalize()} {lsurname.capitalize()}"
        progress_callback(error_msg, "red")
        return pd.DataFrame()
    
    first_candidate = scores[0]

    # Exact match (100% similarity)
    if first_candidate[2] == 100:
        sfirst, ssurname = first_candidate[0], first_candidate[1]
        automatic_matches[key] = (sfirst, ssurname)
        swimmer = qualifiers_table[
            (qualifiers_table[sfirst_name_col] == sfirst) &
            (qualifiers_table[ssurname_col] == ssurname)
        ]
        progress_callback(f"Found exact match: {lfirst_name.capitalize()} {lsurname.capitalize()} -> {sfirst.capitalize()} {ssurname.capitalize()}", "green")
        return swimmer

    # Otherwise, prompt for manual match
    progress_callback(f"No exact match found for {lfirst_name.capitalize()} {lsurname.capitalize()}, requesting manual confirmation...", "yellow")
    
    return prompt_manual_match(
        lfirst_name,
        lsurname,
        scores,
        qualifiers_table,
        manual_matches,
        sfirst_name_col=sfirst_name_col,
        ssurname_col=ssurname_col,
        progress_callback=progress_callback,
        confirm_callback=confirm_callback,
    )
