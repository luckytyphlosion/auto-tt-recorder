import import_ghost_to_save
import gen_gecko_codes
import create_lua_params
import subprocess
import pathlib
import time
import os
import configparser
import argparse
import sys
import mkw_filesys
import shutil
from contextlib import contextmanager
import re
import enumarg
from abc import ABC, abstractmethod
import dolphin_process

from stateclasses.speedometer import *

# def export_enums(enum):
#     globals().update(enum.__members__)
#     return enum
# 
# @export_enums
# class EncodePreset(Enum):
#     ENCODE_COPY = 0
#     ENCODE_x264_LIBOPUS = 1
#     ENCODE_x265_LIBOPUS = 2
#     ENCODE_x264_LIBOPUS_ADD_MUSIC_TRIM_LOADING = 3
#     ENCODE_x265_LIBOPUS_ADD_MUSIC_TRIM_LOADING = 4

ENCODE_COPY = 0
ENCODE_x264_LIBOPUS = 1
ENCODE_x265_LIBOPUS = 2
ENCODE_x264_LIBOPUS_ADD_MUSIC_TRIM_LOADING = 3
ENCODE_x265_LIBOPUS_ADD_MUSIC_TRIM_LOADING = 4
ENCODE_2PASS_VBR_WEBM = 5

TIMELINE_NO_ENCODE = 0
TIMELINE_FROM_TT_GHOST_SELECTION = 1
TIMELINE_FROM_WORLD_CHAMPION_SCREEN = 2
TIMELINE_FROM_TOP_10_LEADERBOARD = 3

MUSIC_NONE = 0
MUSIC_GAME_BGM = 1
MUSIC_CUSTOM_MUSIC = 2

class MusicOption:
    __slots__ = ("option", "music_filename")

    def __init__(self, option, music_filename=None):
        self.option = option
        self.music_filename = music_filename

music_option_bgm = MusicOption(MUSIC_BGM)
speedometer_option_none = SpeedometerOption(SOM_NONE)

audio_len_regex = re.compile(r"^size=N/A time=([0-9]{2}):([0-9]{2}):([0-9]{2}\.[0-9]{2})", flags=re.MULTILINE)
def get_dump_audio_len(ffmpeg_filename):
    # "ffmpeg -i dolphin/User/Dump/Audio/dspdump.wav -acodec copy -f rawaudio -y /dev/null 2>&1 | tr ^M '\n' | awk '/^  Duration:/ {print $2}' | tail -n 1"
    dspdump_ffmpeg_output = subprocess.check_output([ffmpeg_filename, "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-acodec", "copy", "-f", "null", "-"], stderr=subprocess.STDOUT).decode(encoding="ascii")
    audio_len_match_obj = audio_len_regex.search(dspdump_ffmpeg_output)
    if not audio_len_match_obj:
        raise RuntimeError("FFmpeg command did not return dspdump.wav audio duration!")
    audio_len_hours = int(audio_len_match_obj.group(1))
    audio_len_minutes = int(audio_len_match_obj.group(2))
    audio_len_seconds = float(audio_len_match_obj.group(3))
    audio_len = audio_len_hours * 3600 + audio_len_minutes * 60 + audio_len_seconds
    return audio_len

def gen_add_music_trim_loading_filter(ffmpeg_filename):
    output_params = {}

    with open("dolphin/output_params.txt", "r") as f:
        for line in f:
            if line.strip() == "":
                continue

            param_name, param_value = line.split(": ", maxsplit=1)
            output_params[param_name] = param_value.strip()

    frame_replay_starts = int(output_params["frameReplayStarts"])
    frame_recording_starts = int(output_params["frameRecordingStarts"])

    adelay_value = ((frame_replay_starts - frame_recording_starts) * 1000)/60
    audio_len = get_dump_audio_len(ffmpeg_filename)
    fade_duration = 2.5
    fade_start_time = audio_len - fade_duration
    trim_start = (frame_replay_starts - frame_recording_starts)/60

    return f"[2:a]adelay={adelay_value}|{adelay_value}[music_delayed];\
[1:a]volume=0.6[game_audio_voldown];\
[game_audio_voldown][music_delayed]amix=inputs=2:duration=first[audio_combined];\
[0:v]fade=type=out:duration={fade_duration}:start_time={fade_start_time},split[video_faded_out1][video_faded_out2];\
[audio_combined]afade=type=out:duration={fade_duration}:start_time={fade_start_time},asplit[audio_combined_faded_out1][audio_combined_faded_out2];\
[video_faded_out1]trim=end=3.1,setpts=PTS-STARTPTS[v0];\
[audio_combined_faded_out1]atrim=end=3.1,asetpts=PTS-STARTPTS[a0];\
[video_faded_out2]trim=start={trim_start},setpts=PTS-STARTPTS[v1];\
[audio_combined_faded_out2]atrim=start={trim_start},asetpts=PTS-STARTPTS[a1];\
[v0][a0][v1][a1]concat=n=2:v=1:a=1[v_almost_final][a];\
[v_almost_final]scale=2560:trunc(ow/a/2)*2:flags=bicubic[v]"

resolution_string_to_dolphin_enum = {
    "480p": "2",
    "720p": "4",
    "1080p": "6",
    "1440p": "7",
    "2k": "7",
    "2160p": "9",
    "4k": "9"
}

def record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=None, ffmpeg_filename="ffmpeg", szs_filename=None, hide_window=True, dolphin_resolution="480p", use_ffv1=use_ffv1, speedometer=None, music_option=None, timeline_settings=None):

    if speedometer is None:
        speedometer = speedometer_option_none
    if music_option is None:
        music_option = music_option_bgm
    if timeline_settings is None:
        # todo figure out how the "API" function will work with respect to validation
        timeline_settings = NoEncodeTimelineSettings("mkv")

    dolphin_resolution_as_enum = resolution_string_to_dolphin_enum.get(dolphin_resolution)
    if dolphin_resolution_as_enum is None:
        raise RuntimeError(f"Unknown Dolphin resolution \"{dolphin_resolution}\"!")

    rkg, rkg_comparison = import_ghost_to_save.import_ghost_to_save(
        "data/rksys.dat", rkg_file_main,
        "dolphin/User/Wii/title/00010004/524d4345/data/rksys.dat",
        "dolphin/User/Wii/shared2/menu/FaceLib/RFL_DB.dat",
        rkg_file_comparison
    )

    disable_game_bgm = music_option.option in (MUSIC_NONE, MUSIC_CUSTOM_MUSIC)

    params = gen_gecko_codes.create_gecko_code_params_from_central_args(rkg, speedometer, disable_game_bgm, timeline_settings)
    gen_gecko_codes.create_gecko_code_file("data/RMCE01_gecko_codes_template.ini", "dolphin/User/GameSettings/RMCE01.ini", params)
    create_lua_params.create_lua_params(rkg, rkg_comparison, "dolphin/lua_config.txt")
    mkw_filesys.replace_track(szs_filename, rkg)
    mkw_filesys.add_fancy_km_h_race_szs_if_necessary(speedometer)

    output_params_path = pathlib.Path("dolphin/output_params.txt")
    output_params_path.unlink(missing_ok=True)

    framedump_path = pathlib.Path("dolphin/User/Dump/Frames/framedump0.avi")
    framedump_path.unlink(missing_ok=True)

    create_dolphin_configs_if_not_exist()
    modify_dolphin_configs(resolution_as_dolphin_enum, use_ffv1)

    os.chdir("dolphin/")
    args = ["./DolphinR.exe", "-b", "-e", iso_filename]
    if hide_window:
        args.extend(("-hm", "-dr"))

    subprocess.run(args, check=True)
    #popen = subprocess.Popen(args)
    #popen = subprocess.Popen(("./DolphinR.exe", "-b", "-e", iso_filename))
    #kill_path = pathlib.Path("kill.txt")
    #while True:
    #    if kill_path.is_file():
    #        popen.terminate()
    #        # wsl memes
    #        subprocess.run(("taskkill.exe", "/f", "/im", "DolphinR.exe"))
    #        break
    #
    #    time.sleep(1)

    os.chdir("..")
    output_video_path = pathlib.Path(output_video_filename)
    output_video_path.parent.mkdir(parents=True, exist_ok=True)

    if encode_settings == ENCODE_COPY:
        subprocess.run(
            (ffmpeg_filename, "-y", "-i", "dolphin/User/Dump/Frames/framedump0.avi", "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-c", "copy", output_video_filename), check=True
        )
    elif encode_settings == ENCODE_x264_LIBOPUS:
        subprocess.run(
            (ffmpeg_filename, "-y", "-i", "dolphin/User/Dump/Frames/framedump0.avi", "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-c:v", "libx264", "-crf", "18", "-c:a", "libopus", "-b:a", "128000", output_video_filename), check=True
        )
    elif encode_settings == ENCODE_x265_LIBOPUS:
        subprocess.run(
            (ffmpeg_filename, "-y", "-i", "dolphin/User/Dump/Frames/framedump0.avi", "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-c:v", "libx265", "-crf", "18", "-c:a", "libopus", "-b:a", "128000", output_video_filename), check=True
        )
    elif encode_settings in (ENCODE_x264_LIBOPUS_ADD_MUSIC_TRIM_LOADING, ENCODE_x265_LIBOPUS_ADD_MUSIC_TRIM_LOADING):
        if encode_settings == ENCODE_x264_LIBOPUS_ADD_MUSIC_TRIM_LOADING:
            vcodec = "libx264"
        else:
            vcodec = "libx265"

        filter_params = gen_add_music_trim_loading_filter(ffmpeg_filename)
        subprocess.run(
            (ffmpeg_filename, "-y", "-i", "dolphin/user/dump/frames/framedump0.avi", "-i", "dolphin/user/dump/audio/dspdump.wav", "-i", music_filename, "-c:v", vcodec, "-crf", "18", "-pix_fmt", "yuv420p10le", "-c:a", "libopus", "-b:a", "128000", "-filter_complex", filter_params, "-map", "[v]", "-map", "[a]", output_video_filename), check=True
            #("ffmpeg", "-y", "-i", "dolphin/user/dump/frames/framedump0.avi", "-i", "dolphin/user/dump/audio/dspdump.wav", "-i", music_filename, "-c:v", vcodec, "-crf", "18", "-c:a", "libopus", "-b:a", "128000", "-filter_complex", filter_params, "-map", "[v]", "-map", "[a]", output_video_filename), check=True
        )
    elif encode_settings == ENCODE_2PASS_VBR_WEBM:
        # total bytes = 52428800
        # total bits = 52428800 * 8 = 419430400
        # total seconds = 102.654
        # total video bitrate = 419430400/102.654 = 4085865.1392054865
        # desired audio bitrate = 64000
        # total video bitrate - audio bitrate = 4085865.1392054865 - 64000 = 4020329.1392054865
        # with overhead factor = 4020329.1392054865 * 0.99 = 3980125.8478134316
        encode_size_bits = encode_size * 8
        run_len = get_dump_audio_len()
        avg_video_bitrate_as_str = str(int(0.99 * (encode_size_bits/run_len - encode_audio_bitrate)))
        subprocess.run(
            (ffmpeg_filename, "-i", "dolphin/user/dump/frames/framedump0.avi", "-c:v", "libvpx-vp9", "-b:v", avg_video_bitrate_as_str, "-row-mt", "1", "-threads", "8", "-pass", "1", "-f", "null", "/dev/null"), check=True
        )
        subprocess.run(
            (ffmpeg_filename, "-i", "dolphin/user/dump/frames/framedump0.avi", "-i", "dolphin/user/dump/audio/dspdump.wav", "-c:v", "libvpx-vp9", "-b:v", avg_video_bitrate_as_str, "-row-mt", "1", "-threads", "8", "-pass", "2", "-c:a", "libopus", "-b:a", str(encode_audio_bitrate), output_video_filename), check=True
        )

    else:
        raise RuntimeError(f"Invalid encode setting {encode_settings}!")

    print("Done!")

def copy_config_if_not_exist(base_config_filename, dest_config_filename):
    dest_config_filepath = pathlib.Path(dest_config_filename)
    if not dest_config_filepath.exists():
        dest_config_folderpath = dest_config_filepath.parent
        dest_config_folderpath.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base_config_filename, dest_config_filepath)

def create_dolphin_configs_if_not_exist():
    copy_config_if_not_exist("data/Dolphin.ini", "dolphin/User/Config/Dolphin.ini")
    copy_config_if_not_exist("data/GFX.ini", "dolphin/User/Config/GFX.ini")

@contextmanager
def open_config_for_modification(config_filename):
    try:
        with open(config_filename, "r") as f:
            config = configparser.ConfigParser(allow_no_value=True)
            config.read_file(f, config_filename)

        yield config
    finally:
        with open(config_filename, "w+") as f:
            config.write(f)

def modify_dolphin_configs(dolphin_resolution_as_enum, use_ffv1):
    dolphin_config_filename = "dolphin/User/Config/Dolphin.ini"
    dolphin_gfx_config_filename = "dolphin/User/Config/GFX.ini"

    with open_config_for_modification(dolphin_config_filename) as dolphin_config, open_config_for_modification(dolphin_gfx_config_filename) as dolphin_gfx_config:
        turn_off_dump_frames_audio(dolphin_config)
        set_variable_dolphin_config_options(dolphin_config, dolphin_gfx_config)

def turn_off_dump_frames_audio(dolphin_config):
    dolphin_config["Movie"]["DumpFrames"] = "False"
    dolphin_config["DSP"]["DumpAudio"] = "False"

# just use fixed values for now
def set_variable_dolphin_config_options(dolphin_config, dolphin_gfx_config, dolphin_resolution_as_enum, use_ffv1):
    dolphin_config["DSP"]["Volume"] = "0"
    dolphin_gfx_config["Settings"]["EFBScale"] = dolphin_resolution_as_enum
    dolphin_gfx_config["Settings"]["UseFFV1"] = str(use_ffv1)
    
#auto (window size) = 0
#auto (multiple of 640x528) = 1
#native = 2
#1.5x native = 3
#2x native = 4
#2.5x native = 5
#3x native = 6
#4x native = 7
#5x native = 8
#6x native = 9
#7x native = 10
#8x native = 11

valid_dolphin_resolution_scaling_factors = {
    1:   2,
    1.5: 3,
    2:   4,
    2.5: 5,
    3:   6,
    4:   7,
    5:   8,
    6:   9,
    7:  10,
    8:  11
}

timeline_enum_arg_table = enumarg.EnumArgTable({
    "noencode": TIMELINE_NO_ENCODE,
    "ghostselect": TIMELINE_FROM_TT_GHOST_SELECTION,
    "worldchamp": TIMELINE_FROM_WORLD_CHAMPION_SCREEN,
    "top10": TIMELINE_FROM_TOP_10_LEADERBOARD
})

#class NoEncodeTimelineArgs:
#    __slots__ = ("no_music

ENCODE_TYPE_NONE = -1
ENCODE_TYPE_CRF = 0
ENCODE_TYPE_SIZE_BASED = 1

encode_type_enum_arg_table = enumarg.EnumArgTable({
    "crf": ENCODE_TYPE_CRF,
    "size": ENCODE_TYPE_SIZE_BASED
})

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
    __slots__ = ("encode_settings",)

    def __init__(self, encode_settings):
        self.encode_settings = encode_settings

    @property
    def type(self):
        return TIMELINE_FROM_TT_GHOST_SELECTION

class EncodeSettings(ABC):
    __slots__ = ("output_format",)

    def __init__(self, output_format):
        self.output_format = output_format

    @property
    @abstractmethod
    def type(self):
        pass

class CrfEncodeSettings(EncodeSettings):
    __slots__ = ("crf", "h26x_preset", "video_codec", "audio_codec", "audio_bitrate")

    def __init__(self, output_format, crf, h26x_preset, video_codec, audio_codec, audio_bitrate):
        super().__init__(output_format)
        self.crf = crf
        self.h26x_preset = h26x_preset
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate

    @property
    def type(self):
        return ENCODE_TYPE_CRF

class SizeBasedEncodeSettings(EncodeSettings):
    __slots__ = ("video_codec", "audio_codec", "audio_bitrate", "encode_size")

    def __init__(self, output_format, video_codec, audio_codec, audio_bitrate, encode_size):
        super().__init__(output_format)
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.encode_size = encode_size

    @property
    def type(self):
        return ENCODE_TYPE_SIZE_BASED

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

crf_encode_default_audio_bitrate_table = {
    "libopus": "128k",
    "aac": "384k"
}

size_based_encode_default_audio_bitrate_table = {
    "libopus": "64k",
    "aac": "128k"
}

def arg_default_select(arg, default):
    return arg if arg is not None else default

empty_tuple = tuple()

def arg_default_or_validate_from_choices(arg, *choices_and_error_message):
    default = choices_and_error_message[0]
    choices = choices_and_error_message[:-1]
    error_message = choices_and_error_message[-1]

    if arg is None:
        arg = default
    elif arg not in choices:
        #assert len(choices) != 0
        #if len(choices) == 1:
        #    choices_str 
        raise RuntimeError(error_message.format(arg))

    return arg

def parse_audio_bitrate(audio_bitrate):
    try:
        if audio_bitrate[-1] == "k":
            audio_bitrate_as_int = int(audio_bitrate[:-1]) * 1000
        else:
            audio_bitrate_as_int = int(audio_bitrate)
    except (ValueError, IndexError) as e:
        raise RuntimeError(f"Invalid audio bitrate \"{audio_bitrate}\"!") from e

    return audio_bitrate_as_int

def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    # global args
    ap.add_argument("-i", "--main-ghost-filename", dest="input_ghost_filename", help="Filename of the main ghost to record.", required=True)
    ap.add_argument("-o", "--output-video-filename", dest="output_video_filename", help="Filename of the output recorded ghost. All possible allowed formats are mkv, webm, and mp4, but further restrictions apply. See the note on output formats.", required=True)
    ap.add_argument("-r", "--iso-filename", dest="iso_filename", help="Filename of the Mario Kart Wii ISO.", required=True)
    ap.add_argument("-c", "--comparison-ghost-filename", dest="comparison_ghost_filename", default=None, help="Filename of the comparison ghost.")
    ap.add_argument("-s", "--szs-filename", dest="szs_filename", default=None, help="Filename of the szs file corresponding to the ghost file. Omit this for a regular track (or if the track was already replaced in the ISO)")
    ap.add_argument("-kw", "--keep-window", dest="keep_window", action="store_true", default=False, help="By default, the Dolphin executable used to record the ghost is hidden to prevent accidental interaction with the window. Enabling this option will keep the window open, e.g. for debugging.")
    ap.add_argument("-t", "--timeline", dest="timeline", default="noencode", help="Choice of recording timeline to use. Default is noencode (stream copy, i.e. package the raw frame and audio dump into an mkv file).")
    ap.add_argument("-ff", "--ffmpeg-filename", dest="ffmpeg_filename", default="ffmpeg", help="Path to the ffmpeg executable to use. Default is ffmpeg (use system ffmpeg)")
    ap.add_argument("-dr", "--dolphin-resolution", dest="dolphin_resolution", default="480p", help="Internal resolution for Dolphin to render at. Possible options are 480p, 720p, 1080p, 1440p, and 2160p. Default is 480p (966x528)")
    ap.add_argument("-ffv1", "--use-ffv1", dest="use_ffv1", action="store_true", default=False, help="Whether to use the lossless ffv1 codec. Note that an ffv1 dump has the exact same quality as an uncompressed dump, i.e. they are exactly the same pixel-by-pixel.")
    ap.add_argument("-sm", "--speedometer", dest="speedometer", default="none", help="Enables speedometer and takes in an argument for the SOM display type. Possible values are fancy (left aligned, special km/h symbol using a custom Race.szs, looks bad at 480p, 0-1 decimal places allowed), regular (left aligned, \"plain-looking\" km/h symbol, does not require the full NAND code, usable at 480p, 0-2 decimal places allowed), standard (the \"original\" pretty speedometer, might help with code limit), none (do not include a speedometer). Default is none.")
    ap.add_argument("-smt", "--speedometer-metric", dest="speedometer_metric", default="engine", help="What metric of speed the speedometer reports. Possible options are engine for the speed which the vehicle engine is producing (ignoring external factors like Toad's Factory conveyers), and xyz, the norm of the current position minus the previous position. Default is engine.")
    ap.add_argument("-smd", "--speedometer-decimal-places", dest="speedometer_decimal_places", type=int, default=None, help="The number of decimal places in the speedometer. This option is ignored for the standard pretty speedometer. Default is 1 for the fancy speedometer and 2 for the regular speedometer.")

    # timeline no encode
    ap.add_argument("-nm", "--no-music", dest="no_music", action="store_true", default=False, help="Disable BGM and don't replace it with music.")

    # from tt ghost selection
    ap.add_argument("-m", "--music-filename", dest="music_filename", default="bgm", help="Filename of the music which will replace the regular BGM. Specifying bgm will keep the regular BGM. Specifying an empty string or None/none will disable music altogether. The default is bgm.")
    ap.add_argument("-ep", "--encode-preset", dest="encode_preset", default=None, help="Basic encode presets to use [TODO]")
    # youtube-fast-encode, youtube-optimize-size, discord-8mb, discord-50mb, discord-100mb
    ap.add_argument("-et", "--encode-type", dest="encode_type", default=None, help="Type of encoding to perform. Valid options are crf for a constant quality encode, and size for a constrained size based output. Pick crf if you're unsure (this is the default)")
    ap.add_argument("-crf", "--crf-value", dest="crf", type=float, default=18, help="Crf value to pass to ffmpeg. Valid range is 0-51. Default is 18. Lower values provide higher quality at the cost of file size.")
    ap.add_argument("-hp", "--h26x-preset", dest="h26x_preset", default="medium", help="H.26x preset option which will be passed to ffmpeg. Ignored for non-crf based encodes. Default is medium.")
    ap.add_argument("-c:v", "--video-codec", dest="video_codec", default=None, help="Video codec to encode the output video. Valid only for crf-based encodings. For crf-based encodes, valid options are libx264 and libx265, and the default is libx264. For constrained size-based encodes, valid options are libx264 and libvpx-vp9, and the default is libvpx-vp9. The difference between the two is that libx265 results in a smaller file size at the same quality at the cost of encoding time (unscientific tests suggest a speed decrease of 10x). libx265 will also not play in browsers or Discord. Other codecs (e.g. libvpx-vp9) may be supported in the future.")
    ap.add_argument("-c:a", "--audio-codec", dest="audio_codec", default=None, help="Audio codec to encode the audio of the output video. Valid options are aac and libopus. Opus results in higher quality and a lower file size than aac so it should be chosen for almost all use cases, the only reason that aac should be selected is if the desired output file is mp4 and maximizing compatibility across devices is desired. That being said, Opus in mp4 has been tested to work in VLC, PotPlayer, Discord client, Chrome, Firefox, and Discord mobile, and does not work with Windows Media Player. The default is aac for crf encoded mp4 files, libopus for size-based encoded mp4 files, and libopus for mkv and webm files.")
    #ap.add_argument("-f", "--output-format", dest="output_format", default=None, help="File format of the output video. Valid options are mp4, mkv, and webm. The default is mkv for crf-based encodes, and webm for size-based encodes. mkv supports many more codecs than mp4, and can be uploaded to YouTube, but cannot be played in by browsers or Discord. mp4 is supported almost universally but only accepts the libx264 and libx265 codecs from the codecs which auto-tt-recorder supports. webm is also widely supported but only accepts the libvpx-vp9 codec from the codecs supported by auto-tt-recorder. webm is not supported for crf-based encodes.")
    ap.add_argument("-es", "--encode-size", dest="encode_size", type=int, default=52428800, help="Max video size allowed. Currently only used for constrained size-based encodes (2-pass VBR) encoding. Default is 52428800 bytes (50MiB)")
    ap.add_argument("-b:a", "--audio-bitrate", dest="audio_bitrate", default=None, help="Audio bitrate for encodes. Higher bitrate means better audio quality (up to a certain point). Specified value can be an integer or an integer followed by k (multiplies by 1000). For crf-based encodes, the default is 128k for libopus, and 384k for aac. For constrained size-based encodes, the default is 64k for libopus, and 128k for aac.")

    args = ap.parse_args()

    #error_occurred = False

    rkg_file_main = args.input_ghost_filename
    output_video_filename = args.output_video_filename
    output_format_maybe_dot = pathlib.Path(output_video_filename).suffix
    if output_format_maybe_dot not in (".mp4", ".mkv", ".webm"):    
        raise RuntimeError("Output file does not have an accepted file extension!")
    output_format = output_format_maybe_dot[1:]
    
    iso_filename = args.iso_filename
    rkg_file_comparison = args.comparison_ghost_filename
    ffmpeg_filename = args.ffmpeg_filename
    szs_filename = args.szs_filename
    hide_window = not args.keep_window
    timeline = timeline_enum_arg_table.parse_enum_arg(args.timeline, "Unknown timeline \"{}\"!")

    if timeline == TIMELINE_NO_ENCODE:
        if output_format != "mkv":
            raise RuntimeError("Output file must be an .mkv file!")

        timeline_settings = NoEncodeTimelineSettings(output_format)

        if args.no_music:
            music_option = MusicOption(MUSIC_NONE)
        else:
            music_option = MusicOption(MUSIC_GAME_BGM)
    else:
        if args.music_filename in ("", "None", "none"):
            music_option = MusicOption(MUSIC_NONE)
        elif args.music_filename == "bgm":
            music_option = MusicOption(MUSIC_BGM)
        else:
            music_filepath = pathlib.Path(args.music_filename)
            if not music_filepath.exists():
                raise RuntimeError(f"Specified music filename \"{music_filepath}\" does not exist!")
            else:
                music_option = MusicOption(MUSIC_CUSTOM_MUSIC, args.music_filename)

        if args.encode_preset is not None:
            pass
        else:
            encode_type = encode_type_enum_arg_table.parse_enum_arg(args.encode_type, "Unknown encode type \"{}\"!")
            if encode_type == ENCODE_TYPE_CRF:
                if output_format == "webm":
                    raise RuntimeError("Webm is not supported with crf-based encodes!")
    
                crf = args.crf
                video_codec = arg_default_or_validate_from_choices(args.video_codec, "libx264", "libx265", "Unsupported crf-based codec \"{}\"!")

                h26x_preset = arg_default_or_validate_from_choices(args.h26x_preset, "medium", "ultrafast", "superfast", "veryfast", "faster", "fast", "slow", "slower", "veryslow", "placebo", "Unsupported H.26x preset \"{}\"!")

                if output_format == "mkv":
                    audio_codec = arg_default_select(args.audio_codec, "libopus")
                elif output_format == "mp4":
                    audio_codec = arg_default_select(args.audio_codec, "aac")
                else:
                    assert False

                if args.audio_bitrate is not None:
                    audio_bitrate = args.audio_bitrate
                else:
                    audio_bitrate = crf_encode_default_audio_bitrate_table[audio_codec]

                encode_settings = CrfEncodeSettings(output_format, crf, h26x_preset, video_codec, audio_codec, audio_bitrate)
            elif encode_type == ENCODE_TYPE_SIZE_BASED:
                video_codec = args.video_codec
                if output_format == "webm":
                    video_codec = arg_default_or_validate_from_choices(video_codec, "libvpx-vp9",
                        "Only libvpx-vp9 is supported for size-based webm encodes! (got: \"{}\")")
                elif output_format == "mp4":
                    video_codec = arg_default_or_validate_from_choices(video_codec, "libx264",
                        "Only libx264 is supported for size-based mp4 encodes! (got: \"{}\")")
                elif output_format == "mkv":
                    video_codec = arg_default_or_validate_from_choices(video_codec, "libvpx-vp9", "libx264",
                        "Only libx264 and libvpx-vp9 are supported for size-based mkv encodes! (got: \"{}\")")
    
                audio_codec = args.audio_codec
                if output_format == "webm":
                    audio_codec = arg_default_or_validate_from_choices(audio_codec, "libopus",
                        "Only libopus is supported for size-based webm encodes! (got: \"{}\")")
                elif output_format in ("mp4", "mkv"):
                    audio_codec = arg_default_or_validate_from_choices(audio_codec, "libopus", "aac",
                        f"Only libopus and aac are supported for size-based {output_format} encodes! (got: \"{{}}\")")

                encode_size = args.encode_size
    
                if args.audio_bitrate is not None:
                    audio_bitrate = args.audio_bitrate
                else:
                    audio_bitrate = size_based_encode_default_audio_bitrate_table[audio_codec]

                encode_settings = SizeBasedEncodeSettings(output_format, video_codec, audio_codec, audio_bitrate, encode_size)
            else:
                assert False

        if timeline == TIMELINE_FROM_TT_GHOST_SELECTION:
            timeline_settings = FromTTGhostSelectionTimelineSettings(encode_settings)
        else:
            raise RuntimeError(f"todo timeline {timeline}")

    dolphin_resolution = args.dolphin_resolution
    use_ffv1 = args.use_ffv1
    speedometer_style = som_enum_arg_table.parse_enum_arg(args.speedometer)
    if speedometer_style != SOM_NONE:
        speedometer_metric = som_metric_enum_arg_table.parse_enum_arg(speedometer_metric)
        if speedometer_style == SOM_FANCY_KM_H:
            speedometer_decimal_places = arg_default_or_validate_from_choices(args.speedometer_decimal_places,
                1, 0, "Only 0 or 1 decimal places are allowed for fancy km/h speedometer! (got: \"{}\")")
        elif speedometer_style == SOM_REGULAR_KM_H:
            speedometer_decimal_places = arg_default_or_validate_from_choices(args.speedometer_decimal_places,
                2, 0, 1, "Only 0 to 2 decimal places are allowed for regular km/h speedometer! (got: \"{}\")")
        else:
            speedometer_decimal_places = 2

        speedometer = SpeedometerOption(speedometer_style, speedometer_metric, speedometer_decimal_places)
    else:
        speedometer = SpeedometerOption(SOM_NONE)

    record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=rkg_file_comparison, ffmpeg_filename=ffmpeg_filename, szs_filename=szs_filename, hide_window=hide_window, dolphin_resolution=dolphin_resolution, use_ffv1=use_ffv1, speedometer=speedometer, music_option=music_option, timeline_settings=timeline_settings)

def main2():
    popen = subprocess.Popen(("./dolphin/Dolphin.exe",))
    print(f"popen.pid: {popen.pid}")
    #time.sleep(5)
    #popen.terminate()

def main3():
    print(gen_add_music_trim_loading_filter())

if __name__ == "__main__":
    main4()
