import dateutil.parser
from datetime import datetime, timezone
import identifiers

class LbEntry:
    __slots__ = ("lb_data", "lb_entry", "ghost_href", "date_set_timestamp", "last_checked", "lb_info")

    def __init__(self):
        pass

    # three cases:
    # - lb with no ghosts, from initial parse
    # - lb with ghosts, from initial parse
    # - lb with ghosts, from periodic parse

    def add_track_id_category_id(self, track_id, category_id, track_name=None, category_name=None):
        self.track_id = track_id
        self.category_id = category_id

        if track_name is None:
            track_name = identifiers.get_track_name_from_track_id(track_id)

        if category_name is None:
            category_name = identifiers.category_names[category_id]

        self.track_name = track_name
        self.category_name = category_name

    def add_lb_data(self, lb_data):
        self.
        self.category_id = 
        self.lb_entry = lb_data["ghosts"][0]

    def 

def get_additional_info_from_wr_entry(wr_entry_data):
    wr_entry = wr_entry_data[0]
    ghost_href = wr_entry["_links"]["item"]["href"]
    date_set = dateutil.parser.isoparse(wr_entry["dateSet"])
    date_set_timestamp = date_set.timestamp()
    last_checked = date_set
    lb_info = f"{wr_entry['player']} beat {track_name} - {track_category} ({vehicle_name}) in {wr_entry['finishTimeSimple']}."

    return ghost_href, date_set_timestamp, last_checked, lb_info

def gen_wr_entry_for_empty_lb(track_name, track_category, 

def update_wr_entry_with_additional_info(wr_entry, lb_href, ghost_href, date_set_timestamp, last_checked, lb_info):
    vehicle_wr_entry_additional_info = {
        "lbHref": lb_href,
        "ghostHref": ghost_href,
        "dateSetTimestamp": date_set_timestamp,
        "lastCheckedTimestamp": last_checked.timestamp(),
        "recorded": False,
        "lbInfo": lb_info
    }

    vehicle_wr_entry.update(vehicle_wr_entry_additional_info)
