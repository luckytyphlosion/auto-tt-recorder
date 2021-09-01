import pathlib
from sortedcontainers import SortedList
import json
import chadsoft
from datetime import datetime, timezone
import collections
import dateutil
from lb_entry import LbEntryBuilder
import time
import record_ghost
import description
import sys

# input: vehicle_wr_entry
# returns: new last checked timestamp, new vehicle_wr_entry, rkg_data if ghost chosen

#UPDATE_USING_CUR_TIME = 0
#UPDATE_USING_LAST_CHECKED = 1
#UPDATE_

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

def find_ghost_to_record(yt_recorder_config, sorted_vehicle_wrs):
    num_tries = 0
    num_wrs = len(sorted_vehicle_wrs)
    vehicle_wr_entry_to_record = None
    downloaded_ghost_pathname = None
    vehicle_wr_lb = None

    while True:
        wr_index = sorted_vehicle_wrs.bisect_key_right(yt_recorder_config["last_recorded_run_timestamp"])
        vehicle_wr_entry = sorted_vehicle_wrs.pop(wr_index)

        result = check_suitable_ghost(vehicle_wr_entry)
        vehicle_wr_entry = result.vehicle_wr_entry

        if result.last_checked_timestamp is not None:
            vehicle_wr_entry["lastCheckedTimestamp"] = result.last_checked_timestamp

        if result.rkg_data is not None:
            print(f"Found suitable ghost to record! info: {vehicle_wr_entry['lbInfo']}")
            yt_recorder_config["last_recorded_run_timestamp"] = vehicle_wr_entry["dateSetTimestamp"]
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

    return yt_recorder_config, sorted_vehicle_wrs, vehicle_wr_entry_to_record, downloaded_ghost_pathname, vehicle_wr_lb

def main():
    yt_recorder_config_path = pathlib.Path("yt_recorder_config.json")
    if not yt_recorder_config_path.is_file():
        yt_recorder_config = {"last_recorded_run_timestamp": 0}
    else:
        with open(yt_recorder_config_path, "r") as f:
            yt_recorder_config = json.load(f)

    with open("sorted_vehicle_wrs.json", "r") as f:
        vehicle_wrs = json.load(f)

    sorted_vehicle_wrs = SortedList(vehicle_wrs, key=lambda x: x["lastCheckedTimestamp"])

    yt_recorder_config, sorted_vehicle_wrs, vehicle_wr_entry_to_record, downloaded_ghost_pathname, vehicle_wr_lb = find_ghost_to_record(yt_recorder_config, sorted_vehicle_wrs)

    iso_filename = "../../../RMCE01/RMCE01.iso"

    if vehicle_wr_entry_to_record is not None:
        output = ""
        output += f"{description.gen_title(vehicle_wr_entry_to_record)}\n=============================\n"
        output += f"{description.gen_description(vehicle_wr_entry_to_record, vehicle_wr_lb, downloaded_ghost_pathname)}\n"
        print(output)
        #return

        #rkg_file_main = downloaded_ghost_pathname
        #output_video_filename = vehicle_wr_entry_to_record["lbInfo"].replace(" ", "_") + ".mkv"
        #record_ghost.record_ghost(rkg_file_main, output_video_filename, iso_filename, rkg_file_comparison=None, hide_window=False, no_music=True)

    with open(yt_recorder_config_path, "w+") as f:
        json.dump(yt_recorder_config, f)

    sorted_vehicle_wrs_as_list = list(sorted_vehicle_wrs)

    with open("sorted_vehicle_wrs.json", "w+") as f:
        json.dump(sorted_vehicle_wrs_as_list, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
