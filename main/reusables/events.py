def is_event(level) -> bool:
    """
    Return whether or not a level corresponds to a timesheet event.
    For timesheets, it is simply the level which is passed through.
    For the sign in sheet, it is the hours cell.
    """
    # This check if necessary for sign in sheets because we have either floats or strings
    if not isinstance(level, str):
        return False

    lvl = level.lower()
    return 'gala' in lvl or 'house' in lvl


def event_rate_key(level: str) -> str:
    """Return the rates dict key for an event cell value in the sign-in sheet."""
    lvl = level.lower()
    if 'gala' in lvl:
        return "Gala Half Day" if 'half' in lvl else "Gala Full Day"
    return "House Event"
