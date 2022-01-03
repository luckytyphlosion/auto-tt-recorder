
SOM_FANCY_KM_H = 0
SOM_REGULAR_KM_H = 1
SOM_STANDARD = 2
SOM_NONE = 3

SOM_METRIC_ENGINE = 0
SOM_METRIC_XYZ = 1

class SpeedometerOption:
    __slots__ = ("style", "metric", "decimal_places")

    def __init__(self, style, metric=None, decimal_places=None):
        self.style = style
        self.metric = metric
        self.decimal_places = decimal_places

