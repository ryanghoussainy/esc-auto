from discrepancies.discrepancy_types.discrepancy import Discrepancy

class EmptyTimesheet(Discrepancy):
    def __init__(self, name: str):
        self.name = name
    
    def __str__(self):
        return f"- Empty timesheet: {self.name}"