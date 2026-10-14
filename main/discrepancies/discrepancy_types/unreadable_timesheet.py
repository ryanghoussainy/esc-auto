from discrepancies.discrepancy_types.discrepancy import Discrepancy

class UnreadableTimesheet(Discrepancy):
    """A timesheet file that could not be read at all (bad template, missing data, etc.)"""
    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason

    def __str__(self):
        return f"- Could not read timesheet: {self.reason}"
