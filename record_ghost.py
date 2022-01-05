import import_ghost_to_save
import gen_gecko_codes
import create_lua_params
import subprocess
import pathlib
import time
import os
import configparser
import argparse
from enum import Enum
import sys
import mkw_filesys
import shutil
from contextlib import contextmanager
import re

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

def record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=None, hide_window=True, no_music=True, encode_settings=ENCODE_COPY, music_filename=None, szs_filename=None, encode_size=None, encode_audio_bitrate=None, ffmpeg_filename="ffmpeg"):
    rkg, rkg_comparison = import_ghost_to_save.import_ghost_to_save(
        "data/rksys.dat", rkg_file_main,
        "dolphin/User/Wii/title/00010004/524d4345/data/rksys.dat",
        "dolphin/User/Wii/shared2/menu/FaceLib/RFL_DB.dat",
        rkg_file_comparison
    )

    if music_filename is not None:
        no_music = True

    params = gen_gecko_codes.create_gecko_code_params_from_rkg(rkg, no_music)
    gen_gecko_codes.create_gecko_code_file("data/RMCE01_gecko_codes_template.ini", "dolphin/User/GameSettings/RMCE01.ini", params)
    create_lua_params.create_lua_params(rkg, rkg_comparison, "dolphin/lua_config.txt")
    mkw_filesys.replace_track(szs_filename, rkg)

    kill_path = pathlib.Path("dolphin/kill.txt")
    kill_path.unlink(missing_ok=True)

    output_params_path = pathlib.Path("dolphin/output_params.txt")
    output_params_path.unlink(missing_ok=True)

    framedump_path = pathlib.Path("dolphin/User/Dump/Frames/framedump0.avi")
    framedump_path.unlink(missing_ok=True)

    create_dolphin_configs_if_not_exist()
    modify_dolphin_configs()

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
        run_len = get_dump_audio_len(ffmpeg_filename)
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

def modify_dolphin_configs():
    dolphin_config_filename = "dolphin/User/Config/Dolphin.ini"
    dolphin_gfx_config_filename = "dolphin/User/Config/GFX.ini"

    with open_config_for_modification(dolphin_config_filename) as dolphin_config, open_config_for_modification(dolphin_gfx_config_filename) as dolphin_gfx_config:
        turn_off_dump_frames_audio(dolphin_config)
        set_variable_dolphin_config_options(dolphin_config, dolphin_gfx_config)

def turn_off_dump_frames_audio(dolphin_config):
    dolphin_config["Movie"]["DumpFrames"] = "False"
    dolphin_config["DSP"]["DumpAudio"] = "False"

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

# just use fixed values for now
def set_variable_dolphin_config_options(dolphin_config, dolphin_gfx_config):
    dolphin_config["DSP"]["Volume"] = "0"
    dolphin_gfx_config["Settings"]["EFBScale"] = "2"

def hardcoded_test():
    franz = "01m41s1006378 Franz.rkg"
    cole = "01m08s7732250 Cole.rkg"

    bye_shun = "01m40s2989711 Bye shun.rkg"
    bigmactroy = "01m45s4056658 bigmactroy.rkg"

    niyake = "00m15s9610732 Niyake.rkg"
    niyake2 = "00m16s1320374 Niyake2.rkg"

    rds_bob = "rds_super_blooper_bob.rkg"

    wgm_standard_kart_l = "wgm_standard_kart_l_1807FF33880AF428FF791A7DE57F96B40882.rkg"
    wgm_booster_seat = "wgm_booster_seat_BC757B2DD472668BB338883C7F47DA43E650.rkg"

    bryce = "00m20s3190366 MG   DKSC.rkg"

    rds_tiny_titan = "B1DA8CD9AC62E80B4C84B38474CD58052DAE.rkg"

    rkg_file_main = rds_tiny_titan
    output_video_filename = "rds_tiny_titan.mkv"
    iso_filename = "../../../RMCE01/RMCE01.iso"
    rkg_file_comparison = None
    hide_window = False
    no_music = True
    encode_settings = ENCODE_x264_LIBOPUS_ADD_MUSIC_TRIM_LOADING
    music_filename = "otis_mcdonald_intro_hq_complicate_ya_x2.wav"

    record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=rkg_file_comparison, hide_window=hide_window, no_music=no_music, encode_settings=encode_settings, music_filename=music_filename)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--main-ghost-filename", dest="input_ghost_filename", help="Filename of the main ghost to record.", required=True)
    ap.add_argument("-o", "--output-video-filename", dest="output_video_filename", help="Filename of the output recorded ghost.", required=True)
    ap.add_argument("-r", "--iso-filename", dest="iso_filename", help="Filename of the Mario Kart Wii ISO.", required=True)
    ap.add_argument("-c", "--comparison-ghost-filename", dest="comparison_ghost_filename", default=None, help="Filename of the comparison ghost.")
    ap.add_argument("-kw", "--keep-window", dest="keep_window", action="store_true", default=False, help="By default, the Dolphin executable used to record the ghost is hidden to prevent accidental interaction with the window. Enabling this option will keep the window open, e.g. for debugging.")
    ap.add_argument("-e", "--encode-preset", dest="encode_preset", type=int, default=0, help="Integer value of the encoding preset to use. Default is 0 (stream copy, i.e. package the raw frame and audio dump into an mkv file).")
    ap.add_argument("-m", "--music-filename", dest="music_filename", default=None, help="Filename of the music which will replace the regular BGM. Omitting this option will keep the regular BGM. Specifying an empty string or None/none will disable music altogether.")
    ap.add_argument("-nm", "--no-music", dest="no_music", action="store_true", default=False, help="Disable BGM and don't replace it with music.")
    ap.add_argument("-s", "--szs-filename", dest="szs_filename", default=None, help="Filename of the szs file corresponding to the ghost file. Omit this for a regular track (or if the track was already replaced in the ISO)")
    ap.add_argument("-es", "--encode-size", dest="encode_size", type=int, default=52428800, help="Max video size allowed. Currently only used for 2-pass VBR webm encoding. Default is 52428800 bytes (50MiB)")
    ap.add_argument("-eab", "--encode-audio-bitrate", dest="encode_audio_bitrate", type=int, default=64000, help="Audio bitrate for encodes. Currently only used for 2-pass VBR webm encoding. Default is 64000")
    ap.add_argument("-ff", "--ffmpeg-filename", dest="ffmpeg_filename", default="ffmpeg", help="Path to the ffmpeg executable to use. Default is ffmpeg (use system ffmpeg)")
    args = ap.parse_args()

    error_occurred = False

    rkg_file_main = args.input_ghost_filename
    # output filename must end in .mkv!
    output_video_filename = args.output_video_filename
    iso_filename = args.iso_filename
    rkg_file_comparison = args.comparison_ghost_filename
    hide_window = not args.keep_window
    encode_settings = args.encode_preset
    if encode_settings in (ENCODE_x264_LIBOPUS_ADD_MUSIC_TRIM_LOADING, ENCODE_x265_LIBOPUS_ADD_MUSIC_TRIM_LOADING):
        if args.music_filename is None:
            print("Error: Music filename not specified with encode setting which requires music.", file=sys.stderr)
            error_occurred = True
        else:
            if args.music_filename in ("", "None", "none"):
                music_filename = None
            else:
                music_filename = args.music_filename
    else:
        if args.music_filename is not None:
            print("Warning: Music filename specified with incompatible encode setting.", file=sys.stderr)
        music_filename = None

    no_music = (music_filename is not None) or args.no_music

    szs_filename = args.szs_filename
    encode_size = args.encode_size
    encode_audio_bitrate = args.encode_audio_bitrate
    ffmpeg_filename = args.ffmpeg_filename

    if error_occurred:
        sys.exit(1)
    else:
        record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=rkg_file_comparison, hide_window=hide_window, no_music=no_music, encode_settings=encode_settings, music_filename=music_filename, szs_filename=szs_filename, encode_size=encode_size, encode_audio_bitrate=encode_audio_bitrate, ffmpeg_filename=ffmpeg_filename)

def main2():
    popen = subprocess.Popen(("./dolphin/Dolphin.exe",))
    print(f"popen.pid: {popen.pid}")
    #time.sleep(5)
    #popen.terminate()

def main3():
    print(gen_add_music_trim_loading_filter())

if __name__ == "__main__":
    main()
