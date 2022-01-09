
class Split:
    __slots__ = ("minutes", "seconds", "milliseconds")

    def __init__(self, minutes, seconds, milliseconds):
        self.minutes = minutes
        self.seconds = seconds
        self.milliseconds = milliseconds

    def pretty(self):
        return f"{self.minutes:02d}:{self.seconds:02d}.{self.milliseconds:03d}"
