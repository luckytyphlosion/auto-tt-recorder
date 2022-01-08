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

import chadsoft
import util
import import_ghost_to_save
from import_ghost_to_save import Rkg

from constants.customtop10 import *
from stateclasses.gecko_code_line import *
from stateclasses.split_classes import *


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

    ap.add_argument("-ttc", "--top-10-chadsoft", dest="top_10_chadsoft", default=None, help="Chadsoft link for the custom top 10 leaderboard. Current supported filters are the filters that Chadsoft supports (except flaps), i.e. Region, Vehicles, and Times. This cannot be specified with -ttg/--top-10-gecko-code-filename.")
    ap.add_argument("-ttl", "--top-10-location", dest="top_10_location", default="ww", help="What portion of the globe will show on the top 10 screen. Valid options are ww/worldwide, the name of a region, or the name of a country. For region/country, valid options are the same as on https://www.tt-rec.com/customtop10/. If -ttg/--top-10-gecko-code-filename is specified, then valid options are ww/worldwide and regional (so that the program knows whether to show the Regional or Worldwide Top 10 screen).")
    ap.add_argument("-ttt", "--top-10-title", dest="top_10_title", default=None, help="The title that shows at the top of the Top 10 Leaderboard. Default is \"Worldwide Top 10\" for worldwide, and \"<Location> Top 10\" for the specified location. Ignored if -ttg/--top-10-gecko-code-filename is specified.")
    ap.add_argument("-tth", "--top-10-highlight", dest="top_10_highlight", type=int, default=1, help="The entry to highlight on the Top 10 Leaderboard. Must be in range 1-10, or -1 for no highlight. Default is 1. Ignored if -ttg/--top-10-gecko-code-filename is specified.")
    ap.add_argument("-ttg", "--top-10-gecko-code-filename", dest="top_10_gecko_code_filename", default=None, help="The gecko code used to make a Custom Top 10. This cannot be specified with -ttc/--top-10-chadsoft. If your Top 10 is anything more complicated than a chadsoft leaderboard, then you're better off using https://www.tt-rec.com/customtop10/ to make your Custom Top 10.") 
    ap.add_argument("-ttn", "--top-10-course-name", dest="top_10_course_name", default=None, help="The name of the course which will appear on the Top 10 Ghost Entry screen. Default is to use the course name of the Rkg track slot.")
    ap.add_argument("-ttd", "--top-10-ghost-description", dest="top_10_ghost_description", default=None, help="The description of the ghost which appears on the top left of the Top 10 Ghost entry name of the course which will appear on the Top 10 Ghost Entry screen. Default is to use the course name of the Rkg track slot.")

class CustomTop10AndGhostDescription:
    __slots__ = ("globe_location", "course_name", "ghost_description", "top_10_code", "rkg_file_main")

    def __init__(self, globe_location, course_name, ghost_description, top_10_code, rkg_file_main=None):
        self.globe_location = globe_location
        self.course_name = course_name
        self.ghost_description = ghost_description
        self.top_10_code = top_10_code
        self.rkg_file_main = rkg_file_main

    @classmethod
    def from_chadsoft(chadsoft_lb, globe_location, top_10_title, highlight_index, course_name, ghost_description, censored_players, download_rkg_main=False):
        if type(highlight_index) != int:
            raise RuntimeError(f"Highlight index not int!")

        if highlight_index != -1 and not (1 <= highlight_index <= 10):
            raise RuntimeError(f"Highlight index \"{highlight_index}\" not -1 or in range [1, 10]!")

        if highlight_index == -1 and download_rkg_main:
            raise RuntimeError("Unknown main ghost to download!")

        top_10_leaderboard = chadsoft.get_top_10_lb_from_lb_link(chadsoft_lb)
        rkg_file_main = None
        top_10_entries = []
        censored_players_as_set = set(censored_players.split())

        for i, lb_entry in enumerate(top_10_leaderboard["ghosts"], 1):
            rkg_data, status_code = chadsoft.get(rkg_link, is_binary=True)

            if status_code != 404:
                rkg = Rkg(rkg_data)
                if lb_entry["playerId"] in censored_players_as_set:
                    top_10_entry = Top10Entry.from_rkgless_lb_entry(lb_entry)                    
                else:
                    top_10_entry = Top10Entry.from_rkg(rkg)

                if i == highlight_index:
                    rkg_file_main = rkg
            else:
                top_10_entry = Top10Entry.from_rkgless_lb_entry(lb_entry)
                if i == highlight_index:
                    raise RuntimeError("Requested placement to download from leaderboard has missing ghost!")

            top_10_entries.append(top_10_entry)

        if rkg_file_main is None and download_rkg_main:
            raise RuntimeError(f"Highlight index specified is out of bounds of top 10 leaderboard entries! (Leaderboard only has entry count {len(top_10_leaderboard['ghosts'])})")

        custom_top_10 = CustomTop10("NTSC-U", globe_location, top_10_title, top_10_entries, highlight_index)
        top_10_code = custom_top_10.generate()

        return cls(globe_location, course_name, ghost_description, top_10_code, rkg_file_main=rkg_file_main)

    @classmethod
    def from_gecko_code_filename(gecko_code_filename, globe_location, course_name, ghost_description):
        with open(gecko_code_filename, "r") as f:
            top_10_code = f.read()

        return cls(globe_location, course_name, ghost_description, top_10_code)

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
    def from_rkg(cls, rkg):
        country = countries_by_code[rkg.country_code]
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

        wheel = (controller == CONTROLLER_WII_WHEEL)
        # todo replace player name
        partial_mii = list(DEFAULT_MII)

        return cls(country, finish_time, wheel, partial_mii)

class CustomTop10:
    __slots__ = ("code", "region_dependent_codes", "globe_location", "globe_position", "top_10_title", "highlight_index", "include_track_in_title", "entries")

    def __init__(self, iso_region, globe_location, top_10_title, entries, highlight_index=1, include_track_in_title=False):
        self.code = []
        self.region_dependent_codes = custom_top_10_region_dependent_codes[iso_region]
        self.globe_location = globe_location
        self.globe_position = CustomTop10.get_globe_position_from_location(globe_location)
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
                    raise RuntimeError(f"Unknown country \"{globe_location}\"!") from e

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
