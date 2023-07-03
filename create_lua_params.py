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

from constants.lua_params import *

easy_staff_ghost_times = [
    129670,
    137856,
    216110,
    222480,
    144777,
    230764,
    234693,
    219585,
    156822,
    303022,
    258633,
    228237,
    230949,
    216802,
    304836,
    305895,
    134233,
    116461,
    106595,
    214799,
    248651,
    145568,
    241807,
    232882,
    210233,
    258304,
    258264,
    159771,
    138880,
    234894,
    257744,
    319323
]

GHOST_SELECT_STAFF_GHOST = 0
GHOST_SELECT_MAIN_GHOST = 1
GHOST_SELECT_COMPARE_GHOST = 2

class GhostEntry:
    __slots__ = ("type", "time")

    def __init__(self, type, time):
        self.type = type
        self.time = time

def create_lua_params(rkg, rkg_comparison, output_file, mode, ending_delay):
    cup = rkg.track_by_human_id // 4
    cup_menu_pos = rkg.track_by_human_id % 4

    output = ""
    output += f"mode: {mode}\n"
    output += f"cup: {cup}\n"
    output += f"cupMenuPos: {cup_menu_pos}\n"
    output += f"comparison: {'True' if rkg_comparison is not None else 'False'}\n"
    output += f"endingDelay: {ending_delay}\n"

    #print(f"staff time: {easy_staff_ghost_times[rkg.track_by_human_id]}")

    ghost_list = [
        GhostEntry(GHOST_SELECT_STAFF_GHOST, easy_staff_ghost_times[rkg.track_by_human_id]),
        GhostEntry(GHOST_SELECT_MAIN_GHOST, rkg.time()),
    ]
    if rkg_comparison is not None:
        ghost_list.append(GhostEntry(GHOST_SELECT_COMPARE_GHOST, rkg_comparison.time()))

    ghost_list.sort(key=lambda x: x.time, reverse=True)

    for i, ghost in enumerate(ghost_list):
        if ghost.type == GHOST_SELECT_MAIN_GHOST:
            output += f"mainGhostPos: {i}\n"
        elif ghost.type == GHOST_SELECT_COMPARE_GHOST:
            output += f"compareGhostPos: {i}\n"

    output += f"lapCount: {rkg.lap_count}\n"

    with open(output_file, "w+") as f:
        f.write(output)

def create_lua_params_for_custom_top_10_or_mk_channel(output_file, mode):
    with open(output_file, "w+") as f:
        f.write(f"mode: {mode}\n")

def main():
    pass

if __name__ == "__main__":
    main()
