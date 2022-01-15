# =============================================================================
# MIT License
# 
# Copyright (c) 2021 luckytyphlosion
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
# =============================================================================
import bs4
import requests
import json
import re
import time
import urllib
import pathlib
import collections
import wbz

family_info_row_id_regex = re.compile(r"^p1-[0-9]+-0$")
track_id_regex = re.compile(r"a class=jii href=\"(/j/[0-9]+)\"")


ctgp_distribs = ("https://ct.wiimm.de/dis/106", "https://ct.wiimm.de/dis/49", "https://ct.wiimm.de/dis/50", "https://ct.wiimm.de/dis/51", "https://ct.wiimm.de/dis/52", "https://ct.wiimm.de/dis/53", "https://ct.wiimm.de/dis/54", "https://ct.wiimm.de/dis/55", "https://ct.wiimm.de/dis/56", "https://ct.wiimm.de/dis/57", "https://ct.wiimm.de/dis/58", "https://ct.wiimm.de/dis/46", "https://ct.wiimm.de/dis/107", "https://ct.wiimm.de/dis/164", "https://ct.wiimm.de/dis/165", "https://ct.wiimm.de/dis/166", "https://ct.wiimm.de/dis/167", "https://ct.wiimm.de/dis/168", "https://ct.wiimm.de/dis/169", "https://ct.wiimm.de/dis/170")

CTGP_200cc_DISTRIBUTION = "https://ct.wiimm.de/dis/58"

def get_cached_endpoint_filepath(endpoint, params):
    endpoint_as_pathname = f"legacy_records_cached/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}"

    return pathlib.Path(endpoint_as_pathname)

CONTENT_JSON = 0
CONTENT_TEXT = 1
CONTENT_BINARY = 2

# def get(endpoint, params=None, is_binary=False, read_cache=False, write_cache=True, rate_limit=chadsoft_config.RATE_LIMIT):
def requests_get_cached(endpoint, params=None, content_type=CONTENT_TEXT, read_cache=True, write_cache=True, rate_limit=True):
    if params is None:
        params = {}

    endpoint_as_path = get_cached_endpoint_filepath(endpoint, params)
    if read_cache and endpoint_as_path.is_file():
        if endpoint_as_path.stat().st_size == 0:
            if content_type == CONTENT_JSON:                
                return {}, 404
            elif content_type == CONTENT_TEXT:
                return "", 404
            else:
                return bytes(), 404

        if content_type == CONTENT_JSON:
            with open(endpoint_as_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        elif content_type == CONTENT_TEXT:
            with open(endpoint_as_path, "r", encoding="utf-8-sig") as f:
                data = f.read()
        else:
            with open(endpoint_as_path, "rb") as f:
                data = f.read()

        return data, 200

    url = endpoint
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

    if content_type == CONTENT_JSON:
        data = json.loads(r.content.decode("utf-8-sig"))
    elif content_type == CONTENT_TEXT:
        data = r.text
    else:
        data = r.content

    if write_cache:
        if content_type != CONTENT_BINARY:
            with open(endpoint_as_path, "w+", encoding="utf-8-sig") as f:
                f.write(r.text)
        else:
            with open(endpoint_as_path, "wb+") as f:
                f.write(r.content)

    if rate_limit:
        time.sleep(1)

    return data, r.status_code

def add_track_manually_to_distribution_track_ids(all_distribution_track_ids, track_endpoint, check_200cc):
    all_distribution_track_ids[track_endpoint] = {
        "wiimm_track_id": track_endpoint,
        "check_200cc": check_200cc,
        "distributions": ["added manually"]
    }

def get_all_wiimm_ctgp_track_ids():
    all_distribution_track_ids = {}
    add_to_200cc = False

    for distribution in ctgp_distribs:
        print(f"Getting {distribution}")
        html_doc, status_code = requests_get_cached(distribution, content_type=CONTENT_TEXT)
        cur_distribution_track_ids = track_id_regex.findall(html_doc)
        if distribution == CTGP_200cc_DISTRIBUTION:
            print("Adding to 200cc now!")
            add_to_200cc = True

        for track_id in cur_distribution_track_ids:
            track_id_info = all_distribution_track_ids.get(track_id)
            if track_id_info is None:
                track_id_info = {
                    "wiimm_track_id": track_id,
                    "distributions": []
                }
            if track_id == "/j/0":
                print(f"/j/0 found in distribution {distribution}!")

            track_id_info["check_200cc"] = add_to_200cc
            track_id_info["distributions"].append(distribution)
            all_distribution_track_ids[track_id] = track_id_info

    del all_distribution_track_ids["/j/0"]
    # heart of china is missing, see https://discord.com/channels/485882824881209345/485900922468433920/931688063090970624
    add_track_manually_to_distribution_track_ids(all_distribution_track_ids, "/j/7000", True)
    # undiscovered offlimit v1 missing
    add_track_manually_to_distribution_track_ids(all_distribution_track_ids, "/j/1892", False)
    add_track_manually_to_distribution_track_ids(all_distribution_track_ids, "/j/1975", True)
    add_track_manually_to_distribution_track_ids(all_distribution_track_ids, "/j/6999", True)
    add_track_manually_to_distribution_track_ids(all_distribution_track_ids, "/j/7004", True)

    with open("wiimm_ctgp_track_ids.json", "w+") as f:
        json.dump(all_distribution_track_ids, f, indent=2)

n_sha1_aliases_regex = re.compile(r"[0-9] SHA1 aliases:")

def download_full_track_info(track_endpoint):
    return download_full_track_info_common(f"https://ct.wiimm.de{track_endpoint}")

def download_full_track_info_id_only(track_id):
    return download_full_track_info_common(f"https://ct.wiimm.de/i/{track_id}")

def download_full_track_info_common(full_track_endpoint):
    html_doc, status_code = requests_get_cached(full_track_endpoint, content_type=CONTENT_TEXT)
    html_doc = html_doc.replace(u"\u00A0", " ")
    track_info = {}
    soup = bs4.BeautifulSoup(html_doc, "html.parser")
    table_info = soup.find("table", class_="table-info")
    track_info["track_name_full"] = table_info.find("th").string

    # ================================
    # alternate code which finds the type_class_id via tag position
    # don't do this because some tags may be missing depending on the track
    # see: https://ct.wiimm.de/i/1700 https://ct.wiimm.de/i/1293 https://ct.wiimm.de/i/1500
    # table_rows = table_info.find_all_next("tr")
    # type_class_id = table_rows[1].find_all_next("td")[1].string
    # ================================
    type_class_id = table_info.find("td", string="Type, Class and Id:").next_sibling.string
    track_type, track_class, track_id_as_str = type_class_id.split(" / ")
    #if track_id != int(track_id_as_str):
    #    raise RuntimeError("Expected track_id == int(track_id_as_str)!")

    archive_info = {
        "type": track_type,
        "class": track_class,
        "id": int(track_id_as_str)
    }
    track_info["archive_info"] = archive_info
    track_name_and_version_tag = table_info.find("td", string="Track name and version:")
    if track_name_and_version_tag is not None:
        track_name_and_version_tag = track_name_and_version_tag.next_sibling
        track_name = track_name_and_version_tag.find("b").string
        track_version = track_name_and_version_tag.contents[1].strip()
    else:
        track_name = table_info.find("td", string="Track name:").next_sibling.find("b").string
        track_version = None

    track_info["name"] = track_name
    track_info["version"] = track_version
    author = table_info.find("td", string="Created by:")
    if author is not None:
        author = author.next_sibling.string

    track_info["author"] = author
    track_info["sha1s"] = [table_info.find("td", string="SHA1 checksum:").next_sibling.find("tt").string]
    sha1_alias_0 = table_info.find("td", string="SHA1 alias:")

    if sha1_alias_0 is not None:
        track_info["sha1s"].append(sha1_alias_0.next_sibling.find('tt').contents[0])
    else:
        sha1_aliases = table_info.find("td", string=n_sha1_aliases_regex)
        if sha1_aliases is not None:
            track_info["sha1s"].extend(sha1_aliases.next_sibling.find("tt").contents[0::2])
            #print(f"sha1_aliases: {}")
            #print(f"multiple sha1 aliases {track_endpoint}")

    #track_info["sha1_alias"] = sha1_alias


    
    # ==============================
    # alternate code to get archive info from the family box instead
    #family_info = soup.find("table", id="p1-table")
    #family_tracks = family_info.find_all("tr", id=family_info_row_id_regex)
    #
    #for family_track in family_tracks:
    #    family_track_tds = family_track.find_all_next('td')
    #    family_track_id = int(family_track_tds[1].string)
    #    if family_track_id == track_id:
    #        archive_info = {}
    #        archive_info["type"] = family_track.find("td", class_="ctype-1").string
    #        archive_info["class"] = family_track.find("td", class_="cclass").string
    #        archive_info["id"] = family_track_id
    #        track_info["archiveInfo"] = archive_info
    #        break
    #
    #   print(f"family_track_id: {family_track_id}")
    #   #print(f"track id: {family_track.find_all_next('td')[1]}")
    #   #print(f"family_track.contents: {family_track.contents}")
    # ==============================

    return track_info

def test_download_full_track_info():
    track_info = download_full_track_info("/j/6176")
    with open(f"track_info_6176.json", "w+") as f:
        json.dump(track_info, f, indent=2)

def get_all_wiimm_ctgp_full_track_info():
    with open("wiimm_ctgp_track_ids.json", "r") as f:
        all_distribution_track_ids = json.load(f)

    for track_endpoint, small_track_info in all_distribution_track_ids.items():
        track_info = download_full_track_info(track_endpoint)
        small_track_info.update(track_info)

    with open("wiimm_ctgp_full_track_info.json", "w+") as f:
        json.dump(all_distribution_track_ids, f, indent=2)

def download_missing_leaderboard(chadsoft_endpoint):
    missing_lb, status_code = requests_get_cached(chadsoft_endpoint, params={"start": 0, "limit": 0}, content_type=CONTENT_JSON)

    del missing_lb["ghosts"]
    missing_lb["_links"]["item"] = {"href": missing_lb["_links"]["self"]["href"]}
    del missing_lb["_links"]["index"]
    del missing_lb["_links"]["leaderboardFastLap"]
    return missing_lb

def merge_150cc_200cc_leaderboards():
    with open("leaderboards_pretty.json", "r", encoding="utf-8-sig") as f:
        leaderboards_and_info = json.load(f)

    with open("leaderboards-200cc.json", "r", encoding="utf-8-sig") as f:
        leaderboards_and_info_200cc = json.load(f)

    leaderboards_150cc = leaderboards_and_info["leaderboards"]
    leaderboards_200cc = leaderboards_and_info_200cc["leaderboards"]

    leaderboards_150cc.extend(leaderboards_200cc)

    # get volcano beach (missing from leaderboards.json)
    leaderboards_150cc.append(download_missing_leaderboard("https://tt.chadsoft.co.uk/leaderboard/15/34BFAA22C86C4C25600EF3CF265CF76F56D8D74F/00.json"))
    # glitch
    leaderboards_150cc.append(download_missing_leaderboard("https://tt.chadsoft.co.uk/leaderboard/15/34BFAA22C86C4C25600EF3CF265CF76F56D8D74F/01.json"))
    # snes koopa beach 1
    leaderboards_150cc.append(download_missing_leaderboard("https://tt.chadsoft.co.uk/leaderboard/10/C670A7A2DB56A5EA67501B5511EC2D08620740A6/00.json"))
    # comet starway v1.42
    leaderboards_150cc.append(download_missing_leaderboard("https://tt.chadsoft.co.uk/leaderboard/18/a98e1a357c92ba16b118552ecc701e784ee45e59/00.json"))
    # rosalina's snow world v1.1
    leaderboards_150cc.append(download_missing_leaderboard("https://tt.chadsoft.co.uk/leaderboard/1B/19ea4f67ab7bbd03aa295376c9a81d3f6a0fcf73/00.json"))
    # rosalina's snow world v1.1 200cc
    leaderboards_150cc.append(download_missing_leaderboard("https://tt.chadsoft.co.uk/leaderboard/1B/19ea4f67ab7bbd03aa295376c9a81d3f6a0fcf73/04.json"))
    # rosalina's snow world v1.1 200cc glitch
    leaderboards_150cc.append(download_missing_leaderboard("https://tt.chadsoft.co.uk/leaderboard/1B/19ea4f67ab7bbd03aa295376c9a81d3f6a0fcf73/05.json"))

    with open("leaderboards_combined.json", "w+") as f:
        json.dump(leaderboards_150cc, f, indent=2)

class TrackNameVersion:
    __slots__ = ("name", "version")

    def __init__(self, name, version):
        self.name = name
        self.version = version

    def __key(self):
        return (self.name, self.version)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, TrackNameVersion):
            return self.__key() == other.__key()
        return NotImplemented

def key_leaderboards_by_track_id_and_track_name_version_separately():
    with open("leaderboards_combined.json", "r") as f:
        leaderboards_all = json.load(f)

    leaderboards_by_track_id = collections.defaultdict(list)
    leaderboards_by_track_name_version = collections.defaultdict(list)

    for leaderboard in leaderboards_all:
        track_name = leaderboard.get("name")
        if track_name is not None:
            version = leaderboard.get("version")
            if track_name == "SNES Mario Circuit 1" and version == "v1.0":
                author = leaderboard.get("authors", [None])[0]
                track_nameversion = f"{track_name}|{version}|{author}"
            else:
                track_nameversion = f"{track_name}|{version}"
            #track_name_version = TrackNameVersion(track_name, version)
            leaderboards_by_track_name_version[track_nameversion].append(leaderboard)

        leaderboards_by_track_id[leaderboard["trackId"]].append(leaderboard)

    with open("leaderboards_combined_by_id.json", "w+") as f:
        json.dump(leaderboards_by_track_id, f, indent=2)

    with open("leaderboards_combined_by_track_name_version.json", "w+") as f:
        json.dump(leaderboards_by_track_name_version, f, indent=2)

def get_tracks_in_current_ctgp():
    with open("ctgp-leaderboards_1120.json", "r", encoding="utf-8-sig") as f:
        leaderboards_current = json.load(f)

    current_tracks = {}

    for leaderboard in leaderboards_current["leaderboards"]:
        current_tracks[leaderboard["trackId"]] = leaderboard

    with open("ctgp_current_tracks.json", "w+") as f:
        json.dump(current_tracks, f, indent=2)

def get_ghost_count_of_leaderboards_for_track_id(all_leaderboards_for_track_id):
    return sum(leaderboard["ghostCount"] for leaderboard in all_leaderboards_for_track_id if not leaderboard["200cc"])

def calc_ctgp_tracks_from_wiimm_data():
    with open("leaderboards_combined_by_id.json", "r") as f:
        leaderboards_by_track_id = json.load(f)

    with open("wiimm_ctgp_full_track_info.json", "r") as f:
        wiimm_info = json.load(f)

    with open("ctgp_current_tracks.json", "r") as f:
        current_tracks = json.load(f)

    removed_tracks = {}

    for track_endpoint, wiimm_track_info in wiimm_info.items():
        if track_endpoint in ("/j/1399", "/j/1049", "/j/7036", "/j/7047", "/j/1575", "/j/7041", "/j/6953"):
            print(f"Skipping {wiimm_track_info['track_name_full']}! (Known wiimm archive error)")
            continue

        track_id = None
        
        for sha1 in wiimm_track_info["sha1s"]:
            sha1 = sha1.upper()
            possible_all_leaderboards_for_track_id = leaderboards_by_track_id.get(sha1)
            if possible_all_leaderboards_for_track_id is not None:
                if track_id is None:
                    track_id = sha1
                    all_leaderboards_for_track_id = possible_all_leaderboards_for_track_id
                    best_lb_candidate_150cc_ghost_count = get_ghost_count_of_leaderboards_for_track_id(all_leaderboards_for_track_id)
                else:
                    cur_lb_candidate_150cc_ghost_count = get_ghost_count_of_leaderboards_for_track_id(possible_all_leaderboards_for_track_id)
                    if cur_lb_candidate_150cc_ghost_count > best_lb_candidate_150cc_ghost_count:
                        track_id = sha1
                        all_leaderboards_for_track_id = possible_all_leaderboards_for_track_id
                        best_lb_candidate_150cc_ghost_count = cur_lb_candidate_150cc_ghost_count
                    elif cur_lb_candidate_150cc_ghost_count == best_lb_candidate_150cc_ghost_count:
                        raise RuntimeError(f"Track {wiimm_track_info['track_name_full']} has tie in 150cc ghost count!")
                        
                    #print(all_leaderboards_for_track_id)
                    #raise RuntimeError(f" has multiple entries in Chadsoft!")

        if track_id is None:
            if track_endpoint == "/j/7048":
                track_id = "204DAB356B6725DB1229B382BE5E1E910269D6BF"
                all_leaderboards_for_track_id = leaderboards_by_track_id.get(track_id)
                best_lb_candidate_150cc_ghost_count = get_ghost_count_of_leaderboards_for_track_id(all_leaderboards_for_track_id)
                wiimm_track_info["track_name_full"] = "DS Wario Stadium v1.1b (zilly) [r64]"
            else:
                raise RuntimeError(f"Track ({wiimm_track_info['track_name_full']}) found in wiimm's archive but not CTGP!")

        if best_lb_candidate_150cc_ghost_count < 100:
            print(f"Warning: guessed track {track_id} ({wiimm_track_info['track_name_full']}) found has unusual 150cc ghost count of {best_lb_candidate_150cc_ghost_count}")

        if track_id not in current_tracks:
            all_leaderboards_for_track_id_plus_check_200cc = {
                "leaderboards": all_leaderboards_for_track_id,
                "check_200cc": wiimm_track_info["check_200cc"],
                "track_name_full": wiimm_track_info["track_name_full"],
                "missing_from_archive": track_id in ("9F09DDB05BC5C7B04BB7AA120F6D0F21774143EB", "A1E5087B9951410F9B590FD1D6D831357167A3B6"),
                "wiimm_version": wiimm_track_info["version"],
            }
            removed_tracks[track_id] = all_leaderboards_for_track_id_plus_check_200cc

    with open("removed_ctgp_tracks_pt1.json", "w+") as f:
        json.dump(removed_tracks, f, indent=2)

def print_removed_tracks_pt1():
    with open("removed_ctgp_tracks_pt1.json", "r") as f:
        removed_tracks_pt1 = json.load(f)

    output = ""
    for track_id, track_lb_info in removed_tracks_pt1.items():
        output += f"{track_lb_info['track_name_full']}\n"

    with open("removed_ctgp_tracks_pt1_out.txt", "w+") as f:
        f.write(output)

changelog_track_name_regex = re.compile(r"(.+)\s+\(([^\)]+)\)")

new_track_nameversion_to_actual_nameversion = {
    "Daisy's Palace|v1.3.alt": "Daisy's Palace|v1.3-a",
    "Athletic Raceway|v1.02.ctgp": "Athletic Raceway|v1.03",
    "Luncheon Tour|v1.16": "Luncheon Tour|v1.1.6",
    "GCN Wario Colosseum|v1.5.ctgp": "GCN Wario Colosseum|v1.5-CTGP",
    "Colour Circuit|v1.2c": "Colour Circuit|v1.2-a",
    "DS DK Pass|v2.2b": "DS DK Pass|v2.2",
    "SNES Choco Island 2|v1.21": "SNES Choco Island 2|v1.2",
    "Alpine Peak|v1.4": "Alpine Peak|v1.3",
    "Luigi's Island|v4.51": "Luigi's Island|v4.5.1",
    "Mario Castle Raceway|v1.01": "Mario Castle Raceway|v1.0",
    "Lunar Spaceway|v1.11": "Lunar Spaceway|v1.2",
    "SNES Mario Circuit 1|v2.51|ZPL|Jasperr": "SNES Mario Circuit 1|v2.51"
}

def calc_removed_tracks_pt2():
    with open("ctgp_changelog_from_1096_inclusive.txt", "r") as f:
        lines = f.readlines()

    new_track_nameversions = []

    for line in lines:
        line = line.strip()
        if line == "" or line[0] == "#":
            continue

        name_author, version = line.split(",", maxsplit=1)
        match_obj = changelog_track_name_regex.match(name_author)
        if match_obj:
            name = match_obj.group(1)
            if name == "SNES Mario Circuit 1":
                author = match_obj.group(2)
                nameversion = f"{name}|{version}|{author}"
            else:
                nameversion = f"{name}|{version}"
        else:
            if name_author == "SNES Mario Circuit 1":
                nameversion = f"{name_author}|{version}|None"
            else:
                nameversion = f"{name_author}|{version}"

        new_track_nameversions.append(nameversion)

    with open("leaderboards_combined_by_track_name_version.json", "r") as f:
        leaderboards_by_track_name_version = json.load(f)

    for i, new_track_nameversion in enumerate(new_track_nameversions):
        if new_track_nameversion not in leaderboards_by_track_name_version:
            new_track_nameversion_2 = new_track_nameversion_to_actual_nameversion.get(new_track_nameversion)
            if new_track_nameversion_2 is None:
                raise RuntimeError(f"{new_track_nameversion} might not be in CTGP. Check manually!")
            new_track_nameversions[i] = new_track_nameversion_2

    with open("ctgp_current_tracks.json", "r") as f:
        current_tracks = json.load(f)

    wbz_converter = wbz.WbzConverter(
        iso_filename="../../RMCE01/RMCE01.iso",
        original_track_files_dirname="storage/original-race-course",
        wit_filename="bin/wiimm/linux/wit",
        wszst_filename="bin/wiimm/linux/wszst",
        auto_add_containing_dirname="storage"
    )

    consumed_track_nameversions = set()
    removed_tracks = {}

    for new_track_nameversion in new_track_nameversions:
        if new_track_nameversion in consumed_track_nameversions:
            raise RuntimeError(f"Ambiguity detected in track nameverison! new_track_nameversion: {new_track_nameversion}")

        consumed_track_nameversions.add(new_track_nameversion)
        all_leaderboards_for_track_id = leaderboards_by_track_name_version[new_track_nameversion]
        #print(all_leaderboards_for_track_id)
        track_id = all_leaderboards_for_track_id[0]["trackId"]
        if track_id not in current_tracks:
            # sky high island v1.03
            # sakura sanctuary v1.01
            if track_id in ("CF5C08E290F267A9019ABBB321E9963F4C90AD72","82E09E8FD5CFB508CB6A32E541482E54EDB7C488"):
                result = None
            else:
                result = wbz_converter.download_wbz_get_filepath(track_id)

            if result is None:
                print(f"Wiimm archive doesn't have track {new_track_nameversion} ({track_id})!")
                track_name_full = new_track_nameversion
                wiimm_version = None
            else:
                full_track_info = download_full_track_info_id_only(track_id)
                track_name_full = full_track_info["track_name_full"]
                wiimm_version = full_track_info["version"]

            all_leaderboards_for_track_id_plus_check_200cc = {
                "leaderboards": all_leaderboards_for_track_id,
                "check_200cc": True,
                "track_name_full": track_name_full,
                "missing_from_archive": result is None,
                "wiimm_version": wiimm_version
            }
            removed_tracks[track_id] = all_leaderboards_for_track_id_plus_check_200cc

    with open("removed_ctgp_tracks_pt2.json", "w+") as f:
        json.dump(removed_tracks, f, indent=2)

def print_removed_tracks_pt2():
    with open("removed_ctgp_tracks_pt2.json", "r") as f:
        removed_tracks_pt1 = json.load(f)

    output = ""
    for track_id, track_lb_info in removed_tracks_pt1.items():
        output += f"{track_lb_info['track_name_full']}\n"

    with open("removed_ctgp_tracks_pt2_out.txt", "w+") as f:
        f.write(output)

def combine_removed_tracks():
    with open("removed_ctgp_tracks_pt1.json", "r") as f:
        removed_tracks_pt1 = json.load(f)

    with open("removed_ctgp_tracks_pt2.json", "r") as f:
        removed_tracks_pt2 = json.load(f)

    removed_tracks_pt1_keys = frozenset(removed_tracks_pt1.keys())
    removed_tracks_pt2_keys = frozenset(removed_tracks_pt2.keys())

    if not removed_tracks_pt1_keys.isdisjoint(removed_tracks_pt2_keys):
        raise RuntimeError(f"This should not happen, removed tracks parts should be mutually exclusive! Keys in both tracks: {removed_tracks_pt1_keys & removed_tracks_pt2_keys}")

    removed_tracks_pt1.update(removed_tracks_pt2)

    with open("removed_ctgp_tracks.json", "w+") as f:
        json.dump(removed_tracks_pt1, f, indent=2)

def main():
    MODE = 9

    if MODE == 0:
        get_all_wiimm_ctgp_track_ids()
    elif MODE == 1:
        test_download_full_track_info()
    elif MODE == 2:
        get_all_wiimm_ctgp_full_track_info()
    elif MODE == 3:
        merge_150cc_200cc_leaderboards()
    elif MODE == 4:
        key_leaderboards_by_track_id_and_track_name_version_separately()
    elif MODE == 5:
        get_tracks_in_current_ctgp()
    elif MODE == 6:
        calc_ctgp_tracks_from_wiimm_data()
    elif MODE == 7:
        print_removed_tracks_pt1()
    elif MODE == 8:
        calc_removed_tracks_pt2()
    elif MODE == 9:
        print_removed_tracks_pt2()
    elif MODE == 10:
        combine_removed_tracks()
    else:
        print("no mode selected!")

if __name__ == "__main__":
    main()
