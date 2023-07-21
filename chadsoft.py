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

import requests
import urllib
import pathlib
import json
import time
import re
import os
import random

import identifiers
import chadsoft
import chadsoft_config
import wbz
import wiimm
import dir_config
import traceback

from constants.categories import *

API_URL = "https://tt.chadsoft.co.uk"

class CacheSettings:
    __slots__ = ("read_cache", "write_cache", "cache_dirname", "rate_limit", "retry_on_empty")

    def __init__(self, read_cache, write_cache, cache_dirname, rate_limit=chadsoft_config.RATE_LIMIT, retry_on_empty=False):
        self.read_cache = read_cache
        self.write_cache = write_cache
        self.cache_dirname = cache_dirname
        self.rate_limit = rate_limit
        self.retry_on_empty = retry_on_empty

default_cache_settings = CacheSettings(True, True, "chadsoft_cached")

def get_cached_endpoint_filepath(endpoint, params, is_binary, cache_settings):
    if not is_binary:
        endpoint_as_pathname = f"{cache_settings.cache_dirname}/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}.json"
    else:
        endpoint_as_pathname = f"{cache_settings.cache_dirname}/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}.rkg"

    return pathlib.Path(endpoint_as_pathname)

def get(endpoint, params=None, is_binary=False, cache_settings=None):
    exception_sleep_time = 15

    while True:
        try:
            return get_in_loop_code(endpoint, params, is_binary, cache_settings)
        except ConnectionError as e:
            print(f"Exception occurred: {e}\n{''.join(traceback.format_tb(e.__traceback__))}\nSleeping for {exception_sleep_time} seconds now.")
            time.sleep(exception_sleep_time)
            exception_sleep_time *= 2
            if exception_sleep_time > 1000:
                exception_sleep_time = 1000

def get_in_loop_code(endpoint, params, is_binary, cache_settings):
    if params is None:
        params = {}

    if cache_settings is None:
        cache_settings = default_cache_settings

    endpoint_as_path = get_cached_endpoint_filepath(endpoint, params, is_binary, cache_settings)
    if cache_settings.read_cache and endpoint_as_path.is_file():
        error_code = None

        endpoint_as_path_size = endpoint_as_path.stat().st_size
        if endpoint_as_path_size == 0:
            if not is_binary:
                return {}, 404
            else:
                return bytes(), 404

        if not is_binary:
            #print(f"endpoint_as_path: {endpoint_as_path}")
            with open(endpoint_as_path, "r", encoding="utf-8-sig") as f:
                content = f.read().encode("utf-8")
                if len(content) < 5:
                    try:
                        error_code = int(content, 10)
                    except ValueError:
                        pass

                if error_code is None:
                    data = json.loads(content)
        else:
            with open(endpoint_as_path, "rb") as f:
                data = f.read()

            if len(data) < 5:
                try:
                    data_as_str = data.decode("utf-8")
                    error_code = int(data_as_str, 10)
                except (ValueError, UnicodeDecodeError):
                    pass

        if error_code is None:
            return data, 200

    url = f"{API_URL}{endpoint}"
    print(f"url: {url}?{urllib.parse.urlencode(params, doseq=True)}")
    start_time = time.time()
    r = requests.get(url, params=params)
    end_time = time.time()
    print(f"Request took {end_time - start_time}.")

    if cache_settings.write_cache:
        endpoint_as_path.parent.mkdir(parents=True, exist_ok=True)

    if r.status_code != 200:
        if cache_settings.write_cache:
            if r.status_code == 404:
                endpoint_as_path.touch()
            else:
                print(f"Got non-404 error code: {r.status_code}")
                with open(endpoint_as_path, "w+") as f:
                    f.write(str(r.status_code))

        return r.reason, r.status_code
        #raise RuntimeError(f"API returned {r.status_code}: {r.reason}")

    if not is_binary:
        data = json.loads(r.content.decode("utf-8-sig"))
    else:
        data = r.content

    if cache_settings.write_cache:
        endpoint_as_path.parent.mkdir(parents=True, exist_ok=True)
        if not is_binary:
            with open(endpoint_as_path, "w+", encoding="utf-8-sig") as f:
                f.write(r.text)
        else:
            with open(endpoint_as_path, "wb+") as f:
                f.write(r.content)

    if cache_settings.rate_limit:
        time.sleep(1)

    return data, r.status_code

duration_regex = re.compile(r"^(?:([0-9]+)h)?(?:([0-9]+)m)?(?:([0-9]+)s?)?$")

def parse_duration(duration):
    match_obj = duration_regex.match(duration.strip())
    if match_obj:
        hours = match_obj.group(1)
        minutes = match_obj.group(2)
        seconds = match_obj.group(3)
        if hours is None and minutes is None and seconds is None:
            raise RuntimeError(f"Invalid duration \"{expiry_time}\" provided for expiry time!")

        if hours is None:
            hours = 0
        if minutes is None:
            minutes = 0
        if seconds is None:
            seconds = 0

        try:
            duration_as_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        except ValueError:
            raise RuntimeError(f"At least one of hours, seconds, and minutes not an integer!")
    else:
        raise RuntimeError(f"Invalid duration \"{expiry_time}\" provided for expiry time!")

    return duration_as_seconds

def purge_cache(expiry_time_as_str, chadsoft_cache_folder):
    expiry_time = parse_duration(expiry_time_as_str)
    if expiry_time == 0:
        return

    num_files_purged = 0

    if not os.path.isdir(chadsoft_cache_folder):
        return

    for cache_basename in os.listdir(chadsoft_cache_folder):
        cache_filename = f"{chadsoft_cache_folder}/{cache_basename}"
        if os.path.isfile(cache_filename) and os.path.getmtime(cache_filename) + expiry_time < time.time():
            os.remove(cache_filename)
            num_files_purged += 1

    if num_files_purged > 0:
        print(f"Purged {num_files_purged} cache file{'s' if num_files_purged != 1 else ''}")

def get_lb_from_href(endpoint, start=0, limit=1, continent=None, vehicle=None, times="pb", override_cache=None, cache_settings=None):
    return get_lb_from_href_with_status(endpoint, start, limit, continent, vehicle, times, override_cache, cache_settings)[0]

def get_lb_from_href_with_status(endpoint, start=0, limit=1, continent=None, vehicle=None, times="pb", override_cache=None, cache_settings=None, rate_limit=chadsoft_config.RATE_LIMIT):
    params = {}
    if start is not None:
        params["start"] = start
    if limit is not None:
        params["limit"] = limit
    if continent is not None:
        params["continent"] = continent
    if vehicle is not None:
        params["vehicle"] = vehicle
    if times is not None:
        params["times"] = times
    if override_cache is not None:
        params["_"] = override_cache

    return get(endpoint, params, cache_settings=cache_settings)

def get_player_from_player_id(player_id, start=0, limit=0, cache_settings=None):
    params = {}
    if start is not None:
        params["start"] = start
    if limit is not None:
        params["limit"] = limit

    endpoint = f"/players/{player_id[:2]}/{player_id[2:]}.json"
    return get(endpoint, params, cache_settings=cache_settings)[0]

# #filter-region-all
# #filter-region-asia
# #filter-region-america
# #filter-region-europe-and-africa
# #filter-region-oceania
# #filter-region-korea

# #filter-vehicle-all
# #filter-vehicle-karts
# #filter-vehicle-bikes

# #filter-times-personal-best
# #filter-times-personal-records
# #filter-times-record-history
# #filter-times-all

leaderboard_regex = re.compile(r"^https://(?:www\.)?chadsoft\.co\.uk/time-trials/leaderboard/([0-1][0-9A-Fa-f]/[0-9A-Fa-f]{40}/(?:00|01|02|03|04|05|06)(?:-fast-lap)?)\.html(.*)$")

region_name_to_id = {
    "all": None,
    "asia": 1,
    "america": 2,
    "europe-and-africa": 3,
    "oceania": 4,
    "korea": 5
}

time_measure_to_id = {
    "personal-best": "pb",
    "personal-records": "pr",
    "record-history": "wr",
    "all": None
}

def get_lb_from_lb_link(lb_link, num_entries, cache_settings):
    match_obj = leaderboard_regex.match(lb_link)
    if not match_obj:
        raise RuntimeError(f"Invalid chadsoft leaderboard link {lb_link}!")

    filters = match_obj.group(2)
    continent = None
    vehicle = None
    times = "pb"

    if filters != "":
        split_filters = filters.split("#filter-")
        if len(split_filters) < 2:
            raise RuntimeError("Invalid chadsoft leaderboard filters!")

        split_filters = split_filters[1:]

        for filter in split_filters:
            split_filter = filter.split("-", maxsplit=1)
            if len(split_filter) != 2:
                raise RuntimeError(f"Invalid chadsoft leaderboard filter \"#filter-{filter}\"!")
    
            filter_name = split_filter[0].lower()
            filter_value = split_filter[1].lower()
    
            if filter_name == "region":
                try:
                    continent = region_name_to_id[filter_value]
                except KeyError:
                    raise RuntimeError(f"Invalid region value \"{filter_value}\"!")
            elif filter_name == "vehicle":
                if filter_value in {"karts", "bikes"}:
                    vehicle = filter_value
                elif filter_value == "all":
                    vehicle = None
                else:
                    try:
                        vehicle = identifiers.vehicle_ids_by_filter_name[filter_value]
                    except KeyError:
                        raise RuntimeError(f"Invalid vehicle value \"{filter_value}\"!")
            elif filter_name == "times":
                try:
                    times = time_measure_to_id[filter_value]
                except KeyError:
                    raise RuntimeError(f"Invalid times value \"{filter_value}\"!")
            else:
                raise RuntimeError(f"Unknown filter name \"{filter_name}\"!")

    slot_id_track_sha1 = match_obj.group(1)

    top_n_leaderboard = get_lb_from_href(f"/leaderboard/{slot_id_track_sha1}.json", start=0, limit=num_entries, continent=continent, vehicle=vehicle, times=times, cache_settings=cache_settings)

    if len(top_n_leaderboard["ghosts"]) == 0:
        raise RuntimeError("Leaderboard is empty!")

    return top_n_leaderboard, vehicle, continent

ghost_page_link_regex = re.compile(r"^https://(?:www\.)?chadsoft\.co\.uk/time-trials/rkgd/([0-9A-Fa-f]{2}/[0-9A-Fa-f]{2}/[0-9A-Fa-f]{36})\.html$")

default_track_sha1s = {"1AE1A7D894960B38E09E7494373378D87305A163", "90720A7D57A7C76E2347782F6BDE5D22342FB7DD", "0E380357AFFCFD8722329994885699D9927F8276", "1896AEA49617A571C66FF778D8F2ABBE9E5D7479", "7752BB51EDBC4A95377C0A05B0E0DA1503786625", "E4BF364CB0C5899907585D731621CA930A4EF85C", "B02ED72E00B400647BDA6845BE387C47D251F9D1", "D1A453B43D6920A78565E65A4597E353B177ABD0", "72D0241C75BE4A5EBD242B9D8D89B1D6FD56BE8F", "52F01AE3AED1E0FA4C7459A648494863E83A548C", "48EBD9D64413C2B98D2B92E5EFC9B15ECD76FEE6", "ACC0883AE0CE7879C6EFBA20CFE5B5909BF7841B", "38486C4F706395772BD988C1AC5FA30D27CAE098", "B13C515475D7DA207DFD5BADD886986147B906FF", "B9821B14A89381F9C015669353CB24D7DB1BB25D", "FFE518915E5FAAA889057C8A3D3E439868574508", "8014488A60F4428EEF52D01F8C5861CA9565E1CA", "8C854B087417A92425110CC71E23C944D6997806", "071D697C4DDB66D3B210F36C7BF878502E79845B", "49514E8F74FEA50E77273C0297086D67E58123E8", "BA9BCFB3731A6CB17DBA219A8D37EA4D52332256", "E8ED31605CC7D6660691998F024EED6BA8B4A33F", "BC038E163D21D9A1181B60CF90B4D03EFAD9E0C5", "418099824AF6BF1CD7F8BB44F61E3A9CC3007DAE", "4EC538065FDC8ACF49674300CBDEC5B80CC05A0D", "A4BEA41BE83D816F793F3FAD97D268F71AD99BF9", "692D566B05434D8C66A55BDFF486698E0FC96095", "1941A29AD2E7B7BBA8A29E6440C95EF5CF76B01D", "077111B996E5C4F47D20EC29C2938504B53A8E76", "F9A62BEF04CC8F499633E4023ACC7675A92771F0", "B036864CF0016BE0581449EF29FB52B2E58D78A4", "15B303B288F4707E5D0AF28367C8CE51CDEAB490"}

def get_szs_common(iso_filename, track_id):
    if track_id in default_track_sha1s:
        return None

    wit_filename, wszst_filename = wiimm.get_wit_wszst_filename()

    wbz_converter = wbz.WbzConverter(
        iso_filename=iso_filename,
        original_track_files_dirname=f"{dir_config.storage_dirname}/original-race-course",
        wit_filename=wit_filename,
        wszst_filename=wszst_filename,
        auto_add_containing_dirname=dir_config.storage_dirname
    )

    szs_filename = wbz_converter.download_wbz_convert_to_szs_get_szs_filename(track_id, use_auto_add_containing_dirname_as_dest=True)
    return szs_filename

class GhostPage:
    __slots__ = ("ghost_page_link", "ghost_id", "cache_settings", "ghost_info")

    def __init__(self, ghost_page_link, cache_settings):
        self.ghost_page_link = ghost_page_link
        match_obj = ghost_page_link_regex.match(ghost_page_link)
        if not match_obj:
            raise RuntimeError("Invalid chadsoft ghost page link!")

        self.ghost_id = match_obj.group(1)
        self.cache_settings = cache_settings
        self.ghost_info = None

    def get_rkg(self):
        rkg_data, status_code = chadsoft.get(f"/rkgd/{self.ghost_id}.rkg", is_binary=True, cache_settings=self.cache_settings)
    
        if status_code != 404:
            return rkg_data
        else:
            raise RuntimeError(f"Chadsoft ghost page \"{self.ghost_page_link}\" doesn't exist or does exist but has no ghost!")

    def get_szs(self, iso_filename):
        ghost_info = self.get_ghost_info()
        track_id = ghost_info["trackId"]
        return get_szs_common(iso_filename, track_id)

    def is_200cc(self):
        ghost_info = self.get_ghost_info()
        return ghost_info["200cc"]

    def get_ghost_info(self):
        if self.ghost_info is None:
            ghost_info, status_code = chadsoft.get(f"/rkgd/{self.ghost_id}.json", cache_settings=self.cache_settings)
            if status_code == 404:
                raise RuntimeError(f"Chadsoft ghost page \"{self.ghost_page_link}\" doesn't exist!")

            self.ghost_info = ghost_info

        return self.ghost_info

    def get_controller(self):
        ghost_info = self.get_ghost_info()
        return ghost_info["controller"]

    def get_track_name(self):
        ghost_info = self.get_ghost_info()
        return ghost_info.get("trackName")

    @staticmethod
    def is_ghost_page_link(ghost_page_link):
        match_obj = ghost_page_link_regex.match(ghost_page_link)
        return match_obj is not None

lb_href_regex = re.compile(r"^(/leaderboard/[0-1][0-9A-Fa-f]/[0-9A-Fa-f]{40}/)(00|01|02|04|05|06)((?:-fast-lap)?).json")

class Leaderboard:
    __slots__ = ("lb_link", "num_entries", "lb_info_and_entries", "cache_settings", "vehicle", "continent")

    def __init__(self, lb_link, num_entries, cache_settings):
        self.lb_link = lb_link
        self.num_entries = num_entries
        self.lb_info_and_entries = {}
        self.cache_settings = cache_settings
        self.vehicle = None

    def download_info_and_ghosts(self, do_not_download_ghosts=False):
        self.lb_info_and_entries, self.vehicle, self.continent = get_lb_from_lb_link(self.lb_link, self.num_entries, cache_settings=self.cache_settings)

        if do_not_download_ghosts:
            return

        for lb_entry in self.lb_info_and_entries["ghosts"]:
            rkg_data, status_code = chadsoft.get(lb_entry["href"], is_binary=True, cache_settings=self.cache_settings)

            if status_code == 404:
                rkg_data = None

            lb_entry["rkg_data"] = rkg_data

    def get_szs_if_not_default_track(self, iso_filename):
        if self.lb_info_and_entries["defaultTrack"]:
            return None

        return get_szs_common(iso_filename, self.lb_info_and_entries["trackId"])

    def is_200cc(self):
        return self.lb_info_and_entries["200cc"]

    def get_track_name(self):
        return self.lb_info_and_entries.get("name")

    def get_lb_link(self):
        return self.lb_link

    def get_vehicle(self):
        return self.vehicle

    def get_continent(self):
        return self.continent

    def is_vanilla_track(self):
        return self.lb_info_and_entries.get("defaultTrack")

    leaderboard_category_combinations_to_community_category_names = {
        frozenset((CATEGORY_SHORTCUT, CATEGORY_GLITCH, CATEGORY_NO_SHORTCUT)): {
            CATEGORY_SHORTCUT: "Shortcut",
            CATEGORY_GLITCH: "Glitch",
            CATEGORY_NO_SHORTCUT: "No Glitch, No-SC"
        },
        frozenset((CATEGORY_NORMAL_200CC, CATEGORY_GLITCH_200CC, CATEGORY_NO_SHORTCUT_200CC)): {
            CATEGORY_NORMAL_200CC: "Shortcut",
            CATEGORY_GLITCH_200CC: "Glitch",
            CATEGORY_NO_SHORTCUT_200CC: "No Glitch, No-SC"
        },
        frozenset((CATEGORY_SHORTCUT, CATEGORY_NO_SHORTCUT)): {
            CATEGORY_SHORTCUT: "Shortcut",
            CATEGORY_NO_SHORTCUT: "No-shortcut"
        },
        frozenset((CATEGORY_NORMAL_200CC, CATEGORY_NO_SHORTCUT_200CC)): {
            CATEGORY_NORMAL_200CC: "Shortcut",
            CATEGORY_NO_SHORTCUT_200CC: "No-shortcut"
        },
        frozenset((CATEGORY_NORMAL, CATEGORY_GLITCH)): {
            CATEGORY_NORMAL: "SPECIAL_NO_GLITCH_OR_NONE",
            CATEGORY_GLITCH: "Glitch",
        },
        frozenset((CATEGORY_NORMAL_200CC, CATEGORY_GLITCH_200CC)): {
            CATEGORY_NORMAL_200CC: "SPECIAL_NO_GLITCH_OR_NONE",
            CATEGORY_GLITCH_200CC: "Glitch"
        },
        frozenset((CATEGORY_NORMAL,)): {
            CATEGORY_NORMAL: ""
        },
        frozenset((CATEGORY_NORMAL_200CC,)): {
            CATEGORY_NORMAL_200CC: ""
        }
    }

    def add_track_category_id(self, all_track_categories, category_id):
        all_track_categories.add(category_id)

    def determine_community_category_name(self):
        category_id = self.lb_info_and_entries.get("categoryId", -1)
        if category_id == -1:
            return ""

        if not self.is_200cc():
            json_categories_to_check = {"00", "01", "02"}
        else:
            json_categories_to_check = {"04", "05", "06"}

        match_obj = lb_href_regex.match(self.lb_info_and_entries["_links"]["self"]["href"])
        if match_obj is None:
            raise RuntimeError("This shouldn't happen, please contact the developer!")

        track_lb_base = match_obj.group(1)
        json_category = match_obj.group(2)
        fast_lap = match_obj.group(3)

        json_categories_to_check.remove(json_category)
        all_track_categories = set()
        self.add_track_category_id(all_track_categories, category_id)

        for json_category_to_check in json_categories_to_check:
            other_category_lb_href = f"{track_lb_base}{json_category_to_check}{fast_lap}.json"
            other_category_lb, status = chadsoft.get_lb_from_href_with_status(other_category_lb_href, start=0, limit=1, times="pb", cache_settings=self.cache_settings)
            if status != 404:
                other_category_id = other_category_lb.get("categoryId", -1)
                self.add_track_category_id(all_track_categories, other_category_id)

        frozen_all_track_categories = frozenset(all_track_categories)
        community_category_names_for_lb = Leaderboard.leaderboard_category_combinations_to_community_category_names.get(frozen_all_track_categories)
        if community_category_names_for_lb is None:
            return identifiers.category_names_no_200cc[category_id]

        community_category_name = community_category_names_for_lb[category_id]
        if community_category_name == "SPECIAL_NO_GLITCH_OR_NONE":
            community_category_name = "No Glitch" if self.is_vanilla_track() else ""

        return community_category_name

    def test_community_category_name(self, expected):
        actual = self.determine_community_category_name()
        if actual != expected:
            print(f"FAIL: {self.lb_link} expected {expected} got {actual}")
        else:
            print(f"SUCCESS: {self.lb_link}")


# ===
# if default:
# if 00:-1
# (nothing)
# https://chadsoft.co.uk/time-trials/leaderboard/08/1AE1A7D894960B38E09E7494373378D87305A163/00.html
# https://chadsoft.co.uk/time-trials/leaderboard/16/8BFE0DEF91391D0E1930F04662C23CCD407C70E9/00.html
# https://chadsoft.co.uk/time-trials/leaderboard/14/8C854B087417A92425110CC71E23C944D6997806/04.html
# https://chadsoft.co.uk/time-trials/leaderboard/0F/888CA2E0257D24BEDCA93713E0B6CBE384CC9B35/04.html

# if Shortcut, Glitch, No-shortcut (150cc)
# if 00:16, 01:01, 02:02
# 16 -> Shortcut
# 01 -> Glitch
# 02 -> No Glitch, No SC
# https://chadsoft.co.uk/time-trials/leaderboard/02/0E380357AFFCFD8722329994885699D9927F8276/00.html
# https://chadsoft.co.uk/time-trials/leaderboard/05/E4BF364CB0C5899907585D731621CA930A4EF85C/00.html

# if Normal, Glitch, No-shortcut (200cc)
# if 04:04, 05:05, 06:06
# 04 -> Shortcut
# 05 -> Glitch
# 06 -> No Glitch, No SC
# https://chadsoft.co.uk/time-trials/leaderboard/0C/B9821B14A89381F9C015669353CB24D7DB1BB25D/04.html
# https://www.chadsoft.co.uk/time-trials/leaderboard/0D/B615BC0F9BD549E05146C76B2E40F08D272B8395/04.html

# if Shortcut, No-shortcut (150cc)
# if 00:16, 02:02
# 16 -> Shortcut
# 02 -> No-shortcut
# https://chadsoft.co.uk/time-trials/leaderboard/0C/B9821B14A89381F9C015669353CB24D7DB1BB25D/00.html
# https://chadsoft.co.uk/time-trials/leaderboard/03/F1A761F9A647F9C702936587F2DB281D87437641/00.html

# if Normal, No-shortcut (200cc)
# if 04:04, 06:06
# 04 -> Shortcut
# 06 -> No-shortcut
# https://chadsoft.co.uk/time-trials/leaderboard/04/1896AEA49617A571C66FF778D8F2ABBE9E5D7479/04.html
# https://www.chadsoft.co.uk/time-trials/leaderboard/02/0995EDD37C5265D4267FE80F1C2538D9D70A50C9/04.html

# if Normal, Glitch, Vanilla (150cc)
# if 00:00, 01:01, vanilla
# 00 -> No Glitch
# 01 -> Glitch
# https://chadsoft.co.uk/time-trials/leaderboard/0B/48EBD9D64413C2B98D2B92E5EFC9B15ECD76FEE6/00.html
# https://chadsoft.co.uk/time-trials/leaderboard/19/071D697C4DDB66D3B210F36C7BF878502E79845B/00.html

# if Normal, Glitch, Vanilla (200cc)
# if 04:04, 05:05
# 04 -> No Glitch
# 05 -> Glitch
# https://chadsoft.co.uk/time-trials/leaderboard/0D/FFE518915E5FAAA889057C8A3D3E439868574508/04.html
# https://chadsoft.co.uk/time-trials/leaderboard/1F/E8ED31605CC7D6660691998F024EED6BA8B4A33F/04.html

# if Normal, Glitch, Custom (150cc)
# if 00:00, 01:01, Custom
# 00 -> (nothing)
# 01 -> Glitch
# https://chadsoft.co.uk/time-trials/leaderboard/1E/5A5EFA90E4A83E4F873E2728F25A994451E8DB4A/00.html
# https://chadsoft.co.uk/time-trials/leaderboard/0E/882AFADD91CD261E941BEE24A563FAE51F7FF661/00.html

# if Normal, Glitch, Custom (200cc)
# if 04:04, 05:05, Custom
# 00 -> (nothing)
# 01 -> Glitch
# https://chadsoft.co.uk/time-trials/leaderboard/13/8BA7E0A473F06577CEA3DFD73BE639E3DA3C9FF1/04.html
# https://chadsoft.co.uk/time-trials/leaderboard/0B/DA74F3399138CBABAA08182163ACE343F2746357/04.html

# if Normal (150cc)
# if 00:00
# (nothing)
# https://chadsoft.co.uk/time-trials/leaderboard/19/8C4EEED505F0862CBB490A0AC0BD334515895710/00.html
# https://chadsoft.co.uk/time-trials/leaderboard/18/22D1945EEE7D68E87C5033C2C195D11820233169/00.html

# if Normal (200cc)
# if 04:04
# (nothing)
# https://chadsoft.co.uk/time-trials/leaderboard/0D/CD19D287B6578A396C8A4EC77ACF0C633B5C75A8/04.html
# https://chadsoft.co.uk/time-trials/leaderboard/1E/CF7B757F4FFC9629896ED1EDDDCD6FDFFDC0DFA3/04.html

# error:
# return original category name


class CatTest:
    __slots__ = ("lb_link", "expected")

    def __init__(self, lb_link, expected):
        self.lb_link = lb_link
        self.expected = expected

class CatTestGroup:
    __slots__ = ("cc_150_a", "cc_150_b", "cc_200_a", "cc_200_b")

    def __init__(self, cc_150_a, cc_150_b, cc_200_a, cc_200_b):
        self.cc_150_a = cc_150_a
        self.cc_150_b = cc_150_b
        self.cc_200_a = cc_200_a
        self.cc_200_b = cc_200_b

community_category_names_test = [
    CatTestGroup(
        cc_150_a=[CatTest("https://chadsoft.co.uk/time-trials/leaderboard/08/1AE1A7D894960B38E09E7494373378D87305A163/00.html", "")],
        cc_150_b=[CatTest(
        "https://chadsoft.co.uk/time-trials/leaderboard/16/8BFE0DEF91391D0E1930F04662C23CCD407C70E9/00.html", "")],
        cc_200_a=[CatTest(
        "https://chadsoft.co.uk/time-trials/leaderboard/14/8C854B087417A92425110CC71E23C944D6997806/04.html", "")],
        cc_200_b=[CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0F/888CA2E0257D24BEDCA93713E0B6CBE384CC9B35/04.html", "")],
    ),
    CatTestGroup(
        cc_150_a=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/02/0E380357AFFCFD8722329994885699D9927F8276/00.html", "Shortcut"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/02/0E380357AFFCFD8722329994885699D9927F8276/01.html", "Glitch"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/02/0E380357AFFCFD8722329994885699D9927F8276/02.html", "No Glitch, No-SC")
        ],
        cc_150_b=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/05/E4BF364CB0C5899907585D731621CA930A4EF85C/00.html", "Shortcut"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/05/E4BF364CB0C5899907585D731621CA930A4EF85C/01.html", "Glitch"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/05/E4BF364CB0C5899907585D731621CA930A4EF85C/02.html", "No Glitch, No-SC")
        ],
        cc_200_a=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0C/B9821B14A89381F9C015669353CB24D7DB1BB25D/04.html", "Shortcut"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0C/B9821B14A89381F9C015669353CB24D7DB1BB25D/05.html", "Glitch"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0C/B9821B14A89381F9C015669353CB24D7DB1BB25D/06.html", "No Glitch, No-SC")
        ],
        cc_200_b=[
            CatTest("https://www.chadsoft.co.uk/time-trials/leaderboard/0D/B615BC0F9BD549E05146C76B2E40F08D272B8395/04.html", "Shortcut"),
            CatTest("https://www.chadsoft.co.uk/time-trials/leaderboard/0D/B615BC0F9BD549E05146C76B2E40F08D272B8395/05.html", "Glitch"),
            CatTest("https://www.chadsoft.co.uk/time-trials/leaderboard/0D/B615BC0F9BD549E05146C76B2E40F08D272B8395/06.html", "No Glitch, No-SC")
        ]
    ),
    CatTestGroup(
        cc_150_a=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0C/B9821B14A89381F9C015669353CB24D7DB1BB25D/00.html", "Shortcut"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0C/B9821B14A89381F9C015669353CB24D7DB1BB25D/02.html", "No-shortcut"),
        ],
        cc_150_b=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/03/F1A761F9A647F9C702936587F2DB281D87437641/00.html", "Shortcut"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/03/F1A761F9A647F9C702936587F2DB281D87437641/02.html", "No-shortcut"),
        ],
        cc_200_a=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/04/1896AEA49617A571C66FF778D8F2ABBE9E5D7479/04.html", "Shortcut"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/04/1896AEA49617A571C66FF778D8F2ABBE9E5D7479/06.html", "No-shortcut"),
        ],
        cc_200_b=[
            CatTest("https://www.chadsoft.co.uk/time-trials/leaderboard/02/0995EDD37C5265D4267FE80F1C2538D9D70A50C9/04.html", "Shortcut"),
            CatTest("https://www.chadsoft.co.uk/time-trials/leaderboard/02/0995EDD37C5265D4267FE80F1C2538D9D70A50C9/06.html", "No-shortcut"),
        ],
    ),
    CatTestGroup(
        cc_150_a=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0B/48EBD9D64413C2B98D2B92E5EFC9B15ECD76FEE6/00.html", "No Glitch"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0B/48EBD9D64413C2B98D2B92E5EFC9B15ECD76FEE6/01.html", "Glitch"),
        ],
        cc_150_b=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/19/071D697C4DDB66D3B210F36C7BF878502E79845B/00.html", "No Glitch"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/19/071D697C4DDB66D3B210F36C7BF878502E79845B/01.html", "Glitch"),
        ],
        cc_200_a=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0D/FFE518915E5FAAA889057C8A3D3E439868574508/04.html", "No Glitch"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0D/FFE518915E5FAAA889057C8A3D3E439868574508/05.html", "Glitch"),
        ],
        cc_200_b=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/1F/E8ED31605CC7D6660691998F024EED6BA8B4A33F/04.html", "No Glitch"),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/1F/E8ED31605CC7D6660691998F024EED6BA8B4A33F/05.html", "Glitch"),
        ],
    ),
    CatTestGroup(
        cc_150_a=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/1E/5A5EFA90E4A83E4F873E2728F25A994451E8DB4A/00.html", ""),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/1E/5A5EFA90E4A83E4F873E2728F25A994451E8DB4A/01.html", "Glitch"),
        ],
        cc_150_b=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0E/882AFADD91CD261E941BEE24A563FAE51F7FF661/00.html", ""),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0E/882AFADD91CD261E941BEE24A563FAE51F7FF661/01.html", "Glitch"),
        ],
        cc_200_a=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/13/8BA7E0A473F06577CEA3DFD73BE639E3DA3C9FF1/04.html", ""),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/13/8BA7E0A473F06577CEA3DFD73BE639E3DA3C9FF1/05.html", "Glitch"),
        ],
        cc_200_b=[
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0B/DA74F3399138CBABAA08182163ACE343F2746357/04.html", ""),
            CatTest("https://chadsoft.co.uk/time-trials/leaderboard/0B/DA74F3399138CBABAA08182163ACE343F2746357/05.html", "Glitch"),
        ],
    ),
    CatTestGroup(
        cc_150_a=[CatTest("https://chadsoft.co.uk/time-trials/leaderboard/19/8C4EEED505F0862CBB490A0AC0BD334515895710/00.html", "")],
        cc_150_b=[CatTest(
        "https://chadsoft.co.uk/time-trials/leaderboard/18/22D1945EEE7D68E87C5033C2C195D11820233169/00.html", "")],
        cc_200_a=[CatTest(
        "https://chadsoft.co.uk/time-trials/leaderboard/0D/CD19D287B6578A396C8A4EC77ACF0C633B5C75A8/04.html", "")],
        cc_200_b=[CatTest("https://chadsoft.co.uk/time-trials/leaderboard/1E/CF7B757F4FFC9629896ED1EDDDCD6FDFFDC0DFA3/04.html", "")],
    ),
]

cat_test_cache_settings = CacheSettings(True, True, "chadsoft_cached", retry_on_empty=False)

def test_cat_tests(cat_tests):
    for cat_test in cat_tests:
        try:
            leaderboard = Leaderboard(cat_test.lb_link, 1, cat_test_cache_settings)
            leaderboard.download_info_and_ghosts(True)
            leaderboard.test_community_category_name(cat_test.expected)
        except Exception as e:
            print(f"FAIL due to error: {cat_test.lb_link}\nError below:\n{e}\n{''.join(traceback.format_tb(e.__traceback__))}\n")

def test_all_community_category_names():
    purge_cache("24h", "chadsoft_cached")
    random.seed(1111236)

    for cat_test_group in community_category_names_test:
        if False:
            cc_150_cat_tests = cat_test_group.cc_150_a
        else:
            cc_150_cat_tests = cat_test_group.cc_150_b
            
        if False:
            cc_200_cat_tests = cat_test_group.cc_200_a
        else:
            cc_200_cat_tests = cat_test_group.cc_200_b

        test_cat_tests(cc_150_cat_tests)
        test_cat_tests(cc_200_cat_tests)

def main():
    test_all_community_category_names()

if __name__ == "__main__":
    main()