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
