def is_event(level: str) -> bool:
    """
    Return whether or not a level corresponds to a timesheet event.
    For timesheets, it is simply the level which is passed through.
    For the sign in sheet, it is the hours cell.
    """
    lvl = level.lower()
    return 'gala' in lvl or 'house' in lvl
