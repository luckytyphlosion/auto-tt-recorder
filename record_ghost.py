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

def gen_add_music_trim_loading_filter():
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
    audio_len_as_str = subprocess.check_output(
        "ffmpeg -i dolphin/user/dump/audio/dspdump.wav -acodec copy -f rawaudio -y /dev/null 2>&1 | tr ^M '\n' | awk '/^  Duration:/ {print $2}' | tail -n 1", shell=True
    ).decode(encoding="ascii").replace(",\n", "")
    audio_len_hours_as_str, audio_len_minutes_as_str, audio_len_seconds_as_str = audio_len_as_str.split(":")
    audio_len_hours = int(audio_len_hours_as_str)
    audio_len_minutes = int(audio_len_minutes_as_str)
    audio_len_seconds = float(audio_len_seconds_as_str)
    audio_len = audio_len_hours * 3600 + audio_len_minutes * 60 + audio_len_seconds
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
[v_almost_final]scale=1280:trunc(ow/a/2)*2:flags=bicubic[v]"

def record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=None, hide_window=True, no_music=True, encode_settings=ENCODE_COPY, music_filename=None, szs_filename=None):
    rkg, rkg_comparison = import_ghost_to_save.import_ghost_to_save(
        "rksys.dat", rkg_file_main,
        "dolphin/User/Wii/title/00010004/524d4345/data/rksys.dat",
        "dolphin/User/Wii/shared2/menu/FaceLib/RFL_DB.dat",
        rkg_file_comparison
    )

    if music_filename is not None:
        no_music = False

    params = gen_gecko_codes.create_gecko_code_params_from_rkg(rkg, no_music)
    gen_gecko_codes.create_gecko_code_file("RMCE01_gecko_codes_template.ini", "dolphin/User/GameSettings/RMCE01.ini", params)
    create_lua_params.create_lua_params(rkg, rkg_comparison, "dolphin/lua_config.txt")
    mkw_filesys.replace_track(szs_filename, rkg)

    kill_path = pathlib.Path("dolphin/kill.txt")
    kill_path.unlink(missing_ok=True)

    output_params_path = pathlib.Path("dolphin/output_params.txt")
    output_params_path.unlink(missing_ok=True)

    framedump_path = pathlib.Path("dolphin/User/Dump/Frames/framedump0.avi")
    framedump_path.unlink(missing_ok=True)

    turn_off_dump_frames_audio()

    os.chdir("dolphin/")
    args = ["./DolphinR.exe", "-b", "-e", iso_filename]
    if hide_window:
        args.extend(("-hm", "-dr"))

    popen = subprocess.Popen(args)
    #popen = subprocess.Popen(("./DolphinR.exe", "-b", "-e", iso_filename))
    kill_path = pathlib.Path("kill.txt")
    while True:
        if kill_path.is_file():
            popen.terminate()
            # wsl memes
            subprocess.run(("taskkill.exe", "/f", "/im", "DolphinR.exe"))
            break

        time.sleep(1)

    os.chdir("..")
    output_video_path = pathlib.Path(output_video_filename)
    output_video_path.parent.mkdir(parents=True, exist_ok=True)

    if encode_settings == ENCODE_COPY:
        subprocess.run(
            ("ffmpeg", "-y", "-i", "dolphin/User/Dump/Frames/framedump0.avi", "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-c", "copy", output_video_filename), check=True
        )
    elif encode_settings == ENCODE_x264_LIBOPUS:
        subprocess.run(
            ("ffmpeg", "-y", "-i", "dolphin/User/Dump/Frames/framedump0.avi", "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-c:v", "libx264", "-crf", "18", "-c:a", "libopus", "-b:a", "128000", output_video_filename), check=True
        )
    elif encode_settings == ENCODE_x265_LIBOPUS:
        subprocess.run(
            ("ffmpeg", "-y", "-i", "dolphin/User/Dump/Frames/framedump0.avi", "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-c:v", "libx265", "-crf", "18", "-c:a", "libopus", "-b:a", "128000", output_video_filename), check=True
        )
    elif encode_settings in (ENCODE_x264_LIBOPUS_ADD_MUSIC_TRIM_LOADING, ENCODE_x265_LIBOPUS_ADD_MUSIC_TRIM_LOADING):
        if encode_settings == ENCODE_x264_LIBOPUS_ADD_MUSIC_TRIM_LOADING:
            vcodec = "libx264"
        else:
            vcodec = "libx265"

        filter_params = gen_add_music_trim_loading_filter()
        subprocess.run(
            ("ffmpeg", "-y", "-i", "dolphin/user/dump/frames/framedump0.avi", "-i", "dolphin/user/dump/audio/dspdump.wav", "-i", music_filename, "-c:v", vcodec, "-crf", "18", "-pix_fmt", "yuv420p10le", "-c:a", "libopus", "-b:a", "128000", "-filter_complex", filter_params, "-map", "[v]", "-map", "[a]", output_video_filename), check=True
            #("ffmpeg", "-y", "-i", "dolphin/user/dump/frames/framedump0.avi", "-i", "dolphin/user/dump/audio/dspdump.wav", "-i", music_filename, "-c:v", vcodec, "-crf", "18", "-c:a", "libopus", "-b:a", "128000", "-filter_complex", filter_params, "-map", "[v]", "-map", "[a]", output_video_filename), check=True
        )
    else:
        raise RuntimeError(f"Invalid encode setting {encode_settings}!")

    print("Done!")

def turn_off_dump_frames_audio():
    dolphin_config = "dolphin/User/Config/Dolphin.ini"

    with open(dolphin_config, "r") as f:
        config = configparser.ConfigParser(allow_no_value=True)
        config.read_file(f, dolphin_config)

    config["Movie"]["DumpFrames"] = False
    config["DSP"]["DumpAudio"] = False

    with open(dolphin_config, "w+") as f:
        config.write(f)

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
    ap.add_argument("-i", "--main-ghost-filename", dest="input_ghost_filename", help="Filename of the main ghost to record.")
    ap.add_argument("-o", "--output-video-filename", dest="output_video_filename", help="Filename of the output recorded ghost.")
    ap.add_argument("-r", "--iso-filename", dest="iso_filename", help="Filename of the Mario Kart Wii ISO.")
    ap.add_argument("-c", "--comparison-ghost-filename", dest="comparison_ghost_filename", default=None, help="Filename of the comparison ghost.")
    ap.add_argument("-kw", "--keep-window", dest="keep_window", action="store_true", default=False, help="By default, the Dolphin executable used to record the ghost is hidden to prevent accidental interaction with the window. Enabling this option will keep the window open, e.g. for debugging.")
    ap.add_argument("-e", "--encode-preset", dest="encode_preset", type=int, default=0, help="Integer value of the encoding preset to use. Default is 0 (stream copy, i.e. package the raw frame and audio dump into an mkv file).")
    ap.add_argument("-m", "--music-filename", dest="music_filename", default=None, help="Filename of the music which will replace the regular BGM. Omitting this option will keep the regular BGM. Specifying an empty string or None/none will disable music altogether.")
    ap.add_argument("-nm", "--no-music", dest="no_music", action="store_true", default=False, help="Disable BGM and don't replace it with music.")
    ap.add_argument("-s", "--szs-filename", dest="szs_filename", default=None, help="Filename of the szs file corresponding to the ghost file. Omit this for a regular track (or if the track was already replaced in the ISO)")
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

    if error_occurred:
        sys.exit(1)
    else:
        record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=rkg_file_comparison, hide_window=hide_window, no_music=no_music, encode_settings=encode_settings, music_filename=music_filename, szs_filename=szs_filename)

def main2():
    popen = subprocess.Popen(("./dolphin/Dolphin.exe",))
    print(f"popen.pid: {popen.pid}")
    #time.sleep(5)
    #popen.terminate()

def main3():
    print(gen_add_music_trim_loading_filter())

if __name__ == "__main__":
    main()
