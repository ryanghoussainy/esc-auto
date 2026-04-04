

def normalise_time(t):
    return str(t).replace(':', '.').replace(',', '.')


def is_disqualification(t) -> bool:
    return "DQ" in str(t).upper()

