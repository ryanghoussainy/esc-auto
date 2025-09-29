from discrepancies.discrepancy_types.discrepancy import Discrepancy
from reusables.entry import Entry

class TimesheetExtraEntry(Discrepancy):
    def __init__(self, name: str, entry: Entry):
        self.name = name
        self.entry = entry

    def __str__(self):
        return f"- Extra entry in timesheet for {self.name}: {self.entry.hours} hours on {self.entry.date} at {self.entry.rate}/hour"
