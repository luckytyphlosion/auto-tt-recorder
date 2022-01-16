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
import identifiers
import chadsoft
import chadsoft_config
import wbz
import wiimm

API_URL = "https://tt.chadsoft.co.uk"

def get_cached_endpoint_filepath(endpoint, params, is_binary):
    if not is_binary:
        endpoint_as_pathname = f"chadsoft_cached/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}.json"
    else:
        endpoint_as_pathname = f"chadsoft_cached/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}.rkg"

    return pathlib.Path(endpoint_as_pathname)


def get(endpoint, params=None, is_binary=False, read_cache=False, write_cache=True, rate_limit=chadsoft_config.RATE_LIMIT):
    exception_sleep_time = 15

    while True:
        try:
            return get_in_loop_code(endpoint, params, is_binary, read_cache, write_cache, rate_limit)
        except ConnectionError as e:
            print(f"Exception occurred: {e}\n{''.join(traceback.format_tb(e.__traceback__))}\nSleeping for {exception_sleep_time} seconds now.")
            time.sleep(exception_sleep_time)
            exception_sleep_time *= 2
            if exception_sleep_time > 1000:
                exception_sleep_time = 1000

def get_in_loop_code(endpoint, params, is_binary, read_cache, write_cache, rate_limit):
    if params is None:
        params = {}

    endpoint_as_path = get_cached_endpoint_filepath(endpoint, params, is_binary)
    if read_cache and endpoint_as_path.is_file():
        if endpoint_as_path.stat().st_size == 0:
            if not is_binary:
                return {}, 404
            else:
                return bytes(), 404

        if not is_binary:
            #print(f"endpoint_as_path: {endpoint_as_path}")
            with open(endpoint_as_path, "r", encoding="utf-8-sig") as f:
                content = f.read().encode("utf-8")
                data = json.loads(content)
        else:
            with open(endpoint_as_path, "rb") as f:
                data = f.read()

        return data, 200

    url = f"{API_URL}{endpoint}"
    print(f"url: {url}?{urllib.parse.urlencode(params, doseq=True)}")
    start_time = time.time()
    r = requests.get(url, params=params)
    end_time = time.time()
    print(f"Request took {end_time - start_time}.")

    if write_cache:
        endpoint_as_path.parent.mkdir(parents=True, exist_ok=True)

    if r.status_code != 200:
        if write_cache:
            endpoint_as_path.touch()
        return r.reason, r.status_code
        #raise RuntimeError(f"API returned {r.status_code}: {r.reason}")

    if not is_binary:
        data = json.loads(r.content.decode("utf-8-sig"))
    else:
        data = r.content

    if write_cache:
        endpoint_as_path.parent.mkdir(parents=True, exist_ok=True)
        if not is_binary:
            with open(endpoint_as_path, "w+", encoding="utf-8-sig") as f:
                f.write(r.text)
        else:
            with open(endpoint_as_path, "wb+") as f:
                f.write(r.content)

    if rate_limit:
        time.sleep(1)

    return data, r.status_code

def get_lb_from_href(endpoint, start=0, limit=1, continent=None, vehicle=None, times="pb", override_cache=None, read_cache=False, write_cache=True, rate_limit=chadsoft_config.RATE_LIMIT):
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

    return get(endpoint, params, read_cache=read_cache, write_cache=write_cache, rate_limit=rate_limit)[0]

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

leaderboard_regex = re.compile(r"^https://(?:www\.)?chadsoft\.co\.uk/time-trials/leaderboard/([0-1][0-9A-Fa-f]/[0-9A-Fa-f]{40}/(?:00|01|02|03|04|05|06))\.html(.*)$")

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

def get_lb_from_lb_link(lb_link, num_entries, read_cache=False, write_cache=True):
    match_obj = leaderboard_regex.match(lb_link)
    if not match_obj:
        raise RuntimeError("Invalid chadsoft leaderboard link!")

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
                if filter_value in ("karts", "bikes"):
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

    top_n_leaderboard = get_lb_from_href(f"/leaderboard/{slot_id_track_sha1}.json", start=0, limit=num_entries, continent=continent, vehicle=vehicle, times=times, read_cache=read_cache, write_cache=write_cache)

    if len(top_n_leaderboard["ghosts"]) == 0:
        raise RuntimeError("Leaderboard is empty!")

    return top_n_leaderboard

ghost_page_link_regex = re.compile(r"^https://(?:www\.)?chadsoft\.co\.uk/time-trials/rkgd/([0-9A-Fa-f]{2}/[0-9A-Fa-f]{2}/[0-9A-Fa-f]{36})\.html$")

default_track_sha1s = {"1AE1A7D894960B38E09E7494373378D87305A163", "90720A7D57A7C76E2347782F6BDE5D22342FB7DD", "0E380357AFFCFD8722329994885699D9927F8276", "1896AEA49617A571C66FF778D8F2ABBE9E5D7479", "7752BB51EDBC4A95377C0A05B0E0DA1503786625", "E4BF364CB0C5899907585D731621CA930A4EF85C", "B02ED72E00B400647BDA6845BE387C47D251F9D1", "D1A453B43D6920A78565E65A4597E353B177ABD0", "72D0241C75BE4A5EBD242B9D8D89B1D6FD56BE8F", "52F01AE3AED1E0FA4C7459A648494863E83A548C", "48EBD9D64413C2B98D2B92E5EFC9B15ECD76FEE6", "ACC0883AE0CE7879C6EFBA20CFE5B5909BF7841B", "38486C4F706395772BD988C1AC5FA30D27CAE098", "B13C515475D7DA207DFD5BADD886986147B906FF", "B9821B14A89381F9C015669353CB24D7DB1BB25D", "FFE518915E5FAAA889057C8A3D3E439868574508", "8014488A60F4428EEF52D01F8C5861CA9565E1CA", "8C854B087417A92425110CC71E23C944D6997806", "071D697C4DDB66D3B210F36C7BF878502E79845B", "49514E8F74FEA50E77273C0297086D67E58123E8", "BA9BCFB3731A6CB17DBA219A8D37EA4D52332256", "E8ED31605CC7D6660691998F024EED6BA8B4A33F", "BC038E163D21D9A1181B60CF90B4D03EFAD9E0C5", "418099824AF6BF1CD7F8BB44F61E3A9CC3007DAE", "4EC538065FDC8ACF49674300CBDEC5B80CC05A0D", "A4BEA41BE83D816F793F3FAD97D268F71AD99BF9", "692D566B05434D8C66A55BDFF486698E0FC96095", "1941A29AD2E7B7BBA8A29E6440C95EF5CF76B01D", "077111B996E5C4F47D20EC29C2938504B53A8E76", "F9A62BEF04CC8F499633E4023ACC7675A92771F0", "B036864CF0016BE0581449EF29FB52B2E58D78A4", "15B303B288F4707E5D0AF28367C8CE51CDEAB490"}

def get_szs_common(iso_filename, track_id):
    if track_id in default_track_sha1s:
        return None

    wit_filename, wszst_filename = wiimm.get_wit_wszst_filename()

    wbz_converter = wbz.WbzConverter(
        iso_filename=iso_filename,
        original_track_files_dirname="storage/original-race-course",
        wit_filename=wit_filename,
        wszst_filename=wszst_filename,
        auto_add_containing_dirname="storage"
    )

    szs_filename = wbz_converter.download_wbz_convert_to_szs_get_szs_filename(track_id)
    return szs_filename

class GhostPage:
    __slots__ = ("ghost_page_link", "ghost_id", "read_cache", "write_cache", "ghost_info")

    def __init__(self, ghost_page_link, read_cache=False, write_cache=True):
        self.ghost_page_link = ghost_page_link
        match_obj = ghost_page_link_regex.match(ghost_page_link)
        if not match_obj:
            raise RuntimeError("Invalid chadsoft ghost page link!")

        self.ghost_id = match_obj.group(1)
        self.read_cache = read_cache
        self.write_cache = write_cache
        self.ghost_info = None

    def get_rkg(self):
        rkg_data, status_code = chadsoft.get(f"/rkgd/{self.ghost_id}.rkg", is_binary=True, read_cache=self.read_cache, write_cache=self.write_cache)
    
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
            ghost_info, status_code = chadsoft.get(f"/rkgd/{self.ghost_id}.json", read_cache=self.read_cache, write_cache=self.write_cache)
            if status_code == 404:
                raise RuntimeError(f"Chadsoft ghost page \"{self.ghost_page_link}\" doesn't exist!")

            self.ghost_info = ghost_info

        return self.ghost_info

class Leaderboard:
    __slots__ = ("lb_link", "num_entries", "lb_info_and_entries", "read_cache", "write_cache")

    def __init__(self, lb_link, num_entries, read_cache=False, write_cache=True):
        self.lb_link = lb_link
        self.num_entries = num_entries
        self.lb_info_and_entries = {}
        self.read_cache = read_cache
        self.write_cache = write_cache

    def download_info_and_ghosts(self):
        self.lb_info_and_entries = get_lb_from_lb_link(self.lb_link, self.num_entries, read_cache=self.read_cache, write_cache=self.write_cache)

        for lb_entry in self.lb_info_and_entries["ghosts"]:
            rkg_data, status_code = chadsoft.get(lb_entry["href"], is_binary=True, read_cache=self.read_cache, write_cache=self.write_cache)

            if status_code == 404:
                rkg_data = None

            lb_entry["rkg_data"] = rkg_data

    def get_szs_if_not_default_track(self, iso_filename):
        if self.lb_info_and_entries["defaultTrack"]:
            return None

        return get_szs_common(iso_filename, self.lb_info_and_entries["trackId"])

    def is_200cc(self):
        return self.lb_info_and_entries["200cc"]
