
import enumarg
import util

SOM_FANCY_KM_H = 0
SOM_REGULAR_KM_H = 1
SOM_STANDARD = 2
SOM_NONE = 3

SOM_METRIC_ENGINE = 0
SOM_METRIC_XYZ = 1

som_enum_arg_table = enumarg.EnumArgTable({
    "fancy": SOM_FANCY_KM_H,
    "regular": SOM_REGULAR_KM_H,
    "standard": SOM_STANDARD,
    "none": SOM_NONE
})

som_metric_enum_arg_table = enumarg.EnumArgTable({
    "engine": SOM_METRIC_ENGINE,
    "xyz": SOM_METRIC_XYZ
})

class SpeedometerOption:
    __slots__ = ("style", "metric", "decimal_places")

    def __init__(self, style, metric="engine", decimal_places=None):
        if type(style) == str:
            self.style = som_enum_arg_table.parse_enum_arg(style, "Unknown speedometer style \"{}\"!")
        elif type(style) == int:
            if style not in (SOM_FANCY_KM_H, SOM_REGULAR_KM_H, SOM_STANDARD, SOM_NONE):
                raise RuntimeError(f"Unknown speedometer style \"{style}\"!")
            self.style = style
        else:
            raise RuntimeError("Invalid type for speedometer style!")

        if self.style != SOM_NONE:
            self.metric = som_metric_enum_arg_table.parse_enum_arg(metric, "Unknown speedometer metric \"{}\"!")

            if self.style == SOM_FANCY_KM_H:
                self.decimal_places = util.arg_default_or_validate_from_choices(decimal_places,
                    1, 0, "Only 0 or 1 decimal places are allowed for fancy km/h speedometer! (got: \"{}\")")
            elif self.style == SOM_REGULAR_KM_H:
                self.decimal_places = util.arg_default_or_validate_from_choices(decimal_places
                    2, 0, 1, "Only 0 to 2 decimal places are allowed for regular km/h speedometer! (got: \"{}\")")
            elif self.style == SOM_STANDARD:
                self.decimal_places = 2
            else:
                assert False
        else:
            self.metric = None
            self.decimal_places = None
