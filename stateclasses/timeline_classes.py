
from abc import ABC, abstractmethod

TIMELINE_NO_ENCODE = 0
TIMELINE_FROM_TT_GHOST_SELECTION = 1
TIMELINE_FROM_WORLD_CHAMPION_SCREEN = 2
TIMELINE_FROM_TOP_10_LEADERBOARD = 3

class TimelineSettings(ABC):
    def __init__(self):
        pass

    @property
    @abstractmethod
    def type(self):
        pass

class NoEncodeTimelineSettings(TimelineSettings):
    __slots__ = ("output_format",)

    def __init__(self, output_format):
        self.output_format = output_format

    @property
    def type(self):
        return TIMELINE_NO_ENCODE

class FromTTGhostSelectionTimelineSettings(TimelineSettings):
    __slots__ = ("encode_settings", "input_display")

    def __init__(self, encode_settings, input_display):
        self.encode_settings = encode_settings
        self.input_display = input_display

    @property
    def type(self):
        return TIMELINE_FROM_TT_GHOST_SELECTION

class FromTop10LeaderboardTimelineSettings(TimelineSettings):
    __slots__ = ("encode_settings", "input_display", "custom_top_10_and_ghost_description")

    def __init__(self, encode_settings, input_display, custom_top_10_and_ghost_description):
        self.encode_settings = encode_settings
        self.input_display = input_display
        self.custom_top_10_and_ghost_description = custom_top_10_and_ghost_description

    @property
    def type(self):
        return TIMELINE_FROM_TOP_10_LEADERBOARD
