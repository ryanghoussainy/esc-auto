from discrepancies.discrepancy_types.discrepancy import Discrepancy
from reusables.printing import RED, colour_text

class SwimmerNotFound(Discrepancy):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return colour_text(RED, f"Swimmer {self.name} not found in PDF")
