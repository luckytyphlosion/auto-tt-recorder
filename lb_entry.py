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

vehicle_modifier_to_str = {
    "karts": "Kart",
    "bikes": "Bike"
}

class LbEntryBuilder:
    __slots__ = ("track_id", "category_id", "vehicle_modifier", "vehicle_modifier_str",
        "track_name", "category_name", "is_200cc",
        "lb_href", "lb_entry", "ghost_href",
        "date_set_timestamp", "last_checked", "lb_info",
        "track_name_full", "missing_from_archive", "wiimm_version",
        "version_with_brackets", "str_200cc", "is_redundant"
    )

    def __init__(self):
        self.track_id = None
        self.category_id = None
        self.vehicle_modifier = None
        self.vehicle_modifier_str = None
        self.track_name = None
        self.category_name = None
        self.lb_href = None
        self.lb_entry = {}
        self.ghost_href = None
        self.date_set_timestamp = None
        self.last_checked = None
        self.lb_info = None
        self.track_name_full = None
        self.missing_from_archive = None
        self.wiimm_version = None
        self.version_with_brackets = None
        self.is_200cc = None
        self.str_200cc = None
        self.is_redundant = False

    # three cases:
    # - lb with no ghosts, from initial parse
    # - lb with ghosts, from initial parse
    # - lb with ghosts, from periodic parse
    def add_track_category_vehicle_modifier_extra_info(self, track_id, category_id, vehicle_modifier, is_200cc, all_leaderboards_for_track_id_plus_check_200cc, track_name):
        self.track_id = track_id
        self.category_id = category_id
        self.vehicle_modifier = vehicle_modifier
        self.vehicle_modifier_str = vehicle_modifier_to_str.get(vehicle_modifier)

        self.category_name = identifiers.category_names_no_200cc[category_id]
        self.track_name = track_name
        self.track_name_full = all_leaderboards_for_track_id_plus_check_200cc["track_name_full"]
        self.missing_from_archive = all_leaderboards_for_track_id_plus_check_200cc["missing_from_archive"]
        self.wiimm_version = all_leaderboards_for_track_id_plus_check_200cc["wiimm_version"]
        self.is_200cc = is_200cc
        self.str_200cc = "200cc" if is_200cc else None

    def add_track_category_vehicle_modifier_extra_info_from_prev_lb_entry(self, prev_lb_entry):
        self.add_track_category_vehicle_id(
            prev_lb_entry["trackId"],
            prev_lb_entry["categoryId"],
            prev_lb_entry["vehicleModifier"],
            prev_lb_entry["200cc"],
            {
                prev_lb_entry["trackNameFull"],
                prev_lb_entry["missingFromArchive"],
                prev_lb_entry["wiimmVersion"],
            },
            prev_lb_entry["trackName"]
        )

    def add_ghost_href_last_checked_date_set_timestamp(self, ghost_href, last_checked, date_set_timestamp):
        self.ghost_href = ghost_href
        self.last_checked = last_checked
        self.date_set_timestamp = date_set_timestamp

    def add_lb_href(self, lb_href):
        self.lb_href = lb_href

    def add_lb_entry(self, lb_entry):
        self.lb_entry = lb_entry.copy()
        self.ghost_href = lb_entry["_links"]["item"]["href"]
        date_set = dateutil.parser.isoparse(lb_entry["dateSet"])
        self.date_set_timestamp = date_set.timestamp()
        self.last_checked = date_set
        version = lb_entry.get("version")
        if version is None:
            self.version_with_brackets = None
        else:
            self.version_with_brackets = f"({version})"

    @staticmethod
    def join_conditional_modifier(*modifiers):
        return " ".join(modifier for modifier in modifiers if modifier is not None)

    def gen_no_wr_lb_info(self):
        self.lb_info = f"No wr exists for {LbEntryBuilder.join_conditional_modifier(self.str_200cc, self.vehicle_modifier_str, self.track_name, self.version_with_brackets)} - {self.category_name}!"

    def gen_redundant_wr_lb_info(self):
        self.lb_info = f"{LbEntryBuilder.join_conditional_modifier(self.str_200cc, self.vehicle_modifier_str, self.track_name, self.version_with_brackets)} - {self.category_name} is a redundant WR!"
        self.is_redundant = True

    def gen_has_wr_lb_info(self):
        self.lb_info = f"{self.lb_entry['player']} beat {LbEntryBuilder.join_conditional_modifier(self.str_200cc, self.vehicle_modifier_str, self.track_name, self.version_with_brackets)} - {self.category_name} in {self.lb_entry['finishTimeSimple']} on {self.lb_entry['dateSet']}."

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

        if self.lb_info is None:
            raise RuntimeError("Missing lb_info!")

        if self.track_name_full is None:
            raise RuntimeError("Missing track_name_full!")

        if self.missing_from_archive is None:
            raise RuntimeError("Missing missing_from_archive!")

        #if self.wiimm_version is None:
        #    raise RuntimeError("Missing wiimm_version!")

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
            "lbInfo": self.lb_info,
            "vehicleModifier": self.vehicle_modifier,
            "trackNameFull": self.track_name_full,
            "missingFromArchive": self.missing_from_archive,
            "wiimmVersion": self.wiimm_version,
            "isRedundant": self.is_redundant
        }

        self.lb_entry.update(lb_entry_additional_info)
        return self.lb_entry
