from datetime import date

class Entry:
    def __init__(self, date: date, hours: float, rate: float, is_event: bool):
        self.date = date
        self.hours = hours
        self.rate = rate
        self.is_event = is_event
    
    def __eq__(self, other):
        if not isinstance(other, Entry):
            raise NotImplementedError("Can only compare Entry with another Entry")
        if self.is_event and other.is_event:
            # If both are events, don't compare number of hours
            return (self.date, self.rate) == (other.date, other.rate)
        return (self.date, self.hours, self.rate, self.is_event) == (other.date, other.hours, other.rate, other.is_event)

    def __hash__(self):
        if self.is_event:
            return hash((self.date, self.rate, self.is_event))
        return hash((self.date, self.hours, self.rate, self.is_event))
