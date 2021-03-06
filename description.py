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

# -*- coding: utf-8 -*-
import dateutil.parser
import pathlib
import identifiers
from import_ghost_to_save import Rkg
import util
from constants.customtop10 import *
import legacyrecords_staticconfig
import json
import random
import legacyrecords_music
import chadsoft

from constants.slower_glitch import *

TITLE_TEMPLATE = "【CTGP {lb_modifiers}Legacy WR】 {track_version_category} - {time} - {player_name}"
DESCRIPTION_TEMPLATE = """\
Submit music in the CTGP Legacy Records discord server: https://discord.gg/zQebERHCGS 
{fake_glitch_notice}
Date Set: {date_set}
Player: {player_name}
Players page: {player_page_link}
Link to run: {run_link}
Link to leaderboard: {lb_link}
Location: {location}
Controller: {controller}
Vehicle: {vehicle_name}
Drift Type: {drift_type}
Category: {category_name}
{is_fake_glitch}
Total Time - {run_time}
{laps_and_splits}

CTGP Track Name and Version: {track_name_and_version}
Wiimm's CT Archive's Full Track Name: {track_name_full}
Link to track on Wiimm's CT Archive: {wiimms_archive_link}

{run_music_info}

Former World Record: {former_wr}

Ghost being raced: {ghost_being_raced}

Helpful Links
• Support CTGP by donating here: https://streamlabs.com/mrbean35000vr
• CTGP Records discord server: https://discord.com/invite/dPrhVUS
• 200cc CTGP Records discord server: https://discord.gg/rMsJVkj
• CTGP Kart Records discord server: https://discord.gg/zQnvDMjFMh
• Every MKW Top 10 - http://mkleaderboards.com/mkw
• MKW World Record History: https://www.mkwrs.com/mkwii/

This run was automatically recorded by Auto TT Recorder.
"""

MUSIC_TEMPLATE = """\
♪ {music_artist} «» {music_name} ♪
Link: {music_source}
(BGM suggested by {music_suggestor} & Video by Auto TT Recorder)"""

BGM_MUSIC_TEMPLATE = """\
♪ Mario Kart Wii «» {music_name} (Game BGM) ♪
(Video by Auto TT Recorder)"""

FORMER_WR_TEMPLATE = """\
{former_wr_time}
by {former_wr_player} (set on {former_wr_date_set})
Link to run: {former_wr_link}"""

GHOST_BEING_RACED_TEMPLATE = """\
{comparison_ghost_time}
by {comparison_ghost_player} (set on {comparison_ghost_date_set})
Link to run: {comparison_ghost_link}"""

CHADSOFT_TIME_TRIALS = "https://www.chadsoft.co.uk/time-trials"

HEAVY_LEFT_ANGLE_BRACKET = "❮"
HEAVY_RIGHT_ANGLE_BRACKET = "❯"

MAX_TITLE_LEN = 100
MAX_DESCRIPTION_LEN = 5000

def replace_angle_brackets(input_str):
    return input_str.replace("<", HEAVY_LEFT_ANGLE_BRACKET).replace(">", HEAVY_RIGHT_ANGLE_BRACKET)

def get_version_str_from_legacy_wr_entry(legacy_wr_entry):
    version = legacy_wr_entry["version"]
    if version is not None:
        version_str = f"({version})"
    else:
        version_str = None

    return version_str

def gen_title(legacy_wr_entry, slower_glitch_type):
    title, truncated = gen_title_loopcode(legacy_wr_entry, slower_glitch_type)
    if not truncated:
        return title

    title, truncated = gen_title_loopcode(legacy_wr_entry, slower_glitch_type, skip_version_str=True)
    if not truncated:
        return title

    title, truncated = gen_title_loopcode(legacy_wr_entry, slower_glitch_type, skip_version_str=True)
    return title

def create_lb_modifiers_str(legacy_wr_entry):
    str_200cc = "200cc" if legacy_wr_entry["200cc"] else None
    vehicle_modifier_str = identifiers.vehicle_modifier_to_str.get(legacy_wr_entry["vehicleModifier"])

    lb_modifiers = util.join_conditional_modifier(str_200cc, vehicle_modifier_str)
    if lb_modifiers != "":
        lb_modifiers += " "

    return lb_modifiers

def gen_title_loopcode(legacy_wr_entry, slower_glitch_type, skip_version_str=False, skip_category_name=False):
    track_name = legacy_wr_entry["trackName"]

    if skip_category_name:
        category_name = None
    else:
        if slower_glitch_type in (SLOWER_GLITCH_95_RULE, SLOWER_GLITCH_REVERSE_95_RULE, SLOWER_GLITCH_FAKE_GLITCH):
            category_name = "(Fake Glitch)"
        elif slower_glitch_type == SLOWER_GLITCH_REAL_SLOWER_GLITCH:
            category_name = "(Slower Glitch)"
        else:
            category_name = None if legacy_wr_entry["categoryId"] == -1 else f"({legacy_wr_entry['categoryName']})"

    if skip_version_str:
        version_str = None
    else:
        version_str = get_version_str_from_legacy_wr_entry(legacy_wr_entry)

    lb_modifiers = create_lb_modifiers_str(legacy_wr_entry)

    title_intermediate = TITLE_TEMPLATE.format(
        lb_modifiers=lb_modifiers,
        track_version_category=util.join_conditional_modifier(track_name, version_str, category_name),
        time=legacy_wr_entry["finishTimeSimple"],
        player_name=identifiers.replace_extended_symbols(legacy_wr_entry["player"])
    )
    title_intermediate = replace_angle_brackets(title_intermediate)
    if len(title_intermediate) > MAX_TITLE_LEN:
        print(f"Warning: title {title_intermediate} longer than {MAX_TITLE_LEN} characters!")
        truncated = True
    else:
        truncated = False

    return title_intermediate[:MAX_TITLE_LEN], truncated

def create_chadsoft_link(endpoint_link):
    return f"{CHADSOFT_TIME_TRIALS}{pathlib.PurePosixPath(endpoint_link).with_suffix('.html')}"

def create_chadsoft_link_with_vehicle_modifier(legacy_wr_entry):
    lb_link = create_chadsoft_link(legacy_wr_entry["lbHref"])
    if legacy_wr_entry["vehicleModifier"] is not None:
        lb_link += f"#filter-vehicle-{legacy_wr_entry['vehicleModifier']}"

    return lb_link

def create_track_name_and_version_from_wr_entry(legacy_wr_entry):
    version_str = get_version_str_from_legacy_wr_entry(legacy_wr_entry)

    track_name_and_version = util.join_conditional_modifier(legacy_wr_entry["trackName"], version_str)

    return track_name_and_version

def create_track_name_and_version(track_name, version):
    if version is not None:
        version = f"({version})"

    return util.join_conditional_modifier(track_name, version)

def format_date_utc(date_obj):
    return date_obj.strftime("%Y-%m-%d (UTC)")

def gen_description(legacy_wr_entry, legacy_wr_lb, rkg_filename, music_info, slower_glitch_type, comparison_ghost_entry):
    if slower_glitch_type == SLOWER_GLITCH_95_RULE:
        fake_glitch_notice = "Note: This run does not actually perform an Ultra Shortcut. It has been miscategorized as Glitch due to CTGP's faulty Glitch detection. However, it comes close but gets a no-lap count due to the 95% Rule.\n"
    elif slower_glitch_type == SLOWER_GLITCH_REVERSE_95_RULE:
        fake_glitch_notice = "Note: This run does not actually perform an Ultra Shortcut. It has been miscategorized as Glitch due to CTGP's faulty Glitch detection. However, it comes close but gets a no-lap count due to the Reverse 95% Rule/4.9% Rule.\n"
    elif slower_glitch_type == SLOWER_GLITCH_FAKE_GLITCH:
        fake_glitch_notice = "Note: This run does not actually perform an Ultra Shortcut. It has been miscategorized as Glitch due to CTGP's faulty Glitch detection. For this specific run, it may be misclassified due to crossing the finish line backwards via a respawn.\n"
    else:
        fake_glitch_notice = ""

    date_set_obj = dateutil.parser.isoparse(legacy_wr_entry["dateSet"])
    date_set = format_date_utc(date_set_obj)

    player_name = identifiers.replace_extended_symbols(legacy_wr_entry["player"])

    player_page_endpoint_link = legacy_wr_entry["_links"]["player"]["href"]
    player_page_link = create_chadsoft_link(player_page_endpoint_link)

    run_link = create_chadsoft_link(legacy_wr_entry["ghostHref"])
    lb_link = create_chadsoft_link_with_vehicle_modifier(legacy_wr_entry)
    #if legacy_wr_entry["vehicleModifier"] is not None:
    #    lb_link += f"#filter-vehicle-{legacy_wr_entry['vehicleModifier']}"
    country_id = legacy_wr_entry.get("country")
    if country_id is None:
        location = "Unknown"
    else:
        location = countries_by_code.get(country_id, "Unknown").name
    controller = identifiers.get_controller_name(legacy_wr_entry["controller"], legacy_wr_entry["usbGcnAdapterAttached"])

    rkg = Rkg(rkg_filename)
    vehicle_id = legacy_wr_entry["vehicleId"]

    vehicle_name = identifiers.vehicle_names[vehicle_id]
    vehicle_name_eu = identifiers.vehicle_names_eu.get(vehicle_id)
    if vehicle_name_eu is not None:
        vehicle_name += f" ({vehicle_name_eu})"

    drift_type = "Automatic" if rkg.drift_type else "Manual"
    category_name = legacy_wr_entry["categoryName"]

    if slower_glitch_type == SLOWER_GLITCH_95_RULE:
        is_fake_glitch = "Is Fake Glitch: Yes (95% Rule)\n"
    elif slower_glitch_type == SLOWER_GLITCH_REVERSE_95_RULE:
        is_fake_glitch = "Is Fake Glitch: Yes (Reverse 95% Rule)\n"
    elif slower_glitch_type == SLOWER_GLITCH_FAKE_GLITCH:
        is_fake_glitch = "Is Fake Glitch: Yes (Other)\n"
    elif slower_glitch_type == SLOWER_GLITCH_REAL_SLOWER_GLITCH:
        is_fake_glitch = "Is Fake Glitch: No (Slower)\n"
    elif slower_glitch_type == SLOWER_GLITCH_FASTER_GLITCH:
        is_fake_glitch = "Is Fake Glitch: No (Faster)\n"
    else:
        is_fake_glitch = ""

    run_time = legacy_wr_entry["finishTimeSimple"]
    laps_and_splits = "\n".join(f"Lap {lap_num} | {split.pretty()}" for lap_num, split in enumerate(rkg.splits, 1))

    track_name_and_version = create_track_name_and_version_from_wr_entry(legacy_wr_entry)
    if legacy_wr_entry["missingFromArchive"]:
        track_name_full = "N/A"
        wiimms_archive_link = "N/A"
    else:
        track_name_full = legacy_wr_entry["trackNameFull"]
        wiimms_archive_link = f"https://ct.wiimm.de/i/{legacy_wr_entry['trackId']}"

    if music_info is not None:
        music_artist = music_info.artist
        music_name = music_info.name
        music_source = music_info.source
        music_suggestor = music_info.suggestor

        run_music_info = MUSIC_TEMPLATE.format(
            music_artist=music_artist,
            music_name=music_name,
            music_source=music_source,
            music_suggestor=music_suggestor
        )
    else:
        music_name = identifiers.track_names[rkg.track_by_human_id]
        run_music_info = BGM_MUSIC_TEMPLATE.format(
            music_name=music_name
        )

    if len(legacy_wr_lb["ghosts"]) <= 1:
        former_wr = "N/A"
    else:
        former_wr_entry = legacy_wr_lb["ghosts"][1]
        former_wr_time = former_wr_entry["finishTimeSimple"]
        former_wr_player_id = former_wr_entry["playerId"]
        if former_wr_player_id in legacyrecords_staticconfig.censored_players:
            former_wr_player = "Player"
        else:
            former_wr_player = identifiers.replace_extended_symbols(former_wr_entry["player"])

        former_wr_date_set_obj = dateutil.parser.isoparse(former_wr_entry["dateSet"])
        former_wr_date_set = format_date_utc(former_wr_date_set_obj)

        if former_wr_player_id not in legacyrecords_staticconfig.censored_players:
            former_wr_link = create_chadsoft_link(former_wr_entry["_links"]["item"]["href"])
        else:
            former_wr_link = "N/A"

        former_wr = FORMER_WR_TEMPLATE.format(
            former_wr_time=former_wr_time,
            former_wr_player=former_wr_player,
            former_wr_date_set=former_wr_date_set,
            former_wr_link=former_wr_link
        )
 
    if comparison_ghost_entry is not None and comparison_ghost_entry["playerId"] not in legacyrecords_staticconfig.censored_players:
        comparison_ghost_time = comparison_ghost_entry["finishTimeSimple"]
        comparison_ghost_player = identifiers.replace_extended_symbols(comparison_ghost_entry["player"])

        comparison_ghost_date_set_obj = dateutil.parser.isoparse(comparison_ghost_entry["dateSet"])
        comparison_ghost_date_set = format_date_utc(comparison_ghost_date_set_obj)

        comparison_ghost_link = create_chadsoft_link(comparison_ghost_entry["_links"]["item"]["href"])

        ghost_being_raced = GHOST_BEING_RACED_TEMPLATE.format(
            comparison_ghost_time=comparison_ghost_time,
            comparison_ghost_player=comparison_ghost_player,
            comparison_ghost_date_set=comparison_ghost_date_set,
            comparison_ghost_link=comparison_ghost_link
        )
    else:
        ghost_being_raced = "N/A"

    description_intermediate = DESCRIPTION_TEMPLATE.format(
        fake_glitch_notice=fake_glitch_notice,
        date_set=date_set,
        player_name=player_name,
        player_page_link=player_page_link,
        run_link=run_link,
        lb_link=lb_link,
        location=location,
        controller=controller,
        vehicle_name=vehicle_name,
        drift_type=drift_type,
        category_name=category_name,
        is_fake_glitch=is_fake_glitch,
        run_time=run_time,
        laps_and_splits=laps_and_splits,
        track_name_and_version=track_name_and_version,
        track_name_full=track_name_full,
        wiimms_archive_link=wiimms_archive_link,
        run_music_info=run_music_info,
        former_wr=former_wr,
        ghost_being_raced=ghost_being_raced
    )

    description_intermediate = replace_angle_brackets(description_intermediate)
    if len(description_intermediate) > MAX_DESCRIPTION_LEN:
        print(f"Warning: description {description_intermediate} is longer than {MAX_DESCRIPTION_LEN} characters!")

    return description_intermediate[:MAX_DESCRIPTION_LEN]

def test_gen_title():
    with open("sorted_legacy_wrs.json", "r") as f:
        sorted_legacy_wrs = json.load(f)

    while True:
        random_legacy_wr_entry = random.choice(sorted_legacy_wrs)
        if not random_legacy_wr_entry["isRedundant"] and random_legacy_wr_entry["ghostHref"] is not None:
            break

    print(f"Creating title for legacy wr {random_legacy_wr_entry['hash']}!")
    title = gen_title(random_legacy_wr_entry, SLOWER_GLITCH_NO_GLITCH)
    print(f"title: {title}, len(title): {len(title)}")

def test_gen_title_and_description():
    random.seed(1150)
    output = ""

    with open("sorted_legacy_wrs.json", "r") as f:
        sorted_legacy_wrs = json.load(f)

    while True:
        random_legacy_wr_entry = random.choice(sorted_legacy_wrs)
        if not random_legacy_wr_entry["isRedundant"] and random_legacy_wr_entry["ghostHref"] is not None:
            break

    slower_glitch_type = random.choice((SLOWER_GLITCH_NO_GLITCH, SLOWER_GLITCH_REAL_SLOWER_GLITCH, SLOWER_GLITCH_95_RULE, SLOWER_GLITCH_REVERSE_95_RULE, SLOWER_GLITCH_FAKE_GLITCH, SLOWER_GLITCH_FASTER_GLITCH))

    print(f"Random slower_glitch_type: {slower_glitch_type}")
    print(f"Creating title for legacy wr {random_legacy_wr_entry['hash']}!")
    
    output += gen_title(random_legacy_wr_entry, slower_glitch_type) + "\n\n"

    legacy_wr_lb = chadsoft.get_lb_from_href(random_legacy_wr_entry["lbHref"], start=0, limit=2, vehicle=random_legacy_wr_entry["vehicleModifier"], times="wr", read_cache=True, write_cache=True)

    legacy_ghost_data, status_code = chadsoft.get(random_legacy_wr_entry["href"], is_binary=True, read_cache=True, write_cache=True)
    downloaded_ghost_pathname = f"legacy_ghosts/{pathlib.Path(random_legacy_wr_entry['href']).name}"
    downloaded_ghost_path = pathlib.Path(downloaded_ghost_pathname)
    downloaded_ghost_path.parent.mkdir(parents=True, exist_ok=True)
    with open(downloaded_ghost_pathname, "wb+") as f:
        f.write(legacy_ghost_data)

    mock_music_list_text ="""\
https://cdn.discordapp.com/attachments/528745839708078093/932354387983097927/undertale_last_breath_phase_3.opus,luckytyphlosion,https://www.youtube.com/watch?v=dIWNltBsq10,Benlab,Undertale Last Breath: An Enigmatic Encounter (Phase 3)
https://cdn.discordapp.com/attachments/528745839708078093/932356305929240706/-_Dark_Sheep-bYCbm469Zq0.webm,luckytyphlosion,https://youtu.be/bYCbm469Zq0,Chroma,Dark Sheep
"""

    music_info = None#legacyrecords_music.get_music({"music_index": random.randint(0, 2)}, mock_music_list_text)

    if random_legacy_wr_entry["vehicleModifier"] is not None:
        legacy_wr_lb_excluding_vehicle_modifier = chadsoft.get_lb_from_href(random_legacy_wr_entry["lbHref"], start=0, limit=1, times="wr", read_cache=True, write_cache=True)
        random_legacy_wr_entry_excluding_vehicle_modifier = legacy_wr_lb_excluding_vehicle_modifier["ghosts"][0]
    else:
        random_legacy_wr_entry_excluding_vehicle_modifier = None

    output += gen_description(random_legacy_wr_entry, legacy_wr_lb, downloaded_ghost_pathname, music_info, slower_glitch_type, random_legacy_wr_entry_excluding_vehicle_modifier)
    with open("test_gen_description_out.dump", "w+") as f:
        f.write(output)

def main():
    MODE = 1
    if MODE == 0:
        test_gen_title()
    elif MODE == 1:
        test_gen_title_and_description()
    else:
        print("no mode selected")

if __name__ == "__main__":
    main()

