import requests
import urllib
import pathlib
import json
import time
import re
import identifiers
import chadsoft
import chadsoft_config

API_URL = "https://tt.chadsoft.co.uk"

def get(endpoint, params=None, is_binary=False, try_cached=chadsoft_config.TRY_CACHED, rate_limit=chadsoft_config.RATE_LIMIT):
    if params is None:
        params = {}

    if try_cached:
        if not is_binary:
            endpoint_as_pathname = f"chadsoft_cached/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}.json"
        else:
            endpoint_as_pathname = f"chadsoft_cached/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}.rkg"
        endpoint_as_path = pathlib.Path(endpoint_as_pathname)
        if endpoint_as_path.is_file():
            if endpoint_as_path.stat().st_size == 0:
                if not is_binary:
                    return {}, 404
                else:
                    return bytes(), 404

            if not is_binary:
                with open(endpoint_as_path, "r") as f:
                    data = json.load(f)
            else:
                with open(endpoint_as_path, "rb") as f:
                    data = f.read()

            return data, 200
    else:
        endpoint_as_path = None

    url = f"{API_URL}{endpoint}"
    print(f"url: {url}?{urllib.parse.urlencode(params, doseq=True)}")
    start_time = time.time()
    r = requests.get(url, params=params)
    end_time = time.time()
    print(f"Request took {end_time - start_time}.")

    if try_cached:
        endpoint_as_path.parent.mkdir(parents=True, exist_ok=True)

    if r.status_code != 200:
        if try_cached:
            endpoint_as_path.touch()
        return r.reason, r.status_code
        #raise RuntimeError(f"API returned {r.status_code}: {r.reason}")

    if not is_binary:
        data = r.json()
    else:
        data = r.content

    if try_cached:
        endpoint_as_path.parent.mkdir(parents=True, exist_ok=True)
        if not is_binary:
            with open(endpoint_as_path, "w+") as f:
                f.write(r.text)
        else:
            with open(endpoint_as_path, "wb+") as f:
                f.write(r.content)

    if rate_limit:
        time.sleep(1)

    return data, r.status_code

def get_lb_from_href(endpoint, start=0, limit=1, continent=None, vehicle=None, times="pb", override_cache=None, try_cached=chadsoft_config.TRY_CACHED, rate_limit=chadsoft_config.RATE_LIMIT):
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

    return get(endpoint, params, try_cached=try_cached, rate_limit=rate_limit)[0]

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

def get_top_10_lb_from_lb_link(lb_link):
    match_obj = leaderboard_regex.match(lb_link)
    if not match_obj:
        raise RuntimeError("Invalid chadsoft leaderbord link!")

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
                        vehicle = vehicle_ids_by_filter_name[filter_value]
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

    top_10_leaderboard = get_lb_from_href(f"/leaderboard/{slot_id_track_sha1}.json", start=0, limit=10, continent=continent, vehicle=vehicle, times=times)

    if len(top_10_leaderboard["ghosts"]) == 0:
        raise RuntimeError("Leaderboard is empty!")

    return top_10_leaderboard
