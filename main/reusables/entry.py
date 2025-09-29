from datetime import date

class Entry:
    def __init__(self, date: date, hours: float, rate: float):
        self.date = date
        self.hours = hours
        self.rate = rate
    
    def __eq__(self, other):
        if not isinstance(other, Entry):
            raise NotImplementedError("Can only compare Entry with another Entry")
        return (self.date, self.hours, self.rate) == (other.date, other.hours, other.rate)

    def __hash__(self):
        return hash((self.date, self.hours, self.rate))
