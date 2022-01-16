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

import pathlib
from sortedcontainers import SortedList
import json
import chadsoft
from datetime import datetime, timezone, timedelta
import collections
import dateutil
from lb_entry import LbEntryBuilder
import time
import record_ghost
import description
import sys
import math
import pytz
import youtube
import legacyrecords_staticconfig
import legacyrecords_music

from stateclasses.music_option_classes import *
from stateclasses.speedometer import *

CHADSOFT_READ_CACHE = True
CHADSOFT_WRITE_CACHE = True

# input: legacy_wr_entry
# returns: new last checked timestamp, new legacy_wr_entry, rkg_data if ghost chosen

#UPDATE_USING_CUR_TIME = 0
#UPDATE_USING_LAST_CHECKED = 1
#UPDATE_

OUTPUT_VIDEO_DIRECTORY = "yt_recorded_runs"

class CheckSuitableGhostResult:
    __slots__ = ("last_checked_timestamp", "legacy_wr_entry", "rkg_data", "legacy_wr_lb", "legacy_wr_lb_ignoring_vehicle_modifier")

    def __init__(self, last_checked_timestamp, legacy_wr_entry, rkg_data=None, legacy_wr_lb=None, legacy_wr_lb_ignoring_vehicle_modifier=None):
        self.last_checked_timestamp = last_checked_timestamp
        self.legacy_wr_entry = legacy_wr_entry
        self.rkg_data = rkg_data
        self.legacy_wr_lb = legacy_wr_lb
        self.legacy_wr_lb_ignoring_vehicle_modifier = legacy_wr_lb_ignoring_vehicle_modifier

def check_suitable_ghost(legacy_wr_entry):
    vehicle_modifier = legacy_wr_entry["vehicleModifier"]
    lb_href = legacy_wr_entry["lbHref"]
    date_set_timestamp = legacy_wr_entry["dateSetTimestamp"]
    updated_legacy_wr_lb_ignoring_vehicle_modifier = chadsoft.get_lb_from_href(lb_href, start=0, limit=2, times="wr", read_cache=CHADSOFT_READ_CACHE, write_cache=CHADSOFT_WRITE_CACHE)
    updated_legacy_wr_entry_data_ignoring_vehicle_modifier = updated_legacy_wr_lb_ignoring_vehicle_modifier["ghosts"]

    if len(updated_legacy_wr_entry_data_ignoring_vehicle_modifier) == 0:
        lb_entry_builder = LbEntryBuilder()
        lb_entry_builder.add_track_category_vehicle_modifier_extra_info_from_prev_lb_entry(legacy_wr_entry)
        lb_entry_builder.gen_no_wr_lb_info()
        print(lb_entry_builder.lb_info)
        return CheckSuitableGhostResult(time.time(), legacy_wr_entry)

    if vehicle_modifier is not None:
        if vehicle_modifier == "bikes":
            check_kart = False
        else:
            check_kart = True

        updated_legacy_wr_entry_ignoring_vehicle_modifier = updated_legacy_wr_entry_data_ignoring_vehicle_modifier[0]
        if identifiers.vehicle_id_to_is_kart[updated_legacy_wr_entry_ignoring_vehicle_modifier["vehicleId"]] == check_kart:
            print(f"Ghost is redundant! info: {legacy_wr_entry['lbInfo']}")
            return CheckSuitableGhostResult(time.time(), legacy_wr_entry)

        updated_legacy_wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=2, vehicle=vehicle_modifier, times="wr", read_cache=CHADSOFT_READ_CACHE, write_cache=CHADSOFT_WRITE_CACHE)
    else:
        updated_legacy_wr_lb = updated_legacy_wr_lb_ignoring_vehicle_modifier

    updated_legacy_wr_entry_data = updated_legacy_wr_lb["ghosts"]
    updated_legacy_wr_entry = updated_legacy_wr_entry_data[0]
    updated_legacy_wr_timestamp = dateutil.parser.isoparse(updated_legacy_wr_entry["dateSet"])

    if updated_legacy_wr_timestamp.timestamp() > date_set_timestamp:
        lb_entry_builder = LbEntryBuilder()
        lb_entry_builder.add_lb_entry(updated_legacy_wr_entry)
        lb_entry_builder.add_lb_href(lb_href)
        lb_entry_builder.add_track_category_vehicle_modifier_extra_info_from_prev_lb_entry(legacy_wr_entry)

        lb_entry_builder.gen_has_wr_lb_info()

        updated_legacy_wr_entry = lb_entry_builder.get_lb_entry_with_additional_info()
        print(f"Found new wr set on {updated_legacy_wr_entry['dateSet']}! info: {updated_legacy_wr_entry['lbInfo']}")
        return CheckSuitableGhostResult(None, updated_legacy_wr_entry)

    if legacy_wr_entry["recorded"]:
        print(f"Ghost already recorded! info: {legacy_wr_entry['lbInfo']}")
        return CheckSuitableGhostResult(time.time(), legacy_wr_entry)

    rkg_link = updated_legacy_wr_entry["href"]
    rkg_data, status_code = chadsoft.get(rkg_link, is_binary=True)
    if status_code == 404:
        print(f"Rkg file does not exist! info: {legacy_wr_entry['lbInfo']}")
        return CheckSuitableGhostResult(time.time(), legacy_wr_entry)

    # todo
    if legacy_wr_entry["playerId"] == "EE91F250E359EC6E":
        print("TODO!")
        sys.exit(1)

    return CheckSuitableGhostResult(time.time(), legacy_wr_entry, rkg_data, updated_legacy_wr_lb, updated_legacy_wr_lb_ignoring_vehicle_modifier)

def find_ghost_to_record(sorted_legacy_wrs):
    num_tries = 0
    num_wrs = len(sorted_legacy_wrs)
    legacy_wr_entry_to_record = None
    downloaded_ghost_pathname = None
    legacy_wr_lb = None

    while True:
        legacy_wr_entry = sorted_legacy_wrs.pop(0)

        result = check_suitable_ghost(legacy_wr_entry)
        legacy_wr_entry = result.legacy_wr_entry

        if result.last_checked_timestamp is not None:
            legacy_wr_entry["lastCheckedTimestamp"] = result.last_checked_timestamp

        if result.rkg_data is not None:
            print(f"Found suitable ghost to record! info: {legacy_wr_entry['lbInfo']}")
            downloaded_ghost_pathname = f"legacy_ghosts/{pathlib.Path(legacy_wr_entry['href']).name}"
            downloaded_ghost_path = pathlib.Path(downloaded_ghost_pathname)
            downloaded_ghost_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_wr_lb = result.legacy_wr_lb
            legacy_wr_lb_ignoring_vehicle_modifier = result.legacy_wr_lb_ignoring_vehicle_modifier
            with open(downloaded_ghost_pathname, "wb+") as f:
                f.write(result.rkg_data)
            legacy_wr_entry["recorded"] = True
            legacy_wr_entry_to_record = legacy_wr_entry

        sorted_legacy_wrs.add(legacy_wr_entry)

        if result.rkg_data is not None:
            break

        num_tries += 1
        if num_tries >= num_wrs:
            print("All wrs recorded!")
            break

    return sorted_legacy_wrs, legacy_wr_entry_to_record, downloaded_ghost_pathname, legacy_wr_lb, legacy_wr_lb_ignoring_vehicle_modifier

# 9 1 5 9 1 5
# 1 5 9 1 5 9

def ceil_dt(dt, delta):
    return datetime.min + math.ceil((dt - datetime.min) / delta) * delta

def gen_start_datetime(start_datetime_base=None):
    if start_datetime_base is None:
        start_datetime_base = datetime.utcnow()
    #start_datetime_base += timedelta(days=1)
    return ceil_dt(start_datetime_base, timedelta(hours=4)) + timedelta(hours=1)

def test_gen_start_datetime():
    start_datetime = gen_start_datetime(datetime(2021, 9, 2, 23, 6, 0))
    print(f"start_datetime: {start_datetime.isoformat()}")

def gen_schedule_datetime_str(start_datetime, schedule_index):
    if True:
        return pytz.utc.localize(start_datetime + timedelta(hours=4) * schedule_index).isoformat()
    else:
        return pytz.utc.localize(start_datetime + timedelta(hours=1) * schedule_index).isoformat()
        
SETTING_NUM_REMAINING_GHOSTS = 0
RECORDING_GHOSTS = 1
WAITING_FOR_UPLOAD = 2
UPDATING_UPLOADS = 3

def read_in_recorder_config():
    yt_recorder_config_path = pathlib.Path("yt_recorder_config.json")
    if not yt_recorder_config_path.is_file():
        yt_recorder_config = {
            "state": SETTING_NUM_REMAINING_GHOSTS,
            "base_schedule_index": 0,
            "start_datetime": gen_start_datetime().isoformat(),
            "num_remaining_ghosts": 0,
            "music_index": 0
        }
    else:
        with open(yt_recorder_config_path, "r") as f:
            yt_recorder_config = json.load(f)

    return yt_recorder_config

def update_recorder_config_state_and_serialize(yt_recorder_config, state):
    yt_recorder_config["state"] = state
    with open("yt_recorder_config.json", "w+") as f:
        json.dump(yt_recorder_config, f)

    return yt_recorder_config

def read_yt_update_infos():
    with open("yt_update_infos_cur.json", "r") as f:
        return json.load(f)

def serialize_yt_update_infos(yt_update_infos):
    with open("yt_update_infos_cur.json", "w+") as f:
        json.dump(yt_update_infos, f, indent=2, ensure_ascii=False)

#   - For 2160p, set this to 3840
#   - For 1440p, set this to 2560
#   - For 1080p, set this to 1920
#   - For 720p, set this to 1280
#   - For 480p, set this to 854

dolphin_resolution_to_output_width = {
    "2160p": 3840,
    "1440p": 2560,
    "1080p": 1920,
    "720p": 1280,
    "480p": 854
}

def record_legacy_wr_ghosts(num_ghosts, yt_recorder_config):
    with open("sorted_legacy_wrs.json", "r") as f:
        legacy_wrs = json.load(f)

    sorted_legacy_wrs = SortedList(legacy_wrs, key=lambda x: x["lastCheckedTimestamp"])

    yt_update_infos = read_yt_update_infos()
    start_datetime = datetime.fromisoformat(yt_recorder_config["start_datetime"])
    base_schedule_index = yt_recorder_config["base_schedule_index"]

    for i in range(yt_recorder_config["num_remaining_ghosts"]):
        sorted_legacy_wrs, legacy_wr_entry_to_record, downloaded_ghost_pathname, legacy_wr_lb, legacy_wr_lb_ignoring_vehicle_modifier = find_ghost_to_record(sorted_legacy_wrs)

        if legacy_wr_entry_to_record is not None:
            schedule_index = i + base_schedule_index

            music_info = legacyrecords_music.get_music(yt_recorder_config)

            yt_title = description.gen_title(legacy_wr_entry_to_record)
            yt_description = description.gen_description(legacy_wr_entry_to_record, legacy_wr_lb, downloaded_ghost_pathname, music_info)

            rkg_file_main = downloaded_ghost_pathname

            downloaded_ghost_path = pathlib.PurePosixPath(downloaded_ghost_pathname)
            downloaded_ghost_filepath = pathlib.PurePosixPath(downloaded_ghost_path.name)
            upload_title = f"api{downloaded_ghost_filepath.stem}"

            pathlib.Path(legacyrecords_staticconfig.output_video_directory).mkdir(parents=True, exist_ok=True)
            output_video_filename = f"{legacyrecords_staticconfig.output_video_directory}/{upload_title}.mp4"
            iso_filename = legacyrecords_staticconfig.iso_filename

            if legacy_wr_entry_to_record["vehicleModifier"] is not None:
                legacy_wr_entry_ignoring_vehicle_modifier = legacy_wr_lb_ignoring_vehicle_modifier["ghosts"][0]
                if legacy_wr_entry_ignoring_vehicle_modifier["playerId"] not in legacyrecords_staticconfig.censored_players:
                    rkg_link = legacy_wr_entry_ignoring_vehicle_modifier["href"]
                    rkg_data, status_code = chadsoft.get(rkg_link, is_binary=True)
                    if status_code != 404:
                        rkg_file_comparison = rkg_data
                    else:
                        print(f"Rkg file for ghost id {legacy_wr_entry_ignoring_vehicle_modifier['hash']} does not exist!")
                        rkg_file_comparison = None
                else:
                    rkg_file_comparison = None
            else:
                rkg_file_comparison = None

            # defer later
            szs_filename = None

            hide_window = False
            dolphin_resolution = legacyrecords_staticconfig.dolphin_resolution
            use_ffv1 = False
            speedometer = SpeedometerOption("regular", "xz", 2)
            encode_only = False

            if music_info is None:
                music_option = music_option_bgm
            else:
                music_option = MusicOption(MUSIC_CUSTOM_MUSIC, music_info.music_filename)

            dolphin_volume = 0
            track_name = legacy_wr_entry_to_record["trackName"]
            ending_message = "Video recorded by Auto TT Recorder."
            hq_textures = True
            on_200cc = legacy_wr_entry_to_record["200cc"]

            # FromTop10LeaderboardTimelineSettings(encode_settings, input_display, custom_top_10_and_ghost_description)

            # encode_settings = CrfEncodeSettings(
            # output_format, crf, h26x_preset, video_codec, audio_codec, audio_bitrate, output_width, pix_fmt, youtube_settings, game_volume, music_volume
            # )
            output_format = "mp4"
            crf = 18
            h26x_preset = "medium"
            video_codec = "libx265"
            audio_codec = "libopus"
            audio_bitrate = "128k"
            output_width = dolphin_resolution_to_output_width[dolphin_resolution]
            pix_fmt = "yuv420p10le"
            youtube_settings = True
            game_volume = 1.0
            music_volume = 1.0

            encode_settings = CrfEncodeSettings(
                output_format, crf, h26x_preset,
                video_codec, audio_codec, audio_bitrate,
                output_width, pix_fmt, youtube_settings,
                game_volume, music_volume
            )
            
            input_display = InputDisplay("gcn", False)

            # lazy
            html_page_lb_link = description.create_chadsoft_link_with_vehicle_modifier(legacy_wr_entry_to_record)

            track_name_and_version = create_track_name_and_version(legacy_wr_entry_to_record)
            lb_modifiers_str = description.create_lb_modifiers_str(legacy_wr_entry_to_record)

            custom_top_10_and_ghost_description = customtop10.CustomTop10AndGhostDescription.from_chadsoft(
                html_page_lb_link,
                "ww",
                f"{track_name_and_version} {lb_modifiers_str}CTGP Top 10",
                1,
                f"{lb_modifiers_str}CTGP Champion",
                legacyrecords_staticconfig.censored_players,
                CHADSOFT_READ_CACHE,
                CHADSOFT_WRITE_CACHE,
            )

            # now set szs_filename
            szs_filename = custom_top_10_and_ghost_description.get_szs(iso_filename)

            timeline_settings = FromTop10LeaderboardTimelineSettings(encode_settings, input_display, custom_top_10_and_ghost_description)

            record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=rkg_file_comparison, ffmpeg_filename="ffmpeg", ffprobe_filename="ffprobe", szs_filename=szs_filename, hide_window=hide_window, dolphin_resolution=dolphin_resolution, use_ffv1=use_ffv1, speedometer=speedometer, encode_only=encode_only, music_option=music_option, dolphin_volume=dolphin_volume, track_name=track_name, ending_message=ending_message, hq_textures=hq_textures, on_200cc=on_200cc, timeline_settings=timeline_settings)

            schedule_datetime_str = gen_schedule_datetime_str(start_datetime, schedule_index)
            yt_update_infos[upload_title] = {
                "yt_title": yt_title,
                "yt_description": yt_description,
                "schedule_datetime_str": schedule_datetime_str,
                #"track_id": legacy_wr_entry_to_record["trackId"],
                #"vehicle_id": legacy_wr_entry_to_record["vehicleId"]
            }

            yt_recorder_config["base_schedule_index"] += 1
            yt_recorder_config["num_remaining_ghosts"] -= 1
            if music_option is not None:
                yt_recorder_config["music_index"] += 1

            sorted_vehicle_wrs_as_list = list(sorted_legacy_wrs)

            with open("sorted_legacy_wrs.json", "w+") as f:
                json.dump(sorted_vehicle_wrs_as_list, f, indent=2, ensure_ascii=False)

            serialize_yt_update_infos(yt_update_infos)
            
            yt_recorder_config = update_recorder_config_state_and_serialize(yt_recorder_config, RECORDING_GHOSTS)
        else:
            yt_recorder_config["num_remaining_ghosts"] = 0
            break

    return update_recorder_config_state_and_serialize(yt_recorder_config, WAITING_FOR_UPLOAD)

def waiting_for_upload(yt_recorder_config):
    while True:
        s = input("Waiting for upload! Enter \"uploaded\" once uploads have started: ")
        if s == "uploaded":
            break

    #for f in pathlib.Path("yt_recorded_runs").glob("*"):
    #    if f.is_file():
    #        f.unlink()

    return update_recorder_config_state_and_serialize(yt_recorder_config, UPDATING_UPLOADS)

def record_and_update_uploads(num_ghosts):
    yt_recorder_config = read_in_recorder_config()

    if yt_recorder_config["state"] == SETTING_NUM_REMAINING_GHOSTS:
        yt_recorder_config["num_remaining_ghosts"] = num_ghosts
        serialize_yt_update_infos({})
        yt_recorder_config = update_recorder_config_state_and_serialize(yt_recorder_config, RECORDING_GHOSTS)
    if yt_recorder_config["state"] == RECORDING_GHOSTS:
        yt_recorder_config = record_legacy_wr_ghosts(num_ghosts, yt_recorder_config)
    if yt_recorder_config["state"] == WAITING_FOR_UPLOAD:
        yt_recorder_config = waiting_for_upload(yt_recorder_config)
    if yt_recorder_config["state"] == UPDATING_UPLOADS:
        print("Entering update_title_description_and_schedule!")
        yt_recorder_config = youtube.update_title_description_and_schedule(yt_recorder_config)

def record_vehicle_wr_ghosts_outer():
    while True:
        record_and_update_uploads(6)

def test_record_and_update_uploads():
    record_and_update_uploads(4)

def main():
    MODE = 0
    if MODE == 0:
        record_vehicle_wr_ghosts_outer()
    elif MODE == 1:
        test_gen_start_datetime()
    elif MODE == 2:
        test_record_and_update_uploads()
    else:
        print("No mode selected!")

if __name__ == "__main__":
    main()
