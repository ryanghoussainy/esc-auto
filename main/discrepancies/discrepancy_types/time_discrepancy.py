from discrepancies.discrepancy_types.discrepancy import Discrepancy
from reusables.printing import RED, YELLOW, colour_text

class TimeDiscrepancy(Discrepancy):
    def __init__(self, name, event_name, pdf_time, excel_time):
        self.name = name
        self.event_name = event_name
        self.pdf_time = pdf_time
        self.excel_time = excel_time

    def __str__(self):
        return (f"{colour_text(RED, 'Time mismatch')} for {colour_text(YELLOW, self.name)} - "
                f"Event: {self.event_name}\n"
                f"     PDF: {self.pdf_time}\n"
                f"     EXCEL: {self.excel_time}")
