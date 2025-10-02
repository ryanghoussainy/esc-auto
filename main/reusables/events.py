def is_event(level: str) -> bool:
    lvl = level.lower()
    return 'gala' in lvl or 'house' in lvl
