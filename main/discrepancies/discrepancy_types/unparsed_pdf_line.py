from discrepancies.discrepancy_types.discrepancy import Discrepancy

class UnparsedPdfLine(Discrepancy):
    """A swimmer line in the results PDF that could not be parsed, so that swimmer was not checked"""
    def __init__(self, event: str, line: str, reason: str):
        self.event = event
        self.line = line
        self.reason = reason

    def __str__(self):
        return f"- Could not read PDF line under '{self.event}': {self.line.strip()} ({self.reason})"
