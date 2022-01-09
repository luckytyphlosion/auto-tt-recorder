
class EnumArgTable:
    __slots__ = ("enum_to_val", "valid_values")

    def __init__(self, enum_to_val):
        self.enum_to_val = enum_to_val
        self.valid_values = set(enum_to_val.values())

    def parse_enum_arg(self, enum_arg, error_message=None):
        try:
            enum_value = int(enum_arg)
            if enum_value in self.valid_values:
                return enum_value
        except ValueError:
            pass

        try:
            return self.enum_to_val[enum_arg]
        except KeyError as e:
            if error_message is None:
                raise RuntimeError(f"Unknown enum_arg value \"{enum_arg}\"!") from e
            else:
                raise RuntimeError(error_message.format(enum_arg)) from e
