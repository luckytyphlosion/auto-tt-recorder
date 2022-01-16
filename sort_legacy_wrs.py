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

import json
import chadsoft
import identifiers
from sortedcontainers import SortedList
import dateutil.parser
import time
from datetime import datetime, timezone
from lb_entry import LbEntryBuilder

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
    with open("removed_ctgp_tracks.json", "r") as f:
        removed_ctgp_tracks = json.load(f)

    sorted_legacy_wrs = SortedList(key=lambda x: x['lastCheckedTimestamp'])
    lb_count = 0
    ghost_count = 0
    output = ""

    for track_id, all_leaderboards_for_track_id_plus_check_200cc in removed_ctgp_tracks.items():
        check_200cc = all_leaderboards_for_track_id_plus_check_200cc["check_200cc"]
        track_name_full = all_leaderboards_for_track_id_plus_check_200cc["track_name_full"]

        for leaderboard in all_leaderboards_for_track_id_plus_check_200cc["leaderboards"]:
            category_id = leaderboard.get("categoryId", -1)
            version = leaderboard.get("version")
            is_200cc = leaderboard["200cc"]
            track_name = leaderboard["name"]
            slot_id = leaderboard["slotId"]
            correct_slot_id = leaderboard["correctSlotId"]
            authors = leaderboard.get("authors", [])

            if is_200cc and not check_200cc and track_id != "E15503BB76C3B7A2165026D76C3DC7D97B980BBB":
                print(f"Removing 200cc leaderboard on track before 200cc: {track_name}")
            else:
                lb_href = leaderboard["_links"]["item"]["href"]
                lb_full_data = chadsoft.get_lb_from_href(lb_href, times="wr", start=None, limit=None, read_cache=True, write_cache=True, rate_limit=False)
                num_lb_ghosts = len(lb_full_data["ghosts"])
                if num_lb_ghosts == 0:
                    raise RuntimeError(f"{lb_href} unexpectedly has no ghosts!")

                ghost_count += num_lb_ghosts
                lb_count += (num_lb_ghosts != 0)

                lb_entry_builder = LbEntryBuilder()

                lb_entry_data = lb_full_data["ghosts"]
                wr_entry = lb_entry_data[0]
                lb_entry_builder.add_lb_entry(wr_entry)
                lb_entry_builder.add_track_category_vehicle_modifier_extra_info(
                    track_id, category_id, None, is_200cc,
                    all_leaderboards_for_track_id_plus_check_200cc,
                    track_name, slot_id, correct_slot_id, version, authors
                )
                lb_entry_builder.add_lb_href(lb_href)
                lb_entry_builder.gen_has_wr_lb_info()
                print(lb_entry_builder.lb_info)
                output += f"{lb_entry_builder.lb_info}\n"

                vehicle_is_kart = identifiers.vehicle_id_to_is_kart[wr_entry["vehicleId"]]
                if vehicle_is_kart:
                    primary_vehicle_modifier = "karts"
                    alt_vehicle_modifier = "bikes"
                else:
                    primary_vehicle_modifier = "bikes"
                    alt_vehicle_modifier = "karts"

                lb_entry_builder_redundant = LbEntryBuilder()
                lb_entry_builder_redundant.add_lb_entry(wr_entry)
                lb_entry_builder_redundant.add_track_category_vehicle_modifier_extra_info(
                    track_id, category_id, primary_vehicle_modifier, is_200cc,
                    all_leaderboards_for_track_id_plus_check_200cc,
                    track_name, slot_id, correct_slot_id, version, authors
                )
                lb_entry_builder_redundant.add_lb_href(lb_href)
                lb_entry_builder_redundant.gen_redundant_wr_lb_info()
                print(lb_entry_builder_redundant.lb_info)
                output += f"{lb_entry_builder_redundant.lb_info}\n"

                # reuse some old cached results in an earlier script iteration
                alt_vehicle_modifier_lb_start = None if alt_vehicle_modifier == "karts" else 0
                alt_vehicle_modifier_lb_limit = None if alt_vehicle_modifier == "karts" else 1

                alt_vehicle_modifier_lb_full_data = chadsoft.get_lb_from_href(lb_href, times="wr", start=alt_vehicle_modifier_lb_start, limit=alt_vehicle_modifier_lb_limit, vehicle=alt_vehicle_modifier, read_cache=True, write_cache=True, rate_limit=False)
                alt_vehicle_modifier_entry_data = alt_vehicle_modifier_lb_full_data["ghosts"]
                num_alt_vehicle_modifier_lb_ghosts = len(alt_vehicle_modifier_entry_data)
                ghost_count += num_alt_vehicle_modifier_lb_ghosts
                lb_count += (num_alt_vehicle_modifier_lb_ghosts != 0)

                lb_entry_builder_alt_vehicle_modifier = LbEntryBuilder()

                if num_alt_vehicle_modifier_lb_ghosts == 0:
                    lb_entry_builder_alt_vehicle_modifier.add_track_category_vehicle_modifier_extra_info(
                        track_id, category_id, alt_vehicle_modifier, is_200cc,
                        all_leaderboards_for_track_id_plus_check_200cc,
                        track_name, slot_id, correct_slot_id, version, authors
                    )
                    lb_entry_builder_alt_vehicle_modifier.add_ghost_href_last_checked_date_set_timestamp(
                        None, datetime.now(tz=timezone.utc), None
                    )
                    lb_entry_builder_alt_vehicle_modifier.add_lb_href(lb_href)
                    lb_entry_builder_alt_vehicle_modifier.gen_no_wr_lb_info()

                else:
                    alt_vehicle_modifier_wr_entry = alt_vehicle_modifier_entry_data[0]
                    lb_entry_builder_alt_vehicle_modifier.add_lb_entry(alt_vehicle_modifier_wr_entry)
                    lb_entry_builder_alt_vehicle_modifier.add_track_category_vehicle_modifier_extra_info(
                        track_id, category_id, alt_vehicle_modifier, is_200cc,
                        all_leaderboards_for_track_id_plus_check_200cc,
                        track_name, slot_id, correct_slot_id, version, authors
                    )
                    lb_entry_builder_alt_vehicle_modifier.add_lb_href(lb_href)
                    lb_entry_builder_alt_vehicle_modifier.gen_has_wr_lb_info()

                print(lb_entry_builder_alt_vehicle_modifier.lb_info)
                output += f"{lb_entry_builder_alt_vehicle_modifier.lb_info}\n"

                lb_entry_both_vehicles = lb_entry_builder.get_lb_entry_with_additional_info()
                lb_entry_redundant = lb_entry_builder_redundant.get_lb_entry_with_additional_info()
                lb_entry_alt_vehicle_modifier = lb_entry_builder_alt_vehicle_modifier.get_lb_entry_with_additional_info()
                sorted_legacy_wrs.add(lb_entry_both_vehicles)
                sorted_legacy_wrs.add(lb_entry_redundant)
                sorted_legacy_wrs.add(lb_entry_alt_vehicle_modifier)

    print(f"ghost_count: {ghost_count}, lb_count: {lb_count}")

    sorted_legacy_wrs_as_list = list(sorted_legacy_wrs)

    with open("sorted_legacy_wrs.json", "w+", encoding="utf-8") as f:
        json.dump(sorted_legacy_wrs_as_list, f, indent=2, ensure_ascii=False)
    
    with open("lb_info_out.txt", "w+") as f:
        f.write(output)

if __name__ == "__main__":
    main()
