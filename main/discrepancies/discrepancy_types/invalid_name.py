from discrepancies.discrepancy_types.discrepancy import Discrepancy

class InvalidName(Discrepancy):
    def __init__(self, name: str, sign_in_names: list[str]):
        self.name = name
        self.sign_in_names = sign_in_names

    def __str__(self):
        return f"- Invalid name in timesheet: {self.name}\n" \
               f"Names in sign in sheet are:\n" \
               f"{', '.join(self.sign_in_names)}"
