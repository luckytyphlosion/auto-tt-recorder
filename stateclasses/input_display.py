
INPUT_DISPLAY_CLASSIC = 0
INPUT_DISPLAY_NUNCHUCK = 1
INPUT_DISPLAY_WHEEL = 2
INPUT_DISPLAY_NONE = 3

class InputDisplay:
    __slots__ = ("type", "rkg_file_or_data", "dont_create")

    def __init__(self, type, dont_create):
        self.type = type
        self.dont_create = dont_create
        self.rkg_file_or_data = None

    def set_rkg_file_or_data(self, rkg_file_or_data):
        self.rkg_file_or_data = rkg_file_or_data
