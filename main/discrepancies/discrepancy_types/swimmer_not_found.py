from discrepancies.discrepancy_types.discrepancy import Discrepancy

class SwimmersNotFound(Discrepancy):
    def __init__(self, names, pdf=True):
        self.names = ", ".join(names)
        self.pdf = 'PDF' if pdf else 'Excel' # whether the swimmer was not found in the PDF or in the qualifiers table

    def __str__(self):
        return f"Swimmers {self.names} not found in {self.pdf}"