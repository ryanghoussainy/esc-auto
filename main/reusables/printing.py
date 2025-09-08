RED = 91
YELLOW = 93
GREEN = 92
RESET = 0

def colour_text(colour: int, text: str) -> str:
    '''
    Return the text string wrapped in ANSI escape codes for the specified colour.
    '''
    return f"\033[{colour}m{text}\033[0m"

def print_colour(colour: int, text: str, end: str = "\n") -> None:
    '''
    Print text in the specified colour.
    '''
    print(colour_text(colour, text), end=end)
