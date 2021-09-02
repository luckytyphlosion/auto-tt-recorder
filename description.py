# -*- coding: utf-8 -*-
import dateutil.parser
import pathlib
import identifiers
from import_ghost_to_save import Rkg

TITLE_TEMPLATE = "【CTGP {vehicle} WR】 {track}{category}- {time} - {player_name}"
DESCRIPTION_TEMPLATE = """\
Date Set: {date_set}
Player: {player_name}
Players page: {player_page_link}
Link to run: {run_link}
Link to leaderboard: {lb_link}
Location: {location}
Controller: {controller}
Drift Type: {drift_type}
Category: {category_name}

Total Time - {run_time}
Lap 1 | {lap_1_split}
Lap 2 | {lap_2_split}
Lap 3 | {lap_3_split}

Former World Record: {former_wr}"""

FORMER_WR_TEMPLATE = """\
{former_wr_time}
by {former_wr_player} (set on {former_wr_date_set})
Link to run: {former_wr_link}"""

CHADSOFT_TIME_TRIALS = "https://www.chadsoft.co.uk/time-trials"

HEAVY_LEFT_ANGLE_BRACKET = "❮"
HEAVY_RIGHT_ANGLE_BRACKET = "❯"

MAX_TITLE_LEN = 100
MAX_DESCRIPTION_LEN = 1000

def replace_angle_brackets(input_str):
    return input_str.replace("<", HEAVY_LEFT_ANGLE_BRACKET).replace(">", HEAVY_RIGHT_ANGLE_BRACKET)

def gen_title(vehicle_wr_entry):
    title_intermediate = TITLE_TEMPLATE.format(
        vehicle=vehicle_wr_entry["vehicleName"],
        track=vehicle_wr_entry["trackName"],
        category=" " if vehicle_wr_entry["categoryId"] == -1 else f" ({vehicle_wr_entry['categoryName']}) ",
        time=vehicle_wr_entry["finishTimeSimple"],
        player_name=identifiers.replace_extended_symbols(vehicle_wr_entry["player"])
    )
    title_intermediate = replace_angle_brackets(title_intermediate)
    if len(title_intermediate) > MAX_TITLE_LEN:
        print(f"Warning: title {title_intermediate} longer than {MAX_TITLE_LEN} characters!")

    return title_intermediate[:MAX_TITLE_LEN]

def create_chadsoft_link(endpoint_link):
    return f"{CHADSOFT_TIME_TRIALS}{pathlib.PurePosixPath(endpoint_link).with_suffix('.html')}"

def format_date_utc(date_obj):
    return date_obj.strftime("%Y-%m-%d (UTC)")

def gen_description(vehicle_wr_entry, vehicle_wr_lb, rkg_filename):
    date_set_obj = dateutil.parser.isoparse(vehicle_wr_entry["dateSet"])
    date_set = format_date_utc(date_set_obj)

    player_name = identifiers.replace_extended_symbols(vehicle_wr_entry["player"])

    player_page_endpoint_link = vehicle_wr_entry["_links"]["player"]["href"]
    player_page_link = create_chadsoft_link(player_page_endpoint_link)

    run_link = create_chadsoft_link(vehicle_wr_entry["ghostHref"])
    lb_link = create_chadsoft_link(vehicle_wr_entry["lbHref"])
    
    location = identifiers.location_names.get(vehicle_wr_entry.get("country", -1), "Unknown")
    controller = identifiers.get_controller_name(vehicle_wr_entry["controller"], vehicle_wr_entry["usbGcnAdapterAttached"])

    rkg = Rkg(rkg_filename)

    drift_type = "Automatic" if rkg.drift_type else "Manual"
    category_name = vehicle_wr_entry["categoryName"]

    run_time = vehicle_wr_entry["finishTimeSimple"]

    lap_1_split = rkg.splits[0].pretty()
    lap_2_split = rkg.splits[1].pretty()
    lap_3_split = rkg.splits[2].pretty()

    if len(vehicle_wr_lb["ghosts"]) <= 1:
        former_wr = "N/A"
    else:
        former_wr_entry = vehicle_wr_lb["ghosts"][1]
        former_wr_time = former_wr_entry["finishTimeSimple"]
        former_wr_player = identifiers.replace_extended_symbols(former_wr_entry["player"])
        former_wr_date_set_obj = dateutil.parser.isoparse(former_wr_entry["dateSet"])
        former_wr_date_set = format_date_utc(former_wr_date_set_obj)
        former_wr_link = create_chadsoft_link(former_wr_entry["_links"]["item"]["href"])

        former_wr = FORMER_WR_TEMPLATE.format(
            former_wr_time=former_wr_time,
            former_wr_player=former_wr_player,
            former_wr_date_set=former_wr_date_set,
            former_wr_link=former_wr_link
        )

    description_intermediate = DESCRIPTION_TEMPLATE.format(
        date_set=date_set,
        player_name=player_name,
        player_page_link=player_page_link,
        run_link=run_link,
        lb_link=lb_link,
        location=location,
        controller=controller,
        drift_type=drift_type,
        category_name=category_name,
        run_time=run_time,
        lap_1_split=lap_1_split,
        lap_2_split=lap_2_split,
        lap_3_split=lap_3_split,
        former_wr=former_wr
    )

    description_intermediate = replace_angle_brackets(description_intermediate)
    if len(description_intermediate) > MAX_DESCRIPTION_LEN:
        print(f"Warning: description {description_intermediate} is longer than {MAX_DESCRIPTION_LEN} characters!")

    return description_intermediate[:MAX_DESCRIPTION_LEN]
