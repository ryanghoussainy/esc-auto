from discrepancies.discrepancy_types.discrepancy import Discrepancy

class SwimmerNotFound(Discrepancy):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Swimmer {self.name} not found in PDF"
