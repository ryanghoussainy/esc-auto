import pandas as pd
from reusables import print_colour, RED, YELLOW, GREEN
from fuzzywuzzy import fuzz

VALID_MATCH_INPUTS = ["y", "n", "exit"]  # Valid inputs for matching swimmers
VALID_MATCH_INPUTS_STR = f"({'/'.join(VALID_MATCH_INPUTS)}): "  # e.g. "(y, n, exit)"


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
    sfirst_name_col: str = "First name",
    ssurname_col: str = "Surname",
) -> pd.DataFrame:
    """
    Prompt the user to manually confirm a match from a list of scored candidates.
    Returns the matched swimmer DataFrame.
    """
    print_colour(YELLOW, f"Trying to match... {lfirst_name.capitalize()} {lsurname.capitalize()}")
    for sfirst_name, ssurname, score in scores:
        print(f"Is this the right match? ", end="")
        print_colour(YELLOW, f"{lfirst_name.capitalize()} {lsurname.capitalize()}", end="")
        print_colour(YELLOW, f" -> {sfirst_name.capitalize()} {ssurname.capitalize()}", end="")
        print(f" (similarity score: {score}%)")
        match = input(VALID_MATCH_INPUTS_STR)

        while match.lower() not in VALID_MATCH_INPUTS:
            print("Invalid input")
            match = input(VALID_MATCH_INPUTS_STR)

        if match.lower() == 'exit':
            exit()
        if match.lower() == 'y':
            manual_matches[(lfirst_name, lsurname)] = (sfirst_name, ssurname)
            swimmer = qualifiers_table[
                (qualifiers_table[sfirst_name_col] == sfirst_name) &
                (qualifiers_table[ssurname_col] == ssurname)
            ]
            return swimmer

    raise ValueError(f"No swimmer found: {lfirst_name.capitalize()} {lsurname.capitalize()}")
    

def match_swimmer(
    lfirst_name: str,
    lsurname: str,
    qualifiers_table: pd.DataFrame,
    automatic_matches: dict[tuple[str, str], tuple[str, str]],
    manual_matches: dict[tuple[str, str], tuple[str, str]],
    sfirst_name_col: str = "First name",
    ssurname_col: str = "Surname",
) -> pd.DataFrame:
    """
    Find and return the swimmer row in qualifiers_table matching the given Leah swimmer.
    """
    # Automatic match
    key = (lfirst_name, lsurname)
    if key in automatic_matches:
        sfirst, ssurname = automatic_matches[key]
        swimmer = qualifiers_table[
            (qualifiers_table[sfirst_name_col] == sfirst) &
            (qualifiers_table[ssurname_col] == ssurname)
        ]
        return swimmer
    
    # Manual match already exists
    if key in manual_matches:
        sfirst, ssurname = manual_matches[key]
        swimmer = qualifiers_table[
            (qualifiers_table[sfirst_name_col] == sfirst) &
            (qualifiers_table[ssurname_col] == ssurname)
        ]
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
    first_candidate = scores[0]

    # Exact match
    if first_candidate[2] == 100:
        sfirst, ssurname = first_candidate[0], first_candidate[1]
        automatic_matches[key] = (sfirst, ssurname)
        swimmer = qualifiers_table[
            (qualifiers_table[sfirst_name_col] == sfirst) &
            (qualifiers_table[ssurname_col] == ssurname)
        ]
        return swimmer

    # Otherwise, prompt for manual match
    return prompt_manual_match(
        lfirst_name,
        lsurname,
        scores,
        qualifiers_table,
        manual_matches,
        sfirst_name_col=sfirst_name_col,
        ssurname_col=ssurname_col,
    )
