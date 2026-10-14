from discrepancies.discrepancy_types.discrepancy import Discrepancy

class TimesheetMonthMismatch(Discrepancy):
    """The month written on a timesheet is not the month being checked (e.g. an old or copied timesheet)"""
    def __init__(self, name: str, found_month: str, expected_month: str):
        self.name = name
        self.found_month = found_month
        self.expected_month = expected_month

    def __str__(self):
        return f"- {self.name}'s timesheet says '{self.found_month}' but you are checking '{self.expected_month}'"
