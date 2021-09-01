import pathlib
from sortedcontainers import SortedList
import json
import chadsoft
from datetime import datetime, timezone
import collections
import dateutil

# input: vehicle_wr_entry
# returns: new last checked timestamp, new vehicle_wr_entry, rkg_data if ghost chosen

class CheckSuitableGhostResult:
    __slots__ = ("last_checked_timestamp", "vehicle_wr_entry", "rkg_data")

    def __init__(self, last_checked_timestamp, vehicle_wr_entry, rkg_data=None):
        self.last_checked_timestamp = last_checked_timestamp
        self.vehicle_wr_entry = vehicle_wr_entry
        self.rkg_data = rkg_data

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
    wr_entry = wr_lb["ghosts"]
    wr_vehicle = wr_entry["vehicleId"]

    kart_wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=1, vehicle="karts", times="wr", override_cache=1)
    kart_wr_entry = kart_wr_lb["ghosts"]
    kart_wr_vehicle = kart_wr_entry["vehicleId"]
    
    excluded_vehicles = {wr_vehicle, kart_wr_vehicle}

    if vehicle in excluded_vehicles:
        return CheckSuitableGhostResult(time.time(), vehicle_wr_entry)

    updated_vehicle_wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=1, vehicle=vehicle, times="wr", override_cache=1)
    updated_vehicle_wr_entry_data = updated_vehicle_wr_lb["ghosts"]
    if len(updated_vehicle_wr_entry_data) == 0:
        return CheckSuitableGhostResult(time.time(), vehicle_wr_entry)

    updated_vehicle_wr_entry = updated_vehicle_wr_entry_data[0]
    updated_vehicle_wr_timestamp = dateutil.parser.isoparse(updated_vehicle_wr_entry["dateSet"])
    if updated_vehicle_wr_timestamp > date_set_timestamp:
        return CheckSuitableGhostResult(
        del sorted_vehicle_wrs[vehicle_wr_timestamp]
        sorted_vehicle_wrs[updated_vehicle_wr_timestamp] = updated_vehicle_wr_entry
        continue
    else:
        rkg_link = updated_vehicle_wr_entry["href"]
        del sorted_vehicle_wrs[vehicle_wr_timestamp]
        sorted_vehicle_wrs[updated_vehicle_wr_timestamp] = vehicle_wr_entry
        # something "recorded" = true?
        rkg_data, status_code = chadsoft.get(rkg_link, is_binary=True)
        if status_code == 404:
            pass

        break

def main():
    yt_recorder_config_path = pathlib.Path("yt_recorder_config.json")
    if not yt_recorder_config_path.is_file():
        yt_recorder_config = {"last_recorded_run_timestamp": 0}
    else:
        with open(yt_recorder_config_path, "r") as f:
            yt_recorder_config = json.load(f)

    with open("sorted_vehicle_wrs.json", "r") as f:
        vehicle_wrs = json.load(f)

    sorted_vehicle_wrs = SortedList(vehicle_wrs, key=lambda x: x['lastCheckedTimestamp'])

    #wr_and_kart_wr_vehicles = {}

    while True:
        wr_index = sorted_vehicle_wrs.bisect_right(yt_recorder_config['last_recorded_run_timestamp'])
        vehicle_wr_entry = sorted_vehicle_wrs[wr_index]


    print(rkg_link)
    #    bisect_right

    #with open(yt_recorder_config_path, "w+") as f:

if __name__ == "__main__":
    main()
