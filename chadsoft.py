import requests
import urllib
import pathlib
import json
import time

API_URL = "https://tt.chadsoft.co.uk"

def get(endpoint, params, is_binary=False, try_cached=True, rate_limit=True):
    if try_cached:
        endpoint_as_pathname = f"chadsoft_cached/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}.json"
        endpoint_as_path = pathlib.Path(endpoint_as_pathname)
        if endpoint_as_path.is_file():
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
    if r.status_code != 200:
        return r.reason, r.status_code
        raise RuntimeError(f"API returned {r.status_code}: {r.reason}")

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
        time.sleep(5)

    return data, r.status_code

def get_lb_from_href(endpoint, start=0, limit=1, continent=None, vehicle=None, times="pb", override_cache=None, try_cached=True, rate_limit=True):
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
