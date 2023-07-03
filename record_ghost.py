# Copyright (C) 2022 luckytyphlosion
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import subprocess
import pathlib
import time
import os
import configparser
import sys
import shutil
from contextlib import contextmanager
import re
import configargparse

import chadsoft
import customtop10
import enumarg
import util
import dolphin_process
import encode
import import_ghost_to_save
import gen_gecko_codes
import create_lua_params
import mkw_filesys
import msgeditor
import wiimm
import iso
import dir_config

from stateclasses.speedometer import *
from stateclasses.timeline_classes import *
from stateclasses.encode_classes import *
from stateclasses.music_option_classes import *
from stateclasses.input_display import *

from constants.lua_params import *

speedometer_option_none = SpeedometerOption(SOM_NONE)

resolution_string_to_dolphin_enum = {
    "480p": "2",
    "720p": "4",
    "1080p": "6",
    "1440p": "7",
    "2k": "7",
    "2160p": "9",
    "4k": "9"
}

timeline_setting_to_lua_mode = {
    TIMELINE_NO_ENCODE: LUA_MODE_RECORD_GHOST_ONLY,
    TIMELINE_FROM_TT_GHOST_SELECTION: LUA_MODE_RECORD_GHOST_FROM_TT_GHOST_SELECT,
    TIMELINE_FROM_TOP_10_LEADERBOARD: LUA_MODE_RECORD_GHOST_ONLY,
    TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN: LUA_MODE_RECORD_GHOST_ONLY,
    TIMELINE_GHOST_ONLY: LUA_MODE_RECORD_GHOST_ONLY    
}

CHECKPOINT_NONE = -1
CHECKPOINT_DUMPING_TOP_10 = 0
CHECKPOINT_DUMPING_TT_REPLAY = 1
CHECKPOINT_DUMPING_INPUT_DISPLAY = 2
CHECKPOINT_ENCODING = 3

def read_checkpoint(checkpoint_filename):
    if checkpoint_filename is not None:
        checkpoint_filepath = pathlib.Path(checkpoint_filename)
        if checkpoint_filepath.is_file():
            with open(checkpoint_filepath, "r") as f:
                checkpoint = int(f.read().strip())
        else:
            checkpoint = update_and_write_max_checkpoint(checkpoint_filename, CHECKPOINT_DUMPING_TOP_10, CHECKPOINT_DUMPING_TOP_10)
    else:
        checkpoint = CHECKPOINT_NONE

    return checkpoint

def update_and_write_max_checkpoint(checkpoint_filename, cur_checkpoint, new_checkpoint):
    if checkpoint_filename is not None:
        new_checkpoint = max(cur_checkpoint, new_checkpoint)
        checkpoint_as_str = str(new_checkpoint)
        with open(checkpoint_filename, "w+") as f:
            f.write(checkpoint_as_str)
    else:
        new_checkpoint = CHECKPOINT_NONE

    return new_checkpoint

def checkpoint_not_passed(cur_checkpoint, desired_checkpoint):
    if cur_checkpoint == CHECKPOINT_NONE:
        return True

    return cur_checkpoint <= desired_checkpoint

def checkpoint_done(checkpoint_filename):
    if checkpoint_filename is not None:
        checkpoint_filepath = pathlib.Path(checkpoint_filename)
        checkpoint_filepath.unlink(missing_ok=True)

def record_ghost(rkg_file_main, output_video_filename, mkw_iso, rkg_file_comparison=None, ffmpeg_filename="ffmpeg", ffprobe_filename="ffprobe", szs_filename=None, hide_window=True, dolphin_resolution="480p", use_ffv1=False, speedometer=None, encode_only=False, music_option=None, dolphin_volume=0, track_name=None, ending_message="Video recorded by Auto TT Recorder.", hq_textures=False, on_200cc=False, timeline_settings=None, checkpoint_filename=None, no_background_blur=False, no_bloom=False, extra_gecko_codes_filename=None, extra_hq_textures_folder=None, no_music_mkchannel=False, ending_delay=600):

    if szs_filename is not None:
        szs_filepath = pathlib.Path(szs_filename)
        if not szs_filepath.is_file():
            raise RuntimeError(f"Szs file \"{szs_filename}\" does not exist!")

        if wiimm.check_track_has_speedmod(szs_filename):
            if track_name is not None:
                track_name_in_error_msg = f" \"{track_name}\" "
            else:
                track_name_in_error_msg = ""

            raise RuntimeError(f"Track{track_name_in_error_msg}has speed modifier! (speed modified tracks are unsupported currently)")

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

    if timeline_settings.type in (TIMELINE_GHOST_ONLY, TIMELINE_FROM_TT_GHOST_SELECTION, TIMELINE_FROM_TOP_10_LEADERBOARD, TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN):
        timeline_settings.input_display.set_rkg_file_or_data(rkg_file_main)

    checkpoint = read_checkpoint(checkpoint_filename)

    mkw_filesys.add_extended_region_files(mkw_iso.region)
    mkw_filesys.copy_hq_textures_if_necessary(hq_textures, mkw_iso.region, extra_hq_textures_folder)

    if timeline_settings.type in (TIMELINE_FROM_TOP_10_LEADERBOARD, TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN) and checkpoint_not_passed(checkpoint, CHECKPOINT_DUMPING_TOP_10):
        rkg, rkg_comparison = import_ghost_to_save.import_ghost_to_save(
            f"data/{mkw_iso.region.title_id}/rksys.dat", rkg_file_main,
            f"{dir_config.dolphin_dirname}/User/Wii/title/00010004/{mkw_iso.region.hex_title_id}/data/rksys.dat",
            f"{dir_config.dolphin_dirname}/User/Wii/shared2/menu/FaceLib/RFL_DB.dat",
            rkg_file_comparison
        )

        disable_game_bgm_mk_channel = no_music_mkchannel or music_option.start_music_at_beginning

        params = gen_gecko_codes.create_gecko_code_params_for_custom_top_10(rkg, timeline_settings, track_name, mkw_iso.region, disable_game_bgm_mk_channel)
        gen_gecko_codes.create_gecko_code_file(f"data/{mkw_iso.region.title_id}_custom_top_10_gecko_codes_template.ini", f"{dir_config.dolphin_dirname}/User/GameSettings/{mkw_iso.region.title_id}.ini", params, None)
        top_10_or_mk_channel_lua_mode = LUA_MODE_RECORD_MK_CHANNEL_GHOST_SCREEN if timeline_settings.type == TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN else LUA_MODE_RECORD_TOP_10
        create_lua_params.create_lua_params_for_custom_top_10_or_mk_channel(f"{dir_config.dolphin_dirname}/lua_config.txt", top_10_or_mk_channel_lua_mode)

        if not encode_only:
            output_params_path = pathlib.Path(f"{dir_config.dolphin_dirname}/output_params.txt")
            output_params_path.unlink(missing_ok=True)

            framedump_path = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Dump/Frames/framedump0.avi")
            framedump_path.unlink(missing_ok=True)

            create_dolphin_configs_if_not_exist()
            modify_dolphin_configs(dolphin_resolution_as_enum, use_ffv1, dolphin_volume, hq_textures)

            dolphin_process.run_dolphin(mkw_iso, hide_window)

            pathlib.Path(f"{dir_config.dolphin_dirname}/User/Dump/Frames/framedump0.avi").replace(pathlib.Path(f"{dir_config.dolphin_dirname}/User/Dump/Frames/top10.avi"))
            pathlib.Path(f"{dir_config.dolphin_dirname}/User/Dump/Audio/dspdump.wav").replace(pathlib.Path(f"{dir_config.dolphin_dirname}/User/Dump/Audio/top10.wav"))

    checkpoint = update_and_write_max_checkpoint(checkpoint_filename, checkpoint, CHECKPOINT_DUMPING_TT_REPLAY)

    rkg, rkg_comparison = import_ghost_to_save.import_ghost_to_save(
        f"data/{mkw_iso.region.title_id}/rksys.dat", rkg_file_main,
        f"{dir_config.dolphin_dirname}/User/Wii/title/00010004/{mkw_iso.region.hex_title_id}/data/rksys.dat",
        f"{dir_config.dolphin_dirname}/User/Wii/shared2/menu/FaceLib/RFL_DB.dat",
        rkg_file_comparison
    )

    disable_game_bgm = music_option.option in (MUSIC_NONE, MUSIC_CUSTOM_MUSIC)

    params = gen_gecko_codes.create_gecko_code_params_from_central_args(rkg, speedometer, disable_game_bgm, timeline_settings, track_name, ending_message, on_200cc, mkw_iso.region, no_background_blur, no_bloom)
    gen_gecko_codes.create_gecko_code_file(f"data/{mkw_iso.region.title_id}_gecko_codes_template.ini", f"{dir_config.dolphin_dirname}/User/GameSettings/{mkw_iso.region.title_id}.ini", params, extra_gecko_codes_filename)
    lua_mode = timeline_setting_to_lua_mode[timeline_settings.type]

    create_lua_params.create_lua_params(rkg, rkg_comparison, f"{dir_config.dolphin_dirname}/lua_config.txt", lua_mode, ending_delay)
    mkw_filesys.replace_track(szs_filename, rkg)
    mkw_filesys.add_fancy_km_h_race_szs_if_necessary(speedometer, mkw_iso.region)

    if not encode_only and checkpoint_not_passed(checkpoint, CHECKPOINT_DUMPING_TT_REPLAY):
        output_params_path = pathlib.Path(f"{dir_config.dolphin_dirname}/output_params.txt")
        output_params_path.unlink(missing_ok=True)
    
        framedump_path = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Dump/Frames/framedump0.avi")
        framedump_path.unlink(missing_ok=True)
        if timeline_settings.type == TIMELINE_FROM_TT_GHOST_SELECTION:
            tt_ghost_select_framedump_path = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Dump/Frames/tt_ghost_select.avi")
            tt_ghost_select_framedump_path.unlink(missing_ok=True)

            tt_ghost_select_audiodump_path = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Dump/Audio/tt_ghost_select.wav")
            tt_ghost_select_audiodump_path.unlink(missing_ok=True)

        create_dolphin_configs_if_not_exist()
        modify_dolphin_configs(dolphin_resolution_as_enum, use_ffv1, dolphin_volume, hq_textures)

        dolphin_process.run_dolphin(mkw_iso, hide_window)

    # todo CHECKPOINT_DUMPING_INPUT_DISPLAY
    checkpoint = update_and_write_max_checkpoint(checkpoint_filename, checkpoint, CHECKPOINT_ENCODING)
    encode.encode_video(output_video_filename, ffmpeg_filename, ffprobe_filename, dolphin_resolution, music_option, timeline_settings)

    checkpoint_done(checkpoint_filename)
    print("Done!")

def copy_config_if_not_exist(base_config_filename, dest_config_filename):
    dest_config_filepath = pathlib.Path(dest_config_filename)
    if not dest_config_filepath.exists():
        dest_config_folderpath = dest_config_filepath.parent
        dest_config_folderpath.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base_config_filename, dest_config_filepath)

def create_dolphin_configs_if_not_exist():
    copy_config_if_not_exist("data/Dolphin.ini", f"{dir_config.dolphin_dirname}/User/Config/Dolphin.ini")
    copy_config_if_not_exist("data/GFX.ini", f"{dir_config.dolphin_dirname}/User/Config/GFX.ini")
    copy_config_if_not_exist("data/WiimoteNew.ini", f"{dir_config.dolphin_dirname}/User/Config/WiimoteNew.ini")

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

def modify_dolphin_configs(dolphin_resolution_as_enum, use_ffv1, dolphin_volume, hq_textures):
    dolphin_config_filename = f"{dir_config.dolphin_dirname}/User/Config/Dolphin.ini"
    dolphin_gfx_config_filename = f"{dir_config.dolphin_dirname}/User/Config/GFX.ini"
    dolphin_wiimote_config_filename = f"{dir_config.dolphin_dirname}/User/Config/WiimoteNew.ini"

    with open_config_for_modification(dolphin_config_filename) as dolphin_config, open_config_for_modification(dolphin_gfx_config_filename) as dolphin_gfx_config, open_config_for_modification(dolphin_wiimote_config_filename) as dolphin_wiimote_config:
        turn_off_dump_frames_audio(dolphin_config)
        disable_wiimotes(dolphin_wiimote_config)
        enable_pal60_mode(dolphin_config)
        set_variable_dolphin_config_options(dolphin_config, dolphin_gfx_config, dolphin_resolution_as_enum, use_ffv1, dolphin_volume, hq_textures)

def turn_off_dump_frames_audio(dolphin_config):
    dolphin_config["Movie"]["DumpFrames"] = "False"
    dolphin_config["DSP"]["DumpAudio"] = "False"

def disable_wiimotes(dolphin_wiimote_config):
    for section in ("Wiimote1", "Wiimote2", "Wiimote3", "Wiimote4"):
        dolphin_wiimote_config[section]["Source"] = "0"

def enable_pal60_mode(dolphin_config):
    dolphin_config["Display"]["PAL60"] = "True"

def set_variable_dolphin_config_options(dolphin_config, dolphin_gfx_config, dolphin_resolution_as_enum, use_ffv1, dolphin_volume, hq_textures):
    dolphin_config["DSP"]["Volume"] = str(dolphin_volume)
    dolphin_gfx_config["Settings"]["EFBScale"] = dolphin_resolution_as_enum
    dolphin_gfx_config["Settings"]["UseFFV1"] = str(use_ffv1)
    dolphin_gfx_config["Settings"]["HiresTextures"] = str(hq_textures)
    
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
    "mkchannel": TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN,
    "top10": TIMELINE_FROM_TOP_10_LEADERBOARD,
    "ghostonly": TIMELINE_GHOST_ONLY
})

#class NoEncodeTimelineArgs:
#    __slots__ = ("no_music

encode_type_enum_arg_table = enumarg.EnumArgTable({
    "crf": ENCODE_TYPE_CRF,
    "size": ENCODE_TYPE_SIZE_BASED
})

empty_tuple = tuple()

CC_UNKNOWN = 0
CC_150 = 1
CC_200 = 2

def main():
    ap = configargparse.ArgumentParser(
        allow_abbrev=False,
        config_file_parser_class=configargparse.YAMLConfigFileParser,
        config_file_open_func=lambda filename: open(
            filename, "r", encoding="utf-8"
        )
    )
    # global args
    ap.add_argument("-cfg", "--config", dest="config", default=None, is_config_file=True, help="Alternative config file to put in command line arguments. Arguments provided on the command line will override arguments provided in the config file, if specified.")
    ap.add_argument("-i", "--main-ghost-filename", dest="main_ghost_filename", help="Filename of the main ghost to record. Can be omitted if -ttc/--top-10-chadsoft is specified, if so then the ghost to record will be the one specified by -tth/--top-10-highlight", default=None)
    ap.add_argument("-o", "--output-video-filename", dest="output_video_filename", help="Filename of the output recorded ghost. All possible allowed formats are mkv, webm, and mp4, but further restrictions apply. See the note on output formats.", required=True)
    ap.add_argument("-r", "--iso-filename", dest="iso_filename", help="Filename of the Mario Kart Wii ISO or WBFS. Note that NKIT is not supported.", required=True)
    ap.add_argument("-c", "--comparison-ghost-filename", dest="comparison_ghost_filename", default=None, help="Filename of the comparison ghost. This cannot be specified with -ccg/--chadsoft-comparison-ghost-page.")
    ap.add_argument("-s", "--szs-filename", dest="szs_filename", default=None, help="Filename of the szs file corresponding to the ghost file. Omit this for a regular track (or if the track was already replaced in the ISO)")
    ap.add_argument("-kw", "--keep-window", dest="keep_window", action="store_true", default=False, help="By default, the Dolphin executable used to record the ghost is hidden to prevent accidental interaction with the window. Enabling this option will keep the window open, e.g. for debugging.")
    ap.add_argument("-t", "--timeline", dest="timeline", default="noencode", help="Choice of recording timeline to use. Possible options are \"noencode\" (race footage only, fastest to dump, just packages the raw frame and audio dump into an mkv file, no support for editing), \"ghostonly\" (race footage only, but supports all the editing options available for the race, e.g. fade in/out, input display), \"ghostselect\" (records starting from the Time Trial Ghost Select Screen), \"mkchannel\" (records from the Mario Kart Channel Race Ghost Screen), and \"top10\" (records a Custom Top 10 into the Mario Kart Channel Race Ghost Screen). Default is noencode.")
    ap.add_argument("-ff", "--ffmpeg-filename", dest="ffmpeg_filename", default="ffmpeg", help="Path to the ffmpeg executable to use. Default is ffmpeg (use system ffmpeg)")
    ap.add_argument("-fp", "--ffprobe-filename", dest="ffprobe_filename", default="ffprobe", help="Path to the ffprobe executable to use. Default is ffprobe (use system ffprobe).")
    ap.add_argument("-df", "--dolphin-folder", dest="dolphin_folder", default="dolphin", help="Folder of the specially built Dolphin emulator used by the program. Unless if you know what you're doing, you shouldn't need to specify this at all. Default is dolphin.")
    ap.add_argument("-sf", "--storage-folder", dest="storage_folder", default="storage", help="Folder for generated files meant for long-term storage. Currently, auto-add (related to wbz patching), wbz, and szs files are stored here. Default is storage.")
    ap.add_argument("-tf", "--temp-folder", dest="temp_folder", default="temp", help="Folder for miscellaneous temporary files. Currently, only the input display video is stored here. Default is temp.")
    ap.add_argument("-wf", "--wiimm-folder", dest="wiimm_folder", default="bin/wiimm", help="Folder containing the Mario Kart Wii related programs made by Wiimm. Currently, the program requires wit, wszst, and wkmpt. Default is bin/wiimm.")

    ap.add_argument("-dr", "--dolphin-resolution", dest="dolphin_resolution", default="480p", help="Internal resolution for Dolphin to render at. Possible options are 480p, 720p, 1080p, 1440p, and 2160p. Default is 480p (966x528)")
    ap.add_argument("-arsn", "--aspect-ratio-16-by-9", dest="aspect_ratio_16_by_9", default="auto", help="Whether to make the output video aspect ratio 16:9. Dolphin dumps at slightly less than 16:9, which causes black bars to appear in YouTube thumbnails and in full screen. Not recommended if uploading to Discord or recording for offline purposes. Default is true for crf-based encodes and false for size-based encodes.")
    ap.add_argument("-ffv1", "--use-ffv1", dest="use_ffv1", action="store_true", default=False, help="Whether to use the lossless ffv1 codec. Note that an ffv1 dump has the exact same quality as an uncompressed dump, i.e. they are exactly the same pixel-by-pixel.")
    ap.add_argument("-sm", "--speedometer", dest="speedometer", default="none", help="Enables speedometer and takes in an argument for the SOM display type. Possible values are fancy (left aligned, special km/h symbol using a custom Race.szs, looks bad at 480p, 0-1 decimal places allowed), regular (left aligned, \"plain-looking\" km/h symbol, does not require the full NAND code, usable at 480p, 0-2 decimal places allowed), standard (the \"original\" pretty speedometer, might help with code limit), none (do not include a speedometer). Default is none.")
    ap.add_argument("-smt", "--speedometer-metric", dest="speedometer_metric", default="engine", help="What metric of speed the speedometer reports. Possible options are engine for the speed which the vehicle engine is producing (ignoring external factors like Toad's Factory conveyers), xyz, the norm of the current position minus the previous position, and xz, which is like xyz except the vehicle's y position is not taken into account. Default is engine.")
    ap.add_argument("-smd", "--speedometer-decimal-places", dest="speedometer_decimal_places", type=int, default=None, help="The number of decimal places in the speedometer. This option is ignored for the standard pretty speedometer. Default is 1 for the fancy speedometer and 2 for the regular speedometer.")
    ap.add_argument("-eo", "--encode-only", dest="encode_only", action="store_true", default=False, help="Assume that all necessary frame dumps already exist, instead of running Dolphin to dump out frames. Useful for testing in case an error occurs through the encoding stage.")
    ap.add_argument("-dv", "--dolphin-volume", dest="dolphin_volume", type=int, default=0, help="Volume of the Dolphin executable. Only relevant for debugging, has no impact on audiodump volume.")
    ap.add_argument("-cg", "--chadsoft-ghost-page", dest="chadsoft_ghost_page", default=None, help="Link to the Chadsoft ghost page of the ghost to record. Specifying this will fill in the options for -i/--main-ghost-filename and -s/--szs-filename if they are not set (and the track to record is a custom track for szs filename). This option is not valid if the chosen timeline is top10 and -ttg/--top-10-gecko-code-filename is not specified.")
    ap.add_argument("-ccg", "--chadsoft-comparison-ghost-page", dest="chadsoft_comparison_ghost_page", default=None, help="Link to the Chadsoft ghost page of the ghost to compare against. This cannot be specified with -c/--comparison-ghost-filename.")
    ap.add_argument("-mga", "--main-ghost-auto", dest="main_ghost_auto", default=None, help="Smart option which is just -i/--main-ghost-filename and -cg/--chadsoft-ghost-page combined. Will automatically detect which option to use, based on the option input (i.e. chadsoft link will use -cg/--chadsoft-ghost-page, otherwise assumes -i/--main-ghost-filename). Cannot be used with -i/--main-ghost-filename and -cg/--chadsoft-ghost-page.")
    ap.add_argument("-cga", "--comparison-ghost-auto", dest="comparison_ghost_auto", default=None, help="Smart option which is just -c/--comparison-ghost-filename and -ccg/--chadsoft-comparison-ghost-page combined. Will automatically detect which option to use, based on the option input (i.e. chadsoft link will use -ccg/--chadsoft-ghost-page, otherwise assumes -c/--comparison-ghost-filename).")

    ap.add_argument("-tn", "--track-name", dest="track_name", default=None, help="The name of the track. This will affect the track name shown on the Ghost description page, seen in all timelines. Default is to use the track name of the Rkg track slot.")
    ap.add_argument("-em", "--ending-message", dest="ending_message", default="Video recorded by Auto TT Recorder", help="The ending message that shows on the bottom left after completing a time trial. Default is \"Video recorded by Auto TT Recorder\" (without quotes).")
    ap.add_argument("-crc", "--chadsoft-read-cache", dest="chadsoft_read_cache", action="store_true", default=False, help="Whether to read any data downloaded from Chadsoft and saved to a local cache folder. Cache purging is disabled if this option is false.")
    ap.add_argument("-cwc", "--chadsoft-write-cache", dest="chadsoft_write_cache", action="store_true", default=False, help="Whether to save any data downloaded from Chadsoft to a local cache folder to avoid needing to redownload the same files.")
    ap.add_argument("-cce", "--chadsoft-cache-expiry", dest="chadsoft_cache_expiry", default="24h", help="Duration until data downloaded from Chadsoft expires and is purged. Example formats: 1h23m46s, 24h, 3h30m, 1000 (seconds implied), 90m100s. The duration is applied on a per-file basis, so if the expiry time is 24h, each file will be deleted 24h after the specific file was downloaded. Note that the cache is purged when the program is run regardless of whether the purged files would have been requested or not. Default is 24h. Cache purging can be disabled if this option evaluates to 0 or if -crc/--chadsoft-read-cache is unspecified or false.")
    ap.add_argument("-ccf", "--chadsoft-cache-folder", dest="chadsoft_cache_folder", default="chadsoft_cached", help="Folder to temporarily store data downloaded from Chadsoft. Default folder is chadsoft_cached")
    ap.add_argument("-egc", "--extra-gecko-codes-filename", dest="extra_gecko_codes_filename", default=None, help="The filename of the file containing any extra gecko codes you want when recording. Not enabled during the top 10/mkchannel screen. It is your responsibility to make sure the gecko codes file is formatted correctly (this might change in the future) as well as to not specify any conflicting codes. Specifying the MSG Editor gecko code will probably cause issues as only one code can be used at a time.")
    ap.add_argument("-hqt", "--hq-textures", dest="hq_textures", action="store_true", default=False, help="Whether to enable HQ textures. Current built-in HQ textures supported are the Item Slot Mushrooms. Extra textures can be specified using -ehqt/--extra-hq-textures-folder. Looks bad at 480p.")
    ap.add_argument("-ehqt", "--extra-hq-textures-folder", dest="extra_hq_textures_folder", default=None, help="The folder containing any extra HQ textures you want. The program will check if the texture file has already been copied by comparing when each file was last modified. If the source and dest file have different timestamps, then it is copied over.")
    ap.add_argument("-o2", "--on-200cc", dest="on_200cc", action="store_true", default=False, help="Forces the use of 200cc, regardless if the ghost was set on 200cc or not. If neither -o2/--on-200cc nor -n2/--no-200cc is set, auto-tt-recorder will automatically detect 150cc or 200cc if -cg/--chadsoft-ghost-page or -ttc/--top-10-chadsoft is specified, otherwise it will assume 150cc.")
    ap.add_argument("-n2", "--no-200cc", dest="no_200cc", action="store_true", default=False, help="Forces the use of 150cc, regardless if the ghost was set on 150cc or not. If neither -o2/--on-200cc nor -n2/--no-200cc is set, auto-tt-recorder will automatically detect 150cc or 200cc if -cg/--chadsoft-ghost-page or -ttc/--top-10-chadsoft is specified, otherwise it will assume 150cc.")
    ap.add_argument("-nbb", "--no-background-blur", dest="no_background_blur", action="store_true", default=False, help="If enabled, on most tracks, the blurry/fuzzy background images are now sharp and clear.")
    ap.add_argument("-nb", "--no-bloom", dest="no_bloom", action="store_true", default=False, help="If enabled, disables the \"bloom\" effect (see https://en.wikipedia.org/wiki/Bloom_(shader_effect)). The effect is notable for not rendering properly on resolutions higher than 480p. Disabling bloom will cause graphics to look sharper however textures will have increased contrast which some might not like.")
    ap.add_argument("-ed", "--ending-delay", dest="ending_delay", type=int, default=600, help="How many frames to wait after the race ends. Default is 600.")

    # timeline no encode
    ap.add_argument("-nm", "--no-music", dest="no_music", action="store_true", default=False, help="Disable BGM and don't replace it with music.")

    # anything that requires encoding
    ap.add_argument("-m", "--music-filename", dest="music_filename", default="bgm", help="Filename of the music which will replace the regular BGM. Specifying bgm will keep the regular BGM. Specifying an empty string or None/none will disable music altogether. The default is bgm.")
    ap.add_argument("-smb", "--start-music-at-beginning", dest="start_music_at_beginning", action="store_true", default=False, help="Whether to start music at the start of the video instead of at the start of the time trial. Only applicable for mkchannel, top10, and ghostselect timelines. Default is false.")
    ap.add_argument("-fis", "--fade-in-at-start", dest="fade_in_at_start", action="store_true", default=False, help="Whether to fade in at the start of the video. Ignored for ghostonly and noencode timelines.")

    ap.add_argument("-ep", "--encode-preset", dest="encode_preset", default=None, help="Basic encode presets to use [TODO]")
    # youtube-fast-encode, youtube-optimize-size, discord-8mb, discord-50mb, discord-100mb
    ap.add_argument("-et", "--encode-type", dest="encode_type", default=None, help="Type of encoding to perform. Valid options are crf for a constant quality encode, and size for a constrained size based output. Pick crf if you're unsure (this is the default)")
    ap.add_argument("-crf", "--crf-value", dest="crf", type=float, default=18, help="Crf value to pass to ffmpeg. Valid range is 0-51. Default is 18. Lower values provide higher quality at the cost of file size.")
    ap.add_argument("-hp", "--h26x-preset", dest="h26x_preset", default="medium", help="H.26x preset option which will be passed to ffmpeg. Ignored for non-crf based encodes. Default is medium.")
    ap.add_argument("-c:v", "--video-codec", dest="video_codec", default=None, help="Video codec to encode the output video. For crf-based encodes, valid options are libx264 and libx265, and the default is libx264. For constrained size-based encodes, valid options are libx264 and libvpx-vp9, and the default is libvpx-vp9. The difference between the two is that libx265 results in a smaller file size at the same quality at the cost of encoding time (unscientific tests suggest a speed decrease of 10x). libx265 will also not play in browsers or Discord. Other codecs may be supported in the future.")
    ap.add_argument("-c:a", "--audio-codec", dest="audio_codec", default=None, help="Audio codec to encode the audio of the output video. Valid options are aac and libopus. Opus results in higher quality and a lower file size than aac so it should be chosen for almost all use cases, the only reason that aac should be selected is if the desired output file is mp4 and maximizing compatibility across devices is desired. That being said, Opus in mp4 has been tested to work in VLC, PotPlayer, Discord client, Chrome, Firefox, and Discord mobile, and does not work with Windows Media Player. The default is aac for crf encoded mp4 files, libopus for size-based encoded mp4 files, and libopus for mkv and webm files.")
    #ap.add_argument("-f", "--output-format", dest="output_format", default=None, help="File format of the output video. Valid options are mp4, mkv, and webm. The default is mkv for crf-based encodes, and webm for size-based encodes. mkv supports many more codecs than mp4, and can be uploaded to YouTube, but cannot be played in by browsers or Discord. mp4 is supported almost universally but only accepts the libx264 and libx265 codecs from the codecs which auto-tt-recorder supports. webm is also widely supported but only accepts the libvpx-vp9 codec from the codecs supported by auto-tt-recorder. webm is not supported for crf-based encodes.")
    ap.add_argument("-es", "--encode-size", dest="encode_size", type=int, default=52428800, help="Max video size allowed. Currently only used for constrained size-based encodes (2-pass VBR) encoding. Default is 52428800 bytes (50MiB)")
    ap.add_argument("-b:a", "--audio-bitrate", dest="audio_bitrate", default=None, help="Audio bitrate for encodes. Higher bitrate means better audio quality (up to a certain point). Specified value can be an integer or an integer followed by k (multiplies by 1000). For crf-based encodes, the default is 128k for libopus, and 384k for aac. For constrained size-based encodes, the default is 64k for libopus, and 128k for aac.")
    #width_height_group = ap.add_mutually_exclusive_group()
    #width_height_group.add_argument("-ow", "--output-width", dest="output_width", default=None, help="Width of the output video. Cannot be specified together with -oh/--output-height. If omitted, 
    ap.add_argument("-ow", "--output-width", dest="output_width", type=int, default=None, help="Width of the output video. If omitted, don't rescale the video at all.")
    ap.add_argument("-pix_fmt", "--pixel-format", dest="pix_fmt", default="yuv420p", help="Pixel format of the output video. Default is yuv420p. This input is not validated against!")
    ap.add_argument("-yt", "--youtube-settings", dest="youtube_settings", action="store_true", default=False, help="Add some encoding settings recommended by YouTube. This might increase quality on YouTube's end. Ignored for size based encodes.")
    ap.add_argument("-gv", "--game-volume", dest="game_volume", type=float, default=0.6, help="Multiplicative factor to control game volume in the output video (e.g. 0.5 to halve the game volume). Default is 0.6")
    ap.add_argument("-mv", "--music-volume", dest="music_volume", type=float, default=1.0, help="Multiplicative factor to control music volume in the output video (e.g. 0.5 to halve the music volume). Default is 1.0. Ignored if no music is specified.")
    ap.add_argument("-id", "--input-display", dest="input_display", default="none", help="Whether to include the input display in the output video. Currently supported options are auto, classic, gcn, nunchuck, and none (for no input display). auto will automatically try to detect the controller type to use for the input display, but this only works if a chadsoft ghost link or chadsoft leaderboard is provided. Additionally, the controller detected must not be the Wii Wheel as it is not implemented. Otherwise, auto will default to gcn. The rest of the controllers may be supported in the future.")
    ap.add_argument("-idd", "--input-display-dont-create", dest="input_display_dont_create", action="store_true", default=False, help="If enabled, assumes that the video file for the input display has already been created. Only relevant for debugging.")
    # specific to custom top 10
    ap.add_argument("-ttc", "--top-10-chadsoft", dest="top_10_chadsoft", default=None, help="Chadsoft link for the custom top 10 leaderboard. Current supported filters are the filters that Chadsoft supports, i.e. Region, Vehicles, and Times. This will also use the ghost specified by -tth/--top-10-highlight as the ghost to record if it is not already specified by -i/--main-ghost-filename, and the szs file to use if it is not already specified by -s/--szs-filename. This cannot be specified with -ttg/--top-10-gecko-code-filename or -cg/--chadsoft-ghost-page.")
    ap.add_argument("-ttl", "--top-10-location", dest="top_10_location", default="ww", help="What portion of the globe will show on the top 10 screen. Possible options are ww/worldwide for the 3d globe, or a location option from the allowed options at https://www.tt-rec.com/customtop10/. If -ttg/--top-10-gecko-code-filename is specified instead, then the possible options are ww/worldwide for the 3d globe, and anything else to show the regional globe.")
    ap.add_argument("-ttt", "--top-10-title", dest="top_10_title", default=None, help="The title that shows at the top of the Top 10 Leaderboard. Default is \"Worldwide Top 10\" for worldwide, and \"<Location> Top 10\" for the specified location. Ignored if -ttg/--top-10-gecko-code-filename is specified.")
    ap.add_argument("-tth", "--top-10-highlight", dest="top_10_highlight", type=int, default=1, help="The entry to highlight on the Top 10 Leaderboard. Must be in range 1-10, or -1 for no highlight. Default is 1. Ignored if -ttg/--top-10-gecko-code-filename is specified.")
    ap.add_argument("-ttb", "--top-10-censors", dest="top_10_censors", default=None, help="Chadsoft player IDs of the players to censor on the top 10 screen. The player ID can be retrieved from the chadsoft player page. Ignored if -ttg/--top-10-gecko-code-filename is specified.")
    ap.add_argument("-ttg", "--top-10-gecko-code-filename", dest="top_10_gecko_code_filename", default=None, help="The filename of the file containing the gecko code used to make a Custom Top 10. This cannot be specified with -ttc/--top-10-chadsoft. If your Top 10 is anything more complicated than a chadsoft leaderboard, then you're better off using https://www.tt-rec.com/customtop10/ to make your Custom Top 10.") 
    ap.add_argument("-mkd", "--mk-channel-ghost-description", dest="mk_channel_ghost_description", default=None, help="The description of the ghost which appears on the top left of the Mario Kart Channel Race Ghost Screen. Applies for timelines mkchannel and top10. Default is Ghost Data.")
    ap.add_argument("-nmmk", "--no-music-mkchannel", dest="no_music_mkchannel", action="store_true", default=False, help="Whether to disable music when on the Mario Kart Channel (for top10 or mkchannel timelines). Ignored if -smb/--start-music-at-beginning is true.")
    ap.add_argument("-uo", "--unbuffered-output", dest="unbuffered_output", action="store_true", default=False, help="Special option for use with auto-tt-recorder-gui. Forces stdout and stderr to flush at every newline.")
    #ap.add_argument("-sfu8", "--standard-streams-force-utf8", dest="standard_streams_force_utf8", action="store_true", default=False, help="Special option for use with auto-tt-recorder-gui. Forces stdout and stderr as .")

    args = ap.parse_args()

    if args.unbuffered_output:
        sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 1)
        sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 1)

    # Specifically for auto-tt-recorder-gui, but might help those with wonky terminals
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    dir_config.set_dirnames(args.dolphin_folder, args.storage_folder, args.temp_folder, args.wiimm_folder)

    # Cache purging
    if args.chadsoft_read_cache:
        chadsoft.purge_cache(args.chadsoft_cache_expiry, args.chadsoft_cache_folder)

    #error_occurred = False

    if args.on_200cc and args.no_200cc:
        raise RuntimeError("Only one of -o2/--on-200cc and -n2/--no-200cc can be specified!")
    elif args.on_200cc:
        cc_option = CC_200
    elif args.no_200cc:
        cc_option = CC_150
    else:
        cc_option = CC_UNKNOWN

    extra_gecko_codes_filename = args.extra_gecko_codes_filename

    if extra_gecko_codes_filename is not None and pathlib.Path(extra_gecko_codes_filename).suffix != ".ini":
        raise RuntimeError(f"Extra gecko codes filename must be .ini! (Got: {pathlib.Path(extra_gecko_codes_filename).suffix})")

    # backwards compatibility with previous yamls
    chadsoft_ghost_page_link = args.chadsoft_ghost_page
    # just for consistency
    main_ghost_filename = args.main_ghost_filename
    track_name = args.track_name

    if main_ghost_filename is None and args.top_10_chadsoft is None and chadsoft_ghost_page_link is None and args.main_ghost_auto is None:
        raise RuntimeError("Ghost file, chadsoft leaderboard, or chadsoft ghost page not specified!")

    if args.top_10_chadsoft is not None and chadsoft_ghost_page_link is not None and args.top_10_highlight != -1:
        raise RuntimeError("Only one of -ttc/--top-10-chadsoft and -cg/--chadsoft-ghost-page can be specified if -tth/--top-10-highlight is not -1!")

    if chadsoft_ghost_page_link is not None and main_ghost_filename is not None:
        raise RuntimeError("Only one of -i/--main-ghost-filename and -cg/--chadsoft-ghost-page can be specified!")

    cache_settings = chadsoft.CacheSettings(args.chadsoft_read_cache, args.chadsoft_write_cache, args.chadsoft_cache_folder)

    if args.main_ghost_auto is not None:
        if main_ghost_filename is not None or chadsoft_ghost_page_link is not None:
            raise RuntimeError("-mga/--main-ghost-auto cannot be specified with -i/--main-ghost-filename or -cg/--chadsoft-ghost-page!")

        if chadsoft.GhostPage.is_ghost_page_link(args.main_ghost_auto):
            chadsoft_ghost_page_link = args.main_ghost_auto
        else:
            main_ghost_filename = args.main_ghost_auto

    if chadsoft_ghost_page_link is not None:
        ghost_page = chadsoft.GhostPage(chadsoft_ghost_page_link, cache_settings)
        rkg_file_main = ghost_page.get_rkg()
        controller = ghost_page.get_controller()
        if track_name == "auto":
            track_name = ghost_page.get_track_name()
            if track_name is None:
                raise RuntimeError(f"Chadsoft ghost page {chadsoft_ghost_page_link} has no track name! (must specify track-name manually)")

        if cc_option == CC_UNKNOWN:
            cc_option = CC_200 if ghost_page.is_200cc() else CC_150
    else:
        ghost_page = None
        rkg_file_main = main_ghost_filename
        controller = CONTROLLER_UNKNOWN

    output_video_filename = args.output_video_filename
    output_format_maybe_dot = pathlib.Path(output_video_filename).suffix
    if output_format_maybe_dot not in (".mp4", ".mkv", ".webm"):    
        raise RuntimeError("Output file does not have an accepted file extension!")
    output_format = output_format_maybe_dot[1:]

    mkw_iso = iso.Iso(args.iso_filename)

    comparison_ghost_filename = args.comparison_ghost_filename
    chadsoft_comparison_ghost_page_link = args.chadsoft_comparison_ghost_page

    if comparison_ghost_filename is not None and chadsoft_comparison_ghost_page_link is not None:
        raise RuntimeError("Only one of -c/--comparison-ghost-filename and -ccg/--chadsoft-comparison-ghost-page is allowed!")

    if args.comparison_ghost_auto is not None:
        if comparison_ghost_filename is not None or chadsoft_comparison_ghost_page_link is not None:
            raise RuntimeError("-mga/--main-ghost-auto cannot be specified with -i/--main-ghost-filename or -cg/--chadsoft-ghost-page!")

        if chadsoft.GhostPage.is_ghost_page_link(args.comparison_ghost_auto):
            chadsoft_comparison_ghost_page_link = args.comparison_ghost_auto
        else:
            comparison_ghost_filename = args.comparison_ghost_auto

    if track_name == "auto" and chadsoft_ghost_page_link is None and chadsoft_comparison_ghost_page_link is None and args.top_10_chadsoft is None and args.szs_filename is not None:
        raise RuntimeError("Must specify one of a chadsoft ghost page, a chadsoft comparison ghost page, and a chadsoft top 10 leaderboard if -tn/--track-name is auto and -s/--szs-filename is specified!")

    if comparison_ghost_filename is not None:
        rkg_file_comparison = comparison_ghost_filename
    elif chadsoft_comparison_ghost_page_link is not None:
        comparison_ghost_page = chadsoft.GhostPage(chadsoft_comparison_ghost_page_link, cache_settings)
        rkg_file_comparison = comparison_ghost_page.get_rkg()
        if track_name == "auto":
            track_name = comparison_ghost_page.get_track_name()
            if track_name is None:
                raise RuntimeError(f"Chadsoft comparison ghost page {chadsoft_comparison_ghost_page_link} has no track name! (must specify track-name manually)")
    else:
        rkg_file_comparison = None

    ffmpeg_filename = args.ffmpeg_filename
    ffprobe_filename = args.ffprobe_filename
    if args.szs_filename is not None:
        szs_filename = args.szs_filename
    elif ghost_page is not None:
        szs_filename = ghost_page.get_szs(mkw_iso.iso_filename)
    else:
        szs_filename = None

    hide_window = not args.keep_window
    timeline = timeline_enum_arg_table.parse_enum_arg(args.timeline, "Unknown timeline \"{}\"!")
    ending_message = args.ending_message

    #if timeline == TIMELINE_FROM_TOP_10_LEADERBOARD:
    #    if args.top_10_chadsoft is not None and args.top_10_gecko_code_filename is not None:
    #        raise RuntimeError("Only one of -ttc/--top-10-chadsoft or -ttg/--top-10-gecko-code-filename is allowed!")

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
            music_option = MusicOption(MUSIC_GAME_BGM)
        else:
            music_filepath = pathlib.Path(args.music_filename)
            if not music_filepath.exists():
                raise RuntimeError(f"Specified music filename \"{music_filepath}\" does not exist!")
            else:
                start_music_at_beginning = args.start_music_at_beginning
                if timeline == TIMELINE_GHOST_ONLY:
                    start_music_at_beginning = False
                music_option = MusicOption(MUSIC_CUSTOM_MUSIC, args.music_filename, start_music_at_beginning)

        if args.encode_preset is not None:
            raise RuntimeError("-ep/--encode-preset is TODO!")
        else:
            encode_type = encode_type_enum_arg_table.parse_enum_arg(args.encode_type, "Unknown encode type \"{}\"!")
            aspect_ratio_16_by_9 = args.aspect_ratio_16_by_9
            if aspect_ratio_16_by_9 not in {"True", "False", "auto"}:
                raise RuntimeError(f"-arsn/--aspect-ratio-16-by-9 must be true, false, or auto! (got: {aspect_ratio_16_by_9})")

            fade_in_at_start = args.fade_in_at_start
            if timeline == "ghostonly":
                fade_in_at_start = False

            if encode_type == ENCODE_TYPE_CRF:
                encode_settings = CrfEncodeSettings(
                    output_format, args.crf, args.h26x_preset,
                    args.video_codec, args.audio_codec, args.audio_bitrate,
                    args.output_width, args.pix_fmt, args.youtube_settings,
                    args.game_volume, args.music_volume, aspect_ratio_16_by_9, args.fade_in_at_start
                )
            elif encode_type == ENCODE_TYPE_SIZE_BASED:
                encode_settings = SizeBasedEncodeSettings(
                    output_format, args.video_codec, args.audio_codec,
                    args.audio_bitrate, args.encode_size, args.output_width,
                    args.pix_fmt, args.game_volume, args.music_volume, aspect_ratio_16_by_9, args.fade_in_at_start
                )
            else:
                assert False


        if timeline in {TIMELINE_FROM_TT_GHOST_SELECTION, TIMELINE_GHOST_ONLY, TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN}:
            input_display = InputDisplay(args.input_display, controller, args.input_display_dont_create)

            if timeline == TIMELINE_FROM_TT_GHOST_SELECTION:
                timeline_settings = FromTTGhostSelectionTimelineSettings(encode_settings, input_display)
            elif timeline == TIMELINE_GHOST_ONLY:
                timeline_settings = GhostOnlyTimelineSettings(encode_settings, input_display)
            elif timeline == TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN:
                custom_top_10_and_ghost_description = customtop10.CustomTop10AndGhostDescription.from_mk_channel_ghost_select_only(
                    mkw_iso.region.name,
                    args.top_10_location,
                    args.mk_channel_ghost_description
                )
                timeline_settings = FromMKChannelGhostScreenTimelineSettings(encode_settings, input_display, custom_top_10_and_ghost_description)

        elif timeline == TIMELINE_FROM_TOP_10_LEADERBOARD:
            if args.top_10_chadsoft is not None and args.top_10_gecko_code_filename is not None:
                raise RuntimeError("Only one of -ttc/--top-10-chadsoft or -ttg/--top-10-gecko-code-filename is allowed!")
            elif args.top_10_chadsoft is not None:
                custom_top_10_and_ghost_description = customtop10.CustomTop10AndGhostDescription.from_chadsoft(
                    mkw_iso.region.name,
                    args.top_10_chadsoft,
                    args.top_10_location,
                    args.top_10_title,
                    args.top_10_highlight,
                    args.mk_channel_ghost_description,
                    args.top_10_censors,
                    cache_settings
                )

                if rkg_file_main is None:
                    rkg_file_main = custom_top_10_and_ghost_description.get_rkg_file_main()
                if szs_filename is None:
                    szs_filename = custom_top_10_and_ghost_description.get_szs(mkw_iso.iso_filename)
                if cc_option == CC_UNKNOWN:
                    cc_option = CC_200 if custom_top_10_and_ghost_description.is_200cc() else CC_150
                if controller == CONTROLLER_UNKNOWN:
                    controller = custom_top_10_and_ghost_description.get_controller(controller)
                if track_name == "auto":
                    track_name = custom_top_10_and_ghost_description.get_track_name()
                    if track_name is None:
                        raise RuntimeError(f"Chadsoft leaderboard {args.top_10_chadsoft} has no track name! (must specify track-name manually)")
                input_display = InputDisplay(args.input_display, controller, args.input_display_dont_create)

            elif args.top_10_gecko_code_filename is not None:
                input_display = InputDisplay(args.input_display, controller, args.input_display_dont_create)

                custom_top_10_and_ghost_description = customtop10.CustomTop10AndGhostDescription.from_gecko_code_filename(
                    args.top_10_gecko_code_filename,
                    args.top_10_location,
                    args.mk_channel_ghost_description
                )
            else:
                raise RuntimeError("One of -ttc/--top-10-chadsoft or -ttg/--top-10-gecko-code-filename must be specified!")

            timeline_settings = FromTop10LeaderboardTimelineSettings(encode_settings, input_display, custom_top_10_and_ghost_description)
        else:
            raise RuntimeError(f"todo timeline {timeline}")

    dolphin_resolution = args.dolphin_resolution
    use_ffv1 = args.use_ffv1
    speedometer = SpeedometerOption(args.speedometer, args.speedometer_metric, args.speedometer_decimal_places)

    encode_only = args.encode_only
    dolphin_volume = args.dolphin_volume
    hq_textures = args.hq_textures

    if cc_option in (CC_150, CC_UNKNOWN):
        on_200cc = False
    else:
        on_200cc = True

    # assume original track at this point
    if track_name == "auto":
        if szs_filename is None:
            track_name = None
        else:
            raise RuntimeError("Could not automatically get track name! (must specify manually)")

    record_ghost(rkg_file_main, output_video_filename, mkw_iso, rkg_file_comparison=rkg_file_comparison, ffmpeg_filename=ffmpeg_filename, ffprobe_filename=ffprobe_filename, szs_filename=szs_filename, hide_window=hide_window, dolphin_resolution=dolphin_resolution, use_ffv1=use_ffv1, speedometer=speedometer, encode_only=encode_only, music_option=music_option, dolphin_volume=dolphin_volume, track_name=track_name, ending_message=ending_message, hq_textures=hq_textures, on_200cc=on_200cc, timeline_settings=timeline_settings, no_background_blur=args.no_background_blur, no_bloom=args.no_bloom, extra_gecko_codes_filename=extra_gecko_codes_filename, extra_hq_textures_folder=args.extra_hq_textures_folder, no_music_mkchannel=args.no_music_mkchannel, ending_delay=args.ending_delay)

def main2():
    popen = subprocess.Popen(("./dolphin/Dolphin.exe",))
    print(f"popen.pid: {popen.pid}")
    #time.sleep(5)
    #popen.terminate()

def main3():
    print(gen_add_music_trim_loading_filter())

if __name__ == "__main__":
    main()
