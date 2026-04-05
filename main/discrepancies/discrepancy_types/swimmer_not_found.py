from discrepancies.discrepancy_types.discrepancy import Discrepancy

class SwimmersNotFound(Discrepancy):
    def __init__(self, names, pdf=True, event_name=None, missing_time=None):
        self.names = ", ".join(names)
        self.pdf = 'PDF' if pdf else 'Excel' # whether the swimmer was not found in the PDF or in the qualifiers table
        self.event_name = event_name
        self.missing_time = missing_time

    def __str__(self):
        event_suffix = f" (Event: {self.event_name})" if self.event_name else ""
        time_suffix = f" (Time: {self.missing_time})" if self.missing_time is not None else ""
        return f"Swimmers {self.names} not found in {self.pdf}{event_suffix}{time_suffix}"