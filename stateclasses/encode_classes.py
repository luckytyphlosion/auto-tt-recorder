
from abc import ABC, abstractmethod

ENCODE_TYPE_NONE = -1
ENCODE_TYPE_CRF = 0
ENCODE_TYPE_SIZE_BASED = 1

class EncodeSettings(ABC):
    __slots__ = ("output_format",)

    def __init__(self, output_format):
        self.output_format = output_format

    @property
    @abstractmethod
    def type(self):
        pass

    @staticmethod
    def parse_audio_bitrate(audio_bitrate):
        try:
            if audio_bitrate[-1] == "k":
                audio_bitrate_as_int = int(audio_bitrate[:-1]) * 1000
            else:
                audio_bitrate_as_int = int(audio_bitrate)
        except (ValueError, IndexError) as e:
            raise RuntimeError(f"Invalid audio bitrate \"{audio_bitrate}\"!") from e
    
        return audio_bitrate_as_int

class CrfEncodeSettings(EncodeSettings):
    __slots__ = ("crf", "h26x_preset", "video_codec", "audio_codec", "audio_bitrate", "output_width", "fade_duration", "game_volume", "pix_fmt")

    def __init__(self, output_format, crf, h26x_preset, video_codec, audio_codec, audio_bitrate, output_width, pix_fmt):
        super().__init__(output_format)
        self.crf = crf
        self.h26x_preset = h26x_preset
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.audio_bitrate = self.parse_audio_bitrate(audio_bitrate)
        self.output_width = output_width
        self.fade_duration = 2.5
        self.game_volume = 0.6
        self.pix_fmt = pix_fmt

    @property
    def type(self):
        return ENCODE_TYPE_CRF

class SizeBasedEncodeSettings(EncodeSettings):
    __slots__ = ("video_codec", "audio_codec", "audio_bitrate", "encode_size", "output_width", "fade_duration", "game_volume", "pix_fmt")

    def __init__(self, output_format, video_codec, audio_codec, audio_bitrate, encode_size, output_width, pix_fmt):
        super().__init__(output_format)
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.audio_bitrate = self.parse_audio_bitrate(audio_bitrate)
        self.encode_size = encode_size
        self.output_width = output_width
        self.fade_duration = 2.5
        self.game_volume = 0.6
        self.pix_fmt = pix_fmt

    @property
    def type(self):
        return ENCODE_TYPE_SIZE_BASED
