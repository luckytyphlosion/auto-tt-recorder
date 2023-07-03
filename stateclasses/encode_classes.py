
from abc import ABC, abstractmethod
import util

ENCODE_TYPE_NONE = -1
ENCODE_TYPE_CRF = 0
ENCODE_TYPE_SIZE_BASED = 1

INFINITY = float("inf")
MINUS_INFINITY = float("-inf")

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

    def validate_and_set_output_width(self, output_width):
        if output_width is not None:
            if type(output_width) != int:
                raise RuntimeError("Output value not None or int!")
            elif output_width % 2 == 1:
                raise RuntimeError("Output width not even!")
            elif output_width < 2:
                raise RuntimeError("Output width too small!")

        self.output_width = output_width

    @staticmethod
    def validate_int_and_or_float(value, name, lower_bound=MINUS_INFINITY, upper_bound=INFINITY, allowed_types=(float, int)):
        if type(value) not in allowed_types:
            raise RuntimeError(f"{name} not in allowed types {allowed_types}!")

        if not (lower_bound <= value <= upper_bound):
            raise RuntimeError(f"{name} not in range [{lower_bound}, {upper_bound}]!")

        return value

    def validate_default_set_audio_bitrate(self, audio_bitrate, audio_codec, default_table):
        if audio_bitrate is None:
            audio_bitrate = default_table[audio_codec]

        self.audio_bitrate = self.parse_audio_bitrate(audio_bitrate)

crf_encode_default_audio_bitrate_table = {
    "libopus": "128k",
    "aac": "384k"
}

size_based_encode_default_audio_bitrate_table = {
    "libopus": "64k",
    "aac": "128k"
}

class CrfEncodeSettings(EncodeSettings):
    __slots__ = ("crf", "h26x_preset", "video_codec", "audio_codec", "audio_bitrate", "output_width", "fade_frame_duration", "game_volume", "pix_fmt", "music_volume", "youtube_settings", "aspect_ratio_16_by_9")

    def __init__(self, output_format, crf, h26x_preset, video_codec, audio_codec, audio_bitrate, output_width, pix_fmt, youtube_settings, game_volume, music_volume, aspect_ratio_16_by_9):
        if output_format not in ("mkv", "mp4"):
            raise RuntimeError(f"Invalid output format \"{output_format}\" for crf encode!")
        super().__init__(output_format)

        self.crf = self.validate_int_and_or_float(crf, "Crf value", 0, 51)

        self.video_codec = util.arg_default_or_validate_from_choices(video_codec, "libx264", "libx265", "Unsupported crf-based codec \"{}\"!")

        self.h26x_preset = util.arg_default_or_validate_from_choices(h26x_preset, "medium", "ultrafast", "superfast", "veryfast", "faster", "fast", "slow", "slower", "veryslow", "placebo", "Unsupported H.26x preset \"{}\"!")

        if self.output_format == "mkv":
            self.audio_codec = util.arg_default_select(audio_codec, "libopus")
        elif self.output_format == "mp4":
            self.audio_codec = util.arg_default_select(audio_codec, "aac")
        else:
            assert False

        self.validate_default_set_audio_bitrate(audio_bitrate, self.audio_codec, crf_encode_default_audio_bitrate_table)

        self.validate_and_set_output_width(output_width)

        self.output_width = output_width
        self.fade_frame_duration = 150
        self.game_volume = game_volume
        self.music_volume = music_volume
        self.pix_fmt = pix_fmt
        self.youtube_settings = youtube_settings
        if aspect_ratio_16_by_9 == "auto":
            aspect_ratio_16_by_9 = True
        self.aspect_ratio_16_by_9 = aspect_ratio_16_by_9

    @property
    def type(self):
        return ENCODE_TYPE_CRF

class SizeBasedEncodeSettings(EncodeSettings):
    __slots__ = ("video_codec", "audio_codec", "audio_bitrate", "encode_size", "output_width", "fade_frame_duration", "game_volume", "pix_fmt", "music_volume", "aspect_ratio_16_by_9")

    def __init__(self, output_format, video_codec, audio_codec, audio_bitrate, encode_size, output_width, pix_fmt, game_volume, music_volume, aspect_ratio_16_by_9):
        if output_format not in ("mkv", "mp4", "webm"):
            raise RuntimeError(f"Invalid output format \"{output_format}\" for size based encode!")
        super().__init__(output_format)

        if output_format == "webm":
            self.video_codec = util.arg_default_or_validate_from_choices(video_codec, "libvpx-vp9",
                "Only libvpx-vp9 is supported for size-based webm encodes! (got: \"{}\")")
        elif output_format == "mp4":
            self.video_codec = util.arg_default_or_validate_from_choices(video_codec, "libx264",
                "Only libx264 is supported for size-based mp4 encodes! (got: \"{}\")")
        elif output_format == "mkv":
            self.video_codec = util.arg_default_or_validate_from_choices(video_codec, "libvpx-vp9", "libx264",
                "Only libx264 and libvpx-vp9 are supported for size-based mkv encodes! (got: \"{}\")")
        else:
            assert False

        if output_format == "webm":
            self.audio_codec = util.arg_default_or_validate_from_choices(audio_codec, "libopus",
                "Only libopus is supported for size-based webm encodes! (got: \"{}\")")
        elif output_format in ("mp4", "mkv"):
            self.audio_codec = util.arg_default_or_validate_from_choices(audio_codec, "libopus", "aac",
                f"Only libopus and aac are supported for size-based {output_format} encodes! (got: \"{{}}\")")
        else:
            assert False

        self.encode_size = self.validate_int_and_or_float(encode_size, "Encode size", lower_bound=1, allowed_types=(int,))
        self.validate_default_set_audio_bitrate(audio_bitrate, self.audio_codec, size_based_encode_default_audio_bitrate_table)
        self.validate_and_set_output_width(output_width)

        self.fade_frame_duration = 150
        self.game_volume = game_volume
        self.music_volume = music_volume

        self.pix_fmt = pix_fmt
        if aspect_ratio_16_by_9 == "auto":
            aspect_ratio_16_by_9 = False
        self.aspect_ratio_16_by_9 = aspect_ratio_16_by_9

    @property
    def type(self):
        return ENCODE_TYPE_SIZE_BASED
