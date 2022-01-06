
MUSIC_NONE = 0
MUSIC_GAME_BGM = 1
MUSIC_CUSTOM_MUSIC = 2

class MusicOption:
    __slots__ = ("option", "music_filename")

    def __init__(self, option, music_filename=None):
        self.option = option
        self.music_filename = music_filename
