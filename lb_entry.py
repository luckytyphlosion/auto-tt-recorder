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

import dateutil.parser
from datetime import datetime, timezone
import identifiers

class LbEntryBuilder:
    __slots__ = ("track_id", "category_id", "vehicle_id",
        "track_name", "category_name", "vehicle_name",
        "lb_href", "lb_data", "lb_entry", "ghost_href", "date_set_timestamp", "last_checked", "lb_info")

    def __init__(self):
        self.track_id = None
        self.category_id = None
        self.vehicle_id = None
        self.track_name = None
        self.category_name = None
        self.vehicle_name = None
        self.lb_href = None
        self.lb_data = None        
        self.lb_entry = {}
        self.ghost_href = None
        self.date_set_timestamp = None
        self.last_checked = None
        self.lb_info = None

    # three cases:
    # - lb with no ghosts, from initial parse
    # - lb with ghosts, from initial parse
    # - lb with ghosts, from periodic parse

    def add_track_category_vehicle_id(self, track_id, category_id, vehicle_id, track_name=None, category_name=None):
        self.track_id = track_id
        self.category_id = category_id
        self.vehicle_id = vehicle_id

        if track_name is None:
            track_name = identifiers.get_track_name_from_track_id(track_id)

        if category_name is None:
            category_name = identifiers.category_names[category_id]

        self.track_name = track_name
        self.category_name = category_name
        self.vehicle_name = identifiers.vehicle_names[vehicle_id]

    def add_track_category_vehicle_id_from_prev_lb_entry(self, prev_lb_entry):
        self.add_track_category_vehicle_id(
            prev_lb_entry["trackId"],
            prev_lb_entry["categoryId"],
            prev_lb_entry["vehicleId"],
            prev_lb_entry["trackName"],
            prev_lb_entry["categoryName"]
        )

    def add_ghost_href_last_checked_date_set_timestamp(self, ghost_href, last_checked, date_set_timestamp):
        self.ghost_href = ghost_href
        self.last_checked = last_checked
        self.date_set_timestamp = date_set_timestamp

    def add_lb_href(self, lb_href):
        self.lb_href = lb_href

    def add_lb_entry(self, lb_entry):
        self.lb_entry = lb_entry
        self.ghost_href = lb_entry["_links"]["item"]["href"]
        date_set = dateutil.parser.isoparse(lb_entry["dateSet"])
        self.date_set_timestamp = date_set.timestamp()
        self.last_checked = date_set

    #def add_lb_data(self, lb_data):
    #    self.lb_entry = lb_data["ghosts"][0]
    #    self.
    #
    #def add_lb_entry(

    def gen_no_wr_lb_info(self):
        self.lb_info = f"No wr exists for {self.track_name} - {self.category_name} ({self.vehicle_name})!"

    def gen_has_wr_lb_info(self):
        self.lb_info = f"{self.lb_entry['player']} beat {self.track_name} - {self.category_name} ({self.vehicle_name}) in {self.lb_entry['finishTimeSimple']}."

    def get_lb_entry_with_additional_info(self):
        if self.lb_href is None:
            raise RuntimeError("Missing lb_href!")

        if self.last_checked is None:
            raise RuntimeError("Missing last_checked!")

        if self.track_id is None:
            raise RuntimeError("Missing track_id!")

        if self.track_name is None:
            raise RuntimeError("Missing track_name!")

        if self.category_id is None:
            raise RuntimeError("Missing category_id!")

        if self.category_name is None:
            raise RuntimeError("Missing category_name!")

        if self.vehicle_name is None:
            raise RuntimeError("Missing vehicle_name!")

        if self.lb_info is None:
            raise RuntimeError("Missing lb_info!")

        lb_entry_additional_info = {
            "lbHref": self.lb_href,
            "ghostHref": self.ghost_href,
            "dateSetTimestamp": self.date_set_timestamp,
            "lastCheckedTimestamp": self.last_checked.timestamp(),
            "recorded": False,
            "trackId": self.track_id,
            "trackName": self.track_name,
            "categoryId": self.category_id,
            "categoryName": self.category_name,
            "vehicleName": self.vehicle_name,
            "lbInfo": self.lb_info
        }

        self.lb_entry.update(lb_entry_additional_info)
        return self.lb_entry
