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

# input: vehicle_wr_entry
# returns: new last checked timestamp, new vehicle_wr_entry, rkg_data if ghost chosen

#UPDATE_USING_CUR_TIME = 0
#UPDATE_USING_LAST_CHECKED = 1
#UPDATE_

OUTPUT_VIDEO_DIRECTORY = "yt_recorded_runs"

class CheckSuitableGhostResult:
    __slots__ = ("last_checked_timestamp", "vehicle_wr_entry", "rkg_data", "vehicle_wr_lb")

    def __init__(self, last_checked_timestamp, vehicle_wr_entry, rkg_data=None, vehicle_wr_lb=None):
        self.last_checked_timestamp = last_checked_timestamp
        self.vehicle_wr_entry = vehicle_wr_entry
        self.rkg_data = rkg_data
        self.vehicle_wr_lb = vehicle_wr_lb

def check_suitable_ghost(vehicle_wr_entry):
    lb_href = vehicle_wr_entry["lbHref"]
    vehicle = vehicle_wr_entry["vehicleId"]
    date_set_timestamp = vehicle_wr_entry["dateSetTimestamp"]

    #excluded_vehicles = wr_and_kart_wr_vehicles.get(lb_href)
    #if excluded_vehicles is None:
    #    wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=1, override_cache=1, times="wr")
    #    wr_entry = wr_lb["ghosts"]
    #    wr_vehicle = wr_entry["vehicleId"]
    #    
    #    if vehicle == wr_vehicle:
    #        del sorted_vehicle_wrs[vehicle_wr_timestamp]
    #        sorted_vehicle_wrs[time.time()] = vehicle_wr_entry
    #        continue
    #
    #    
    #    kart_wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=1, vehicle="karts", times="wr", override_cache=1)
    #    kart_wr_entry = kart_wr_lb["ghosts"]
    #    kart_wr_vehicle = kart_wr_entry["vehicleId"]
    #        
    #else:

    wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=1, times="wr", override_cache=1)
    wr_entry_data = wr_lb["ghosts"]
    wr_vehicle = wr_entry_data[0]["vehicleId"]

    kart_wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=1, vehicle="karts", times="wr", override_cache=1)
    kart_wr_entry_data = kart_wr_lb["ghosts"]
    kart_wr_vehicle = kart_wr_entry_data[0]["vehicleId"]

    excluded_vehicles = {wr_vehicle, kart_wr_vehicle}

    if vehicle in excluded_vehicles:
        return CheckSuitableGhostResult(time.time(), vehicle_wr_entry)

    updated_vehicle_wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=2, vehicle=vehicle, times="wr", override_cache=1)
    updated_vehicle_wr_entry_data = updated_vehicle_wr_lb["ghosts"]
    if len(updated_vehicle_wr_entry_data) == 0:
        lb_entry_builder = LbEntryBuilder()
        lb_entry_builder.add_track_category_vehicle_id_from_prev_lb_entry(vehicle_wr_entry)
        lb_entry_builder.gen_no_wr_lb_info()
        print(lb_entry_builder.lb_info)
        return CheckSuitableGhostResult(time.time(), vehicle_wr_entry)

    updated_vehicle_wr_entry = updated_vehicle_wr_entry_data[0]
    updated_vehicle_wr_timestamp = dateutil.parser.isoparse(updated_vehicle_wr_entry["dateSet"])
    if updated_vehicle_wr_timestamp.timestamp() > date_set_timestamp:
        lb_entry_builder = LbEntryBuilder()
        lb_entry_builder.add_lb_entry(updated_vehicle_wr_entry)
        lb_entry_builder.add_lb_href(lb_href)
        lb_entry_builder.add_track_category_vehicle_id_from_prev_lb_entry(vehicle_wr_entry)

        lb_entry_builder.gen_has_wr_lb_info()

        updated_vehicle_wr_entry = lb_entry_builder.get_lb_entry_with_additional_info()
        print(f"Found new wr set on {updated_vehicle_wr_entry['dateSet']}! info: {updated_vehicle_wr_entry['lbInfo']}")
        return CheckSuitableGhostResult(None, updated_vehicle_wr_entry)

    if vehicle_wr_entry["recorded"]:
        print(f"Ghost already recorded! info: {vehicle_wr_entry['lbInfo']}")
        return CheckSuitableGhostResult(time.time(), vehicle_wr_entry)

    rkg_link = updated_vehicle_wr_entry["href"]
    #del sorted_vehicle_wrs[vehicle_wr_timestamp]
    #sorted_vehicle_wrs[updated_vehicle_wr_timestamp] = vehicle_wr_entry
    # something "recorded" = true?
    rkg_data, status_code = chadsoft.get(rkg_link, is_binary=True)
    if status_code == 404:
        print(f"Rkg file does not exist! info: {vehicle_wr_entry['lbInfo']}")
        return CheckSuitableGhostResult(time.time(), vehicle_wr_entry)

    # todo
    if vehicle_wr_entry["playerId"] == "EE91F250E359EC6E":
        print("TODO!")
        sys.exit(1)

    return CheckSuitableGhostResult(time.time(), vehicle_wr_entry, rkg_data, updated_vehicle_wr_lb)

def find_ghost_to_record(sorted_vehicle_wrs):
    num_tries = 0
    num_wrs = len(sorted_vehicle_wrs)
    vehicle_wr_entry_to_record = None
    downloaded_ghost_pathname = None
    vehicle_wr_lb = None

    while True:
        vehicle_wr_entry = sorted_vehicle_wrs.pop(0)

        result = check_suitable_ghost(vehicle_wr_entry)
        vehicle_wr_entry = result.vehicle_wr_entry

        if result.last_checked_timestamp is not None:
            vehicle_wr_entry["lastCheckedTimestamp"] = result.last_checked_timestamp

        if result.rkg_data is not None:
            print(f"Found suitable ghost to record! info: {vehicle_wr_entry['lbInfo']}")
            downloaded_ghost_pathname = pathlib.Path(vehicle_wr_entry["href"]).name
            vehicle_wr_lb = result.vehicle_wr_lb
            with open(downloaded_ghost_pathname, "wb+") as f:
                f.write(result.rkg_data)
            vehicle_wr_entry["recorded"] = True
            vehicle_wr_entry_to_record = vehicle_wr_entry

        sorted_vehicle_wrs.add(vehicle_wr_entry)

        if result.rkg_data is not None:
            break

        num_tries += 1
        if num_tries >= num_wrs:
            print("All wrs recorded!")
            break

    return sorted_vehicle_wrs, vehicle_wr_entry_to_record, downloaded_ghost_pathname, vehicle_wr_lb

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
            "add_in_music": False,
            "music_filename": None,
            "num_remaining_ghosts": 0
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

def record_vehicle_wr_ghosts(num_ghosts, yt_recorder_config):
    with open("sorted_vehicle_wrs.json", "r") as f:
        vehicle_wrs = json.load(f)

    sorted_vehicle_wrs = SortedList(vehicle_wrs, key=lambda x: x["lastCheckedTimestamp"])

    yt_update_infos = read_yt_update_infos()
    start_datetime = datetime.fromisoformat(yt_recorder_config["start_datetime"])
    base_schedule_index = yt_recorder_config["base_schedule_index"]

    for i in range(yt_recorder_config["num_remaining_ghosts"]):
        sorted_vehicle_wrs, vehicle_wr_entry_to_record, downloaded_ghost_pathname, vehicle_wr_lb = find_ghost_to_record(sorted_vehicle_wrs)

        iso_filename = "../../../RMCE01/RMCE01.iso"

        if vehicle_wr_entry_to_record is not None:
            schedule_index = i + base_schedule_index
            yt_title = description.gen_title(vehicle_wr_entry_to_record)
            yt_description = description.gen_description(vehicle_wr_entry_to_record, vehicle_wr_lb, downloaded_ghost_pathname)

            downloaded_ghost_path = pathlib.PurePosixPath(downloaded_ghost_pathname)
            upload_title = f"api{downloaded_ghost_path.stem}"
            #pathlib.Path(OUTPUT_VIDEO_DIRECTORY).mkdir(parents=True, exist_ok=True)
            output_video_filename = f"{OUTPUT_VIDEO_DIRECTORY}/{upload_title}.mkv"

            schedule_datetime_str = gen_schedule_datetime_str(start_datetime, schedule_index)
            yt_update_infos[upload_title] = {
                "yt_title": yt_title,
                "yt_description": yt_description,
                "schedule_datetime_str": schedule_datetime_str,
                "track_id": vehicle_wr_entry_to_record["trackId"],
                "vehicle_id": vehicle_wr_entry_to_record["vehicleId"]
            }

            rkg_file_main = downloaded_ghost_pathname

            if yt_recorder_config["add_in_music"]:
                no_music = True
                encode_settings = record_ghost.ENCODE_x265_LIBOPUS_ADD_MUSIC_TRIM_LOADING
                music_filename = yt_recorder_config["music_filename"]
            else:
                no_music = False
                encode_settings = record_ghost.ENCODE_COPY
                music_filename = None

            record_ghost.record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=None, hide_window=True, no_music=no_music, encode_settings=encode_settings, music_filename=music_filename)

            yt_recorder_config["base_schedule_index"] += 1
            yt_recorder_config["num_remaining_ghosts"] -= 1

            sorted_vehicle_wrs_as_list = list(sorted_vehicle_wrs)

            with open("sorted_vehicle_wrs.json", "w+") as f:
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
        yt_recorder_config = record_vehicle_wr_ghosts(num_ghosts, yt_recorder_config)
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
