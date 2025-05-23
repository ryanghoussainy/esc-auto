RED = 91
YELLOW = 93
GREEN = 92

def print_colour(colour: int, text: str, end: str = "\n") -> None:
    '''
    Print text in the specified colour.
    '''
    print(f"\033[{colour}m{text}\033[0m", end=end)