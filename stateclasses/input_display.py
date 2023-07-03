import enumarg

INPUT_DISPLAY_CLASSIC = 0
INPUT_DISPLAY_NUNCHUCK = 1
INPUT_DISPLAY_WHEEL = 2
INPUT_DISPLAY_NONE = 3
INPUT_DISPLAY_AUTO = 4

CONTROLLER_WII_WHEEL = 0
CONTROLLER_NUNCHUCK = 1
CONTROLLER_CLASSIC = 2
CONTROLLER_GAMECUBE = 3
CONTROLLER_UNKNOWN = 15

class InputDisplayGeometry:
    __slots__ = ("base_inputs_x", "base_inputs_y", "base_inputs_width", "base_inputs_height", "base_input_box_x", "base_input_box_y", "base_input_box_width", "base_input_box_height", "input_box_vertical_stretch_y_offset_callback")

    def __init__(self, base_inputs_x, base_inputs_y, base_inputs_width, base_inputs_height, base_input_box_x, base_input_box_y, base_input_box_width, base_input_box_height, input_box_vertical_stretch_y_offset_callback):
        self.base_inputs_x = base_inputs_x
        self.base_inputs_y = base_inputs_y
        self.base_inputs_width = base_inputs_width
        self.base_inputs_height = base_inputs_height
        self.base_input_box_x = base_input_box_x
        self.base_input_box_y = base_input_box_y
        self.base_input_box_width = base_input_box_width
        self.base_input_box_height = base_input_box_height
        self.input_box_vertical_stretch_y_offset_callback = input_box_vertical_stretch_y_offset_callback

def adjust_input_box_y_offset_for_vertical_stretch(rect, vertical_stretch_factor):
    return rect.y_offset + 52 * (vertical_stretch_factor - 1)

input_display_controller_geometries = {
    INPUT_DISPLAY_CLASSIC: InputDisplayGeometry(
        base_inputs_x=148,
        base_inputs_y=2161,
        base_inputs_width=1216,
        base_inputs_height=769,
        base_input_box_x=209,
        base_input_box_y=2195,
        base_input_box_width=1060,
        base_input_box_height=681,
        input_box_vertical_stretch_y_offset_callback=adjust_input_box_y_offset_for_vertical_stretch
    ),
    INPUT_DISPLAY_NUNCHUCK: InputDisplayGeometry(
        base_inputs_x=358,
        base_inputs_y=2120,
        base_inputs_width=811,
        base_inputs_height=751,
        base_input_box_x=287,
        base_input_box_y=2112,
        base_input_box_width=896,
        base_input_box_height=765,
        input_box_vertical_stretch_y_offset_callback=adjust_input_box_y_offset_for_vertical_stretch
    ),
    INPUT_DISPLAY_WHEEL: None,
    INPUT_DISPLAY_NONE: None,
}

input_display_names = {
    INPUT_DISPLAY_CLASSIC: "classic",
    INPUT_DISPLAY_NUNCHUCK: "nunchuck",
    INPUT_DISPLAY_WHEEL: "wheel",
    INPUT_DISPLAY_NONE: "none"
}

input_display_box_filenames = {
    INPUT_DISPLAY_CLASSIC: "data/input_box.png",
    INPUT_DISPLAY_NUNCHUCK: "data/input_box_nunchuck.png",
    INPUT_DISPLAY_WHEEL: None,
    INPUT_DISPLAY_NONE: None,
}

input_display_enum_arg_table = enumarg.EnumArgTable({
    "classic": INPUT_DISPLAY_CLASSIC,
    "gcn": INPUT_DISPLAY_CLASSIC,
    "nunchuck": INPUT_DISPLAY_NUNCHUCK,
    "none": INPUT_DISPLAY_NONE,
    "auto": INPUT_DISPLAY_AUTO
})

# input display, warning
controller_to_input_display = {
    CONTROLLER_WII_WHEEL: (INPUT_DISPLAY_CLASSIC, "Wheel input display does not exist, defaulting to GCN/Classic."),
    CONTROLLER_NUNCHUCK: (INPUT_DISPLAY_NUNCHUCK, None),
    CONTROLLER_CLASSIC: (INPUT_DISPLAY_CLASSIC, None),
    CONTROLLER_GAMECUBE: (INPUT_DISPLAY_CLASSIC, None),
    CONTROLLER_UNKNOWN: (INPUT_DISPLAY_CLASSIC, "Could not automatically detect controller (either chadsoft link not supplied or data possibly missing in Chadsoft), defaulting to GCN/Classic.")
}

class InputDisplay:
    __slots__ = ("type", "rkg_file_or_data", "dont_create", "geometry", "name", "box_filename")

    def __init__(self, input_display_arg, controller, dont_create):
        self.type = input_display_enum_arg_table.parse_enum_arg(input_display_arg, "Unknown input display type \"{}\"!")
        if self.type == INPUT_DISPLAY_AUTO:
            self.type, warning = controller_to_input_display[controller]
            if warning is not None:
                print(f"Warning: {warning}")

        self.dont_create = dont_create
        self.rkg_file_or_data = None
        self.geometry = input_display_controller_geometries[self.type]
        self.name = input_display_names[self.type]
        self.box_filename = input_display_box_filenames[self.type]

    def set_rkg_file_or_data(self, rkg_file_or_data):
        self.rkg_file_or_data = rkg_file_or_data
