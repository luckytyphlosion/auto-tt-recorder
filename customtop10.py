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

# Much of this code was derived from https://github.com/AtishaRibeiro/TT-Rec-Tools/tree/dev/customtop10
# Below is said code's license

# MIT License
# 
# Copyright (c) 2020 AtishaRibeiro
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import itertools
import pathlib
import functools

import chadsoft
import util
import import_ghost_to_save
from import_ghost_to_save import Rkg
import wbz
import identifiers

from constants.customtop10 import *
from stateclasses.gecko_code_line import *
from stateclasses.split_classes import *

import sys

CONTROLLER_WII_WHEEL = 0

# -tt -ttc "https://chadsoft.co.uk" -ttl ww
regional_to_country = {
    "eu": "Germany",
    "europe": "Germany",
    "na": "USA",
    "north america": "USA",
    "northamerica": "USA",
    "ame": "Mexico",
    "americas": "Mexico",
    "la": "Paraguay",
    "latin": "Paraguay",
    "latinamerica": "Paraguay",
    "latin america": "Paraguay",
    "asia": "Hong Kong",
    "oc": "Australia",
    "oceania": "Australia"
}

regional_to_full_name = {
    "eu": "Europe",
    "europe": "Europe",
    "na": "North America",
    "north america": "North America",
    "northamerica": "North America",
    "ame": "Americas",
    "americas": "Americas",
    "la": "Latin America",
    "latin": "Latin America",
    "latinamerica": "Latin America",
    "latin america": "Latin America",
    "asia": "Asia",
    "oc": "Oceania",
    "oceania": "Oceania"
}

continent_to_name = {
    1: "Asia",
    2: "America",
    3: "Europe & Africa",
    4: "Oceania",
    5: "Korea"
}
    
def simplify_globe_location(globe_location):
    if globe_location.lower() in ("worldwide", "ww"):
        return "ww"
    else:
        return globe_location

##############################################
# CODE GENERATION FUNCTIONS
##############################################

def get_top_10_entries_from_filelist(*rkg_filenames):
    if not (1 <= len(rkg_filenames) <= 10):
        raise RuntimeError(f"Number of RKG files \"{len(rkg_filenames)}\" not in range [1, 10]!")

    top_10_entries = []

    for rkg_filename in rkg_filenames:
        rkg = Rkg(rkg_filename)
        top_10_entries.append(Top10Entry.from_rkg(rkg))

    return top_10_entries

empty_tuple = tuple()

class CustomTop10AndGhostDescription:
    __slots__ = ("globe_location", "ghost_description", "top_10_code", "leaderboard", "highlight_index")

    def __init__(self, globe_location, ghost_description, top_10_code, leaderboard=None, highlight_index=None):
        self.globe_location = simplify_globe_location(globe_location)
        self.ghost_description = ghost_description
        self.top_10_code = top_10_code
        self.leaderboard = leaderboard
        self.highlight_index = highlight_index

    @classmethod
    def from_chadsoft(cls, iso_region, chadsoft_lb, globe_location, top_10_title, highlight_index, ghost_description, censored_players, track_name, cache_settings, wbz_settings):
        if type(highlight_index) != int:
            raise RuntimeError(f"Highlight index not int!")

        if highlight_index != -1 and not (1 <= highlight_index <= 10):
            raise RuntimeError(f"Highlight index \"{highlight_index}\" not -1 or in range [1, 10]!")

        if top_10_title == "auto":
            top_10_title = "{trackName} {cc} {vehicle} {category} {continent} Top 10"

        leaderboard = chadsoft.Leaderboard(chadsoft_lb, 10, cache_settings, wbz_settings)
        leaderboard.download_info_and_ghosts()

        top_10_entries = []
        if censored_players is not None:
            if isinstance(censored_players, (tuple, set, list)):
                censored_players_as_set = set(censored_players)
            else:
                censored_players_as_set = set(censored_players.split())
        else:
            censored_players_as_set = empty_tuple

        for lb_entry in leaderboard.lb_info_and_entries["ghosts"]:
            rkg_data = lb_entry["rkg_data"]
            if rkg_data is not None:                
                rkg = Rkg(rkg_data)
                if lb_entry["playerId"] in censored_players_as_set:
                    top_10_entry = Top10Entry.from_rkgless_lb_entry(lb_entry, censor=True)
                else:
                    top_10_entry = Top10Entry.from_rkg(rkg, lb_entry["playerId"], cache_settings=cache_settings)

            else:
                top_10_entry = Top10Entry.from_rkgless_lb_entry(lb_entry)

            top_10_entries.append(top_10_entry)

        globe_location = simplify_globe_location(globe_location)

        custom_top_10 = CustomTop10(iso_region, globe_location, top_10_title, top_10_entries, highlight_index, track_name=track_name)
        custom_top_10.build_automatic_title(leaderboard)
        top_10_code = custom_top_10.generate()

        return cls(globe_location, ghost_description, top_10_code, leaderboard=leaderboard, highlight_index=highlight_index)

    @classmethod
    def from_gecko_code_filename(cls, gecko_code_filename, globe_location, ghost_description, iso_region):
        gecko_code_filepath = pathlib.Path(gecko_code_filename)
        if not gecko_code_filepath.is_file():
            raise RuntimeError(f"top-10-gecko-code-filename \"{gecko_code_filename}\" does not exist!")

        if gecko_code_filepath.suffix == ".gct":
            raise RuntimeError(f"top-10-gecko-code-filename \"{gecko_code_filename}\" must not be .gct! (Paste the gecko code generated from tt-rec.com in a text file)")

        try:
            with open(gecko_code_filename, "r") as f:
                top_10_code = f.read()
        except UnicodeDecodeError:
            raise RuntimeError(f"top-10-gecko-code-filename \"{gecko_code_filename}\" is not a text file! (Paste the gecko code generated from tt-rec.com in a text file)")

        top_10_region_dependent_codes_to_iso_region = {region_dependent_codes.top_10: iso_region for iso_region, region_dependent_codes in custom_top_10_region_dependent_codes.items()}

        top_10_code_lines = top_10_code.splitlines()
        found_top_10_code = False

        for i, line in enumerate(top_10_code_lines, 1):
            line = line.strip()
            if line.strip() == "":
                continue

            is_gecko_code_line_valid = True
            codeline_split = line.split(maxsplit=1)
            if len(codeline_split) != 2:
                is_gecko_code_line_valid = False
            else:
                codeline_first_half, codeline_second_half = codeline_split
                if len(codeline_first_half) != 8 or len(codeline_second_half) != 8:
                    is_gecko_code_line_valid = False
                else:
                    try:
                        int(codeline_first_half, 16)
                        int(codeline_second_half, 16)
                    except ValueError:
                        is_gecko_code_line_valid = False

            if not is_gecko_code_line_valid:
                raise RuntimeError(f"Bad line found in top-10-gecko-code-filename \"{gecko_code_filename}\" at line {i}: {line}")

            expected_iso_region = top_10_region_dependent_codes_to_iso_region.get(codeline_first_half.upper())
            if expected_iso_region is not None:
                if found_top_10_code:
                    raise RuntimeError(f"Broken code provided by top-10-gecko-code-filename \"{gecko_code_filename}\"! (possible duplicate line)")

                if iso_region.name != expected_iso_region:
                    raise RuntimeError(f"top-10-gecko-code-filename \"{gecko_code_filename}\" was made for {expected_iso_region} but ISO/WBFS is {iso_region.name}!")

                found_top_10_code = True

        if not found_top_10_code:
            raise RuntimeError("Provided manual top 10 gecko code is not actually a top 10 gecko code!")

        return cls(globe_location, ghost_description, top_10_code)

    @classmethod
    def from_mk_channel_ghost_select_only(cls, iso_region, globe_location, ghost_description):
        dummy_top_10_entry = Top10Entry.dummy_entry()
        custom_top_10 = CustomTop10(iso_region, globe_location, "Dummy", [dummy_top_10_entry], 1)
        top_10_code = custom_top_10.generate()
        return cls(globe_location, ghost_description, top_10_code)

    def get_rkg_file_main(self):
        if self.highlight_index == -1:
            raise RuntimeError("Unknown main ghost to download! (highlight index is -1)")
        elif self.highlight_index > len(self.leaderboard.lb_info_and_entries):
            raise RuntimeError(f"Highlight index specified is out of bounds of top 10 leaderboard entries! (Leaderboard only has entry count {len(self.leaderboard.lb_info_and_entries)})")

        rkg_data = self.leaderboard.lb_info_and_entries["ghosts"][self.highlight_index - 1]["rkg_data"]
        
        if rkg_data is None:
            raise RuntimeError("Requested placement to download from leaderboard has missing ghost!")

        return rkg_data

    def get_szs_and_wbz_converter(self, iso_filename):
        return self.leaderboard.get_szs_and_wbz_converter_if_not_default_track(iso_filename)

    def is_200cc(self):
        return self.leaderboard.is_200cc()

    def get_controller(self, controller):
        if self.highlight_index == -1:
            return controller
        elif self.highlight_index > len(self.leaderboard.lb_info_and_entries):
            raise RuntimeError(f"Highlight index specified is out of bounds of top 10 leaderboard entries! (Leaderboard only has entry count {len(self.leaderboard.lb_info_and_entries)})")

        controller = self.leaderboard.lb_info_and_entries["ghosts"][self.highlight_index - 1]["controller"]
        return controller

    def get_track_name(self):
        return self.leaderboard.get_track_name()

oMII_SYSTEM_ID = 0x1c
oMII_SYSTEM_ID_END = 0x20
oMII_CREATOR_NAME = 0x36

finish_time_regex = re.compile(r"^([0-9]{2}):([0-9]{2})\.([0-9]{3})$")

class Top10Entry:
    __slots__ = ("country", "finish_time", "wheel", "partial_mii")

    def __init__(self, country, finish_time, wheel, partial_mii):
        self.country = country
        self.finish_time = finish_time
        self.wheel = wheel
        self.partial_mii = partial_mii

    @classmethod
    def from_rkg(cls, rkg, player_id=None, cache_settings=None):
        country_code = rkg.country_code
        if country_code == 255 and player_id is not None:
            country_code = chadsoft.get_player_from_player_id(player_id, cache_settings=cache_settings).get("country", 255)

        country = countries_by_code[country_code]
        finish_time = rkg.finish_time
        wheel = (rkg.controller == CONTROLLER_WII_WHEEL)
        partial_mii = list(rkg.mii[:oMII_SYSTEM_ID] + rkg.mii[oMII_SYSTEM_ID_END:oMII_CREATOR_NAME])
        return cls(country, finish_time, wheel, partial_mii)

    @classmethod
    def from_rkgless_lb_entry(cls, lb_entry, censor=False):
        if censor:
            country = countries_by_name["NO FLAG"]
        else:
            country = countries_by_code[lb_entry["country"]]

        match_obj = finish_time_regex.match(lb_entry["finishTimeSimple"])
        finish_time = Split(int(match_obj.group(1)), int(match_obj.group(2)), int(match_obj.group(3)))
        controller = lb_entry["controller"]
        wheel = (controller == CONTROLLER_WII_WHEEL)
        # todo replace player name
        partial_mii = list(DEFAULT_MII)

        return cls(country, finish_time, wheel, partial_mii)

    @classmethod
    def dummy_entry(cls):
        country = countries_by_name["NO FLAG"]
        finish_time = Split(0, 0, 1)
        wheel = False
        partial_mii = list(DEFAULT_MII)
        return cls(country, finish_time, wheel, partial_mii)

split_with_space_regex = re.compile(r"(\s+|(?={))|(?<=})(?=[^{\s])")

class CustomTop10:
    __slots__ = ("code", "region_dependent_codes", "globe_location", "globe_position", "top_10_title", "highlight_index", "include_track_in_title", "entries", "track_name", "iso_region", "top_10_title_specifiers")

    def __init__(self, iso_region, globe_location, top_10_title, entries, highlight_index=1, include_track_in_title=False, track_name=None):
        self.code = []
        self.region_dependent_codes = custom_top_10_region_dependent_codes[iso_region]
        self.iso_region = iso_region
        self.globe_location = simplify_globe_location(globe_location)
        self.globe_position = CustomTop10.get_globe_position_from_location(globe_location)
        self.track_name = track_name
        self.top_10_title_specifiers = {}
        if self.globe_position == "":
            self.globe_position = countries_by_name["Belgium"].globe_position
        self.top_10_title = top_10_title
        if highlight_index != -1 and not (1 <= highlight_index <= 10):
            raise RuntimeError(f"Highlight index \"{highlight_index}\" not -1 or in range [1, 10]!")

        self.highlight_index = highlight_index
        self.include_track_in_title = include_track_in_title
        if not (1 <= len(entries) <= 10):
            raise RuntimeError(f"Number of entries \"{len(entries)}\" not in range [1, 10]!")
        self.entries = entries

    @staticmethod
    def get_globe_position_from_location(globe_location):
        if globe_location == "ww":
            return countries_by_name["Belgium"].globe_position
        else:
            regional_country = regional_to_country.get(globe_location.lower())
            if regional_country is not None:
                return countries_by_name[regional_country].globe_position
            else:
                try:
                    return countries_by_name[globe_location].globe_position
                except KeyError:
                    pass
    
                try:
                    return countries_by_flag_id[globe_location.upper()].globe_position
                except KeyError as e:
                    raise RuntimeError(f"Unknown country \"{globe_location}\" specified in top-10-location!")

    def set_top_10_title_track_name(self, leaderboard):
        if self.track_name is None:
            self.include_track_in_title = True
            return ""
        elif self.track_name == "auto":
            track_name = leaderboard.get_track_name()
            if track_name is None:
                raise RuntimeError(f"{{trackName}} specifier in top-10-title failed because Chadsoft leaderboard {leaderboard.get_lb_link()} has no track name! (must specify track-name manually)")
            return track_name
        else:
            return self.track_name

    def get_200cc_str(self, leaderboard):
        if leaderboard.is_200cc():
            return "200cc"
        else:
            return ""

    def get_vehicle_name(self, leaderboard, iso_region_name):
        vehicle = leaderboard.get_vehicle()
        if vehicle == "karts":
            return "Kart"
        elif vehicle == "bikes":
            return "Bike"
        elif vehicle is None:
            return ""
        else:
            return identifiers.get_vehicle_name_region_dependent(vehicle, iso_region_name)

    def get_location_full_name(self, leaderboard, worldwide_name):
        globe_location = self.globe_location
        if globe_location == "ww":
            location_full_name = worldwide_name
        else:
            try:
                location_full_name = regional_to_full_name[globe_location.lower()]
            except KeyError:
                try:
                    location_full_name = countries_by_name[globe_location].name
                except KeyError:
                    try:
                        location_full_name = countries_by_flag_id[globe_location.upper()].name
                    except KeyError as e:
                        raise RuntimeError(f"Unknown country \"{globe_location}\" specified in top-10-location!")

        return location_full_name

    def get_continent_name(self, leaderboard, worldwide_name):
        continent_name = continent_to_name.get(leaderboard.get_continent())
        if continent_name is None:
            return worldwide_name
        else:
            return continent_name

    def get_community_category_name(self, leaderboard):
        return leaderboard.determine_community_category_name()

    def create_top_10_title_specifiers(self):
        self.top_10_title_specifiers = {
            "{trackName}": CustomTop10.set_top_10_title_track_name,
            "{cc}": CustomTop10.get_200cc_str,
            "{vehicle}": functools.partial(CustomTop10.get_vehicle_name, iso_region_name=self.iso_region),
            "{vehicleUS}": functools.partial(CustomTop10.get_vehicle_name, iso_region_name="NTSC-U"),
            "{vehicleEU}": functools.partial(CustomTop10.get_vehicle_name, iso_region_name="PAL"),
            "{location}": functools.partial(CustomTop10.get_location_full_name, worldwide_name="Worldwide"),
            "{locationWWisCTGP}": functools.partial(CustomTop10.get_location_full_name, worldwide_name="CTGP"),
            "{category}": CustomTop10.get_community_category_name,
            "{continent}": functools.partial(CustomTop10.get_continent_name, worldwide_name="Worldwide"),
            "{continentWWisCTGP}": functools.partial(CustomTop10.get_continent_name, worldwide_name="CTGP")
        }

    def build_automatic_title(self, leaderboard):
        if "{" not in self.top_10_title and "}" not in self.top_10_title:
            return

        self.create_top_10_title_specifiers()

        escape_removed_top_10_title = self.top_10_title.replace("{{", "\x05").replace("}}", "\x06")
        split_top_10_title = [x if x is not None else "" for x in split_with_space_regex.split(escape_removed_top_10_title)]
        prev_was_empty_specifier = False
        built_top_10_title_parts = []

        for top_10_title_part in split_top_10_title:
            top_10_title_specifier_func = self.top_10_title_specifiers.get(top_10_title_part)
            if top_10_title_specifier_func is not None:
                value = top_10_title_specifier_func(self, leaderboard)
                if value != "":
                    calculated_top_10_title_part = value
                    prev_was_empty_specifier = False
                else:
                    calculated_top_10_title_part = ""
                    prev_was_empty_specifier = True
            else:
                if prev_was_empty_specifier and top_10_title_part != "":
                    calculated_top_10_title_part = top_10_title_part[1:]
                else:
                    calculated_top_10_title_part = top_10_title_part

                prev_was_empty_specifier = False
            built_top_10_title_parts.append(calculated_top_10_title_part)

        self.top_10_title = "".join(built_top_10_title_parts).strip()
        self.top_10_title.replace("\x05", "{").replace("\x06", "}")

    # main function that generates the code
    def generate(self):
        self.crc16_bypass_code();
        self.globe_position_code();
        self.add_highlight_code();
        self.custom_title_code();
        self.add_top_10_code();

        return "".join(f"{code_line.left_side} {code_line.right_side}\n" for code_line in self.code).upper()

    def add_code_line(self, left_side, right_side):
        self.code.append(GeckoCodeLine(left_side, right_side))

    def add_code_lines(self, *args):
        if len(args) % 2 != 0:
            raise RuntimeError("Number of code elements not even!")

        for left_side, right_side in util.grouper(args, 2):
            self.code.append(GeckoCodeLine(left_side, right_side))

    def crc16_bypass_code(self):
        self.add_code_line(self.region_dependent_codes.bypass_crc, "48000010")

    def globe_position_code(self):
        if self.globe_location != "ww":
            self.add_code_lines(
                self.region_dependent_codes.flag_changer, "00004303",
                self.region_dependent_codes.globe_position, self.globe_position
            )

    def custom_title_code(self):
        title_code = [self.region_dependent_codes.custom_title, "XXXXXXXX",
                        "7D6802A6", "YYYYYYYY"]

        hex_title = ""
        if self.include_track_in_title:
            # this is string that will be replaced by the track name
            hex_title += "001A0802001100000020"

        hex_title += util.utf_16_hex(self.top_10_title)
        title_data = ["".join(eight_digit_chunk) for eight_digit_chunk in util.grouper(hex_title, 8, "0")]
        title_data.append("00000000")
        title_code.extend(title_data)
        title_code.extend(("2C0E1776", "4082000C",
                            "7C6802A6", "90610020",
                            "7EA3AB78", "7D6803A6"))

        if len(title_code) % 2 == 0:
            title_code.append("60000000")

        title_code.append("00000000");
        title_code[1] = f"{len(title_code) // 2 - 1:08x}"
        title_code[3] = f"48{(len(title_data) + 1) * 4 + 1:06x}"
        self.add_code_lines(*title_code)

    def add_highlight_code(self):
        if self.highlight_index != -1:
            highlight_code = [self.region_dependent_codes.highlight, "00000005",
                                    "386300A8", f"2C1C000{self.highlight_index:x}",
                                    "40A2001C", "A183003C",
                                    "2C0C7031", "40A20010",
                                    "80830010", "8164FF68",
                                    "91640008", "00000000"];
            self.add_code_lines(*highlight_code)

    def add_top_10_code(self):
        total_entries = len(self.entries)

        entries_code_part = f"398000{total_entries:02x}"
        branch_code_part = f"48{0x05 + total_entries * 0x38:06x}"

        top_10_code = [self.region_dependent_codes.top_10, None,
                            "BE41FFC8", "38800000",
                            "39800001", "91830058", 
                            entries_code_part, "91830060",
                            "7D8903A6", "39630068", 
                            branch_code_part]
                                  
        for entry in self.entries:
            # convert all data to code
            finish_time = entry.finish_time
            country_id = entry.country.code
            wheel = entry.wheel

            top_10_code.append(f"{finish_time.milliseconds:04x}{finish_time.minutes:02x}{finish_time.seconds:02x}")
            #print(f"finish time code: {finish_time.minutes:02x}{finish_time.seconds:02x}{finish_time.milliseconds:04x}")
            print(f"finish_time.pretty(): {finish_time.pretty()}")
            partial_mii_data_plus_country_wheel = entry.partial_mii + [country_id, (0 if wheel else 1)]
            #print(f"len(partial_mii_data_plus_country_wheel): {len(partial_mii_data_plus_country_wheel)}")
            top_10_code.extend("".join(f"{num:02x}" for num in four_byte_chunk) for four_byte_chunk in util.grouper(partial_mii_data_plus_country_wheel, 4))

        top_10_code.extend(("7D8802A6",
                                "BA4C0000", "B24B0001",
                                "924B0004", "BE6B0008",
                                "BF4B0028", "9BEB0057",
                                "B3EB0060", "398C0038",
                                "396B0068", "4200FFDC",
                                "7C0803A6", "BA41FFC8"))

        if len(top_10_code) % 2 == 0:
            top_10_code.append("60000000")

        top_10_code.append("00000000")
        top_10_code[1] = f"{(len(top_10_code) // 2) - 1:08x}"
        self.add_code_lines(*top_10_code)

def test_custom_top_10():
    top_10_entries = get_top_10_entries_from_filelist(
        "00m15s7259880 labies man.rkg",
        "00m15s7943144 labies man.rkg",
        "00m15s9610732 Niyake.rkg",
        "00m16s1320374 Niyake2.rkg",
        "01m56s8601510 Batcake.rkg"
    )

    custom_top_10 = CustomTop10("NTSC-U", "ww", "My Custom Track Top 10", top_10_entries)
    top_10_code = custom_top_10.generate()
    with open("customtop10_out.dump", "w+") as f:
        f.write(top_10_code)

def main():
    MODE = 0
    if MODE == 0:
        test_custom_top_10()
    else:
        print("No mode selected!")

if __name__ == "__main__":
    main()
