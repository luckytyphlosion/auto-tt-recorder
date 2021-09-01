import json
import chadsoft
import identifiers
from sortedcontainers import SortedList
import dateutil.parser
import time
from datetime import datetime, timezone
import wr_entry

class LeaderboardId:
    __slots__ = ("track_id", "category_id")

    def __init__(self, track_id, category_id):
        self.track_id = track_id
        self.category_id = category_id

    def __key(self):
        return (self.track_id, self.category_id)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, LeaderboardId):
            return self.__key() == other.__key()
        return NotImplemented

def main():
    with open("original_lbs.json", "r") as f:
        original_lbs = json.load(f)

    output = ""
    lb_hrefs = {}

    for lb in original_lbs["leaderboards"]:
        category_id = lb.get("categoryId", -1)
        if category_id in (-1, 0, 2):
            lb_hrefs[LeaderboardId(lb["slotId"], category_id)] = lb["_links"]["item"]["href"]

    vehicle_wr_minlookup_entries = SortedList(key=lambda x: x['lastCheckedTimestamp'])

    for lb_id, lb_href in lb_hrefs.items():
        #wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=1, times="wr")
        #wr_entry_data = wr_lb["ghosts"]
        #wr_vehicle = wr_entry_data["vehicleId"]
        #
        #kart_wr_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=1, vehicle="karts", times="wr")
        #kart_wr_entry_data = kart_wr_lb["ghosts"]
        #kart_wr_vehicle = kart_wr_entry_data["vehicleId"]
        #
        #excluded_vehicles = {wr_vehicle, kart_wr_vehicle}
        track_name = get_track_name_from_track_id(lb_id.track_id)
        category_name = identifiers.category_names[lb_id.category_id]

        for i in range(identifiers.NUM_VEHICLES):
            #if i in excluded_vehicles:
            #    continue
            vehicle_name = identifiers.vehicle_names[i]
            vehicle_lb = chadsoft.get_lb_from_href(lb_href, start=0, limit=1, vehicle=i, times="wr")
            vehicle_entry_data = vehicle_lb["ghosts"]
            if len(vehicle_entry_data) == 0:
                vehicle_wr_entry = {}
                ghost_href = None
                last_checked = datetime.now(tz=timezone.utc)

                lb_info = f"No wr exists for {track_name} - {category_name} ({vehicle_name})!"
                print(lb_info)
                output += f"{lb_info}\n"
            else:
                vehicle_wr_entry = vehicle_entry_data[0]
                ghost_href, date_set_timestamp, last_checked, lb_info = wr_entry.get_additional_info_from_wr_entry(vehicle_wr_entry)
                print(lb_info)
                output += f"{lb_info}\n"

            wr_entry.update_wr_entry_with_additional_info(vehicle_wr_entry, lb_href, ghost_href, date_set_timestamp, last_checked, lb_info)
            vehicle_wr_minlookup_entries.add(vehicle_wr_entry)

    vehicle_wr_minlookup_entries_as_list = list(vehicle_wr_minlookup_entries)

    with open("sorted_vehicle_wrs.json", "w+", encoding="utf-8") as f:
        json.dump(vehicle_wr_minlookup_entries_as_list, f, indent=2, ensure_ascii=False)

    with open("lb_info_out.txt", "w+") as f:
        f.write(output)


if __name__ == "__main__":
    main()
