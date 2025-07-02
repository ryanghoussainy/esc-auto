
MAIN_EVENTS = set([
    '25m Free',
    '25m Back',
    '25m Breast',
    '25m Fly',
    '50m Free',
    '50m Back',
    '50m Breast',
    '50m Fly',
    '100m Free',
    '100m Back',
    '100m Breast',
    '100m Fly',
    '100m IM',
])


def is_final(event_name: str) -> bool:
    '''
    Check if the event is a final.
    '''
    return event_name not in MAIN_EVENTS

def rename_final_column(leah_tables, time_column_name: str):
    for table in leah_tables:
        if "Finals" in table.columns:
            table.rename(columns={"Finals": time_column_name}, inplace=True)
