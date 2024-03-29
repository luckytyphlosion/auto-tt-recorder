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

from stateclasses.input_display import *
from constants.categories import *

vehicle_names = {
    0x00: "Standard Kart S",
    0x01: "Standard Kart M",
    0x02: "Standard Kart L",
    0x03: "Booster Seat",
    0x04: "Classic Dragster",
    0x05: "Offroader",
    0x06: "Mini Beast",
    0x07: "Wild Wing",
    0x08: "Flame Flyer",
    0x09: "Cheep Charger",
    0x0A: "Super Blooper",
    0x0B: "Piranha Prowler",
    0x0C: "Tiny Titan",
    0x0D: "Daytripper",
    0x0E: "Jetsetter",
    0x0F: "Blue Falcon",
    0x10: "Sprinter",
    0x11: "Honeycoupe",
    0x12: "Standard Bike S",
    0x13: "Standard Bike M",
    0x14: "Standard Bike L",
    0x15: "Bullet Bike",
    0x16: "Mach Bike",
    0x17: "Flame Runner",
    0x18: "Bit Bike",
    0x19: "Sugarscoot",
    0x1A: "Wario Bike",
    0x1B: "Quacker",
    0x1C: "Zip Zip",
    0x1D: "Shooting Star",
    0x1E: "Magikruiser",
    0x1F: "Sneakster",
    0x20: "Spear",
    0x21: "Jet Bubble",
    0x22: "Dolphin Dasher",
    0x23: "Phantom"
}

vehicle_id_to_is_kart = {
    0x00: True, # "Standard Kart S",
    0x01: True, # "Standard Kart M",
    0x02: True, # "Standard Kart L",
    0x03: True, # "Booster Seat",
    0x04: True, # "Classic Dragster",
    0x05: True, # "Offroader",
    0x06: True, # "Mini Beast",
    0x07: True, # "Wild Wing",
    0x08: True, # "Flame Flyer",
    0x09: True, # "Cheep Charger",
    0x0A: True, # "Super Blooper",
    0x0B: True, # "Piranha Prowler",
    0x0C: True, # "Tiny Titan",
    0x0D: True, # "Daytripper",
    0x0E: True, # "Jetsetter",
    0x0F: True, # "Blue Falcon",
    0x10: True, # "Sprinter",
    0x11: True, # "Honeycoupe",
    0x12: False, # "Standard Bike S",
    0x13: False, # "Standard Bike M",
    0x14: False, # "Standard Bike L",
    0x15: False, # "Bullet Bike",
    0x16: False, # "Mach Bike",
    0x17: False, # "Flame Runner",
    0x18: False, # "Bit Bike",
    0x19: False, # "Sugarscoot",
    0x1A: False, # "Wario Bike",
    0x1B: False, # "Quacker",
    0x1C: False, # "Zip Zip",
    0x1D: False, # "Shooting Star",
    0x1E: False, # "Magikruiser",
    0x1F: False, # "Sneakster",
    0x20: False, # "Spear",
    0x21: False, # "Jet Bubble",
    0x22: False, # "Dolphin Dasher",
    0x23: False # "Phantom"
}

vehicle_ids_by_filter_name = {vehicle_name.lower().replace(" ", "-"): vehicle_id for vehicle_id, vehicle_name in vehicle_names.items()}

vehicle_names_eu = {
    0x03: "Baby Booster",
    0x04: "Nostalgia 1",
    0x06: "Concerto",
    0x0A: "Turbo Blooper",
    0x0C: "Rally Romper",
    0x0D: "Royal Racer",
    0x0E: "Aero Glider",
    0x10: "B Dasher Mk 2",
    0x11: "Dragonetti",
    0x17: "Bowser Bike",
    0x18: "Nanobike",
    0x19: "Bon Bon",
    0x1C: "Rapide",
    0x1D: "Twinkle Star",
    0x1F: "Nitrocycle",
    0x20: "Torpedo",
    0x21: "Bubble Bike",
}

def get_vehicle_name_region_dependent(vehicle, iso_region_name):
    if iso_region_name == "PAL":
        return vehicle_names_eu.get(vehicle, vehicle_names.get(vehicle))
    else:
        return vehicle_names.get(vehicle)

track_names_eu = {
    6: "DK's Snowboard Cross"
}

NUM_VEHICLES = len(vehicle_names)

track_id_to_ghost_slot = {
    0x00: 4, 0x01: 1, 0x02: 2, 0x03: 10, 0x04: 3, 0x05: 5, 0x06: 6, 0x07: 7,
    0x08: 0, 0x09: 8, 0x0a: 12, 0x0b: 11, 0x0c: 14, 0x0d: 15, 0x0e: 13, 0x0f: 9,
    0x10: 24, 0x11: 25, 0x12: 26, 0x13: 27, 0x14: 28, 0x15: 29, 0x16: 30, 0x17: 31,
    0x18: 18, 0x19: 17, 0x1a: 21, 0x1b: 20, 0x1c: 23, 0x1d: 22, 0x1e: 19, 0x1f: 16
}

track_id_to_human_track_id = {
    0x00: 4, 0x01: 1, 0x02: 2, 0x03: 11,
    0x04: 3, 0x05: 5, 0x06: 6, 0x07: 7,
    0x08: 0, 0x09: 8, 0x0a: 13, 0x0b: 10,
    0x0c: 14, 0x0d: 15, 0x0e: 12, 0x0f: 9,
    0x10: 16, 0x11: 27, 0x12: 23, 0x13: 30,
    0x14: 17, 0x15: 24, 0x16: 29, 0x17: 22,
    0x18: 28, 0x19: 18, 0x1a: 19, 0x1b: 20,
    0x1c: 31, 0x1d: 26, 0x1e: 25, 0x1f: 21,
}

track_names = [
    "Luigi Circuit",
    "Moo Moo Meadows",
    "Mushroom Gorge",
    "Toad's Factory",
    "Mario Circuit",
    "Coconut Mall",
    "DK Summit",
    "Wario's Gold Mine",
    "Daisy Circuit",
    "Koopa Cape",
    "Maple Treeway",
    "Grumble Volcano",
    "Dry Dry Ruins",
    "Moonview Highway",
    "Bowser's Castle",
    "Rainbow Road",
    "GCN Peach Beach",
    "DS Yoshi Falls",
    "SNES Ghost Valley 2",
    "N64 Mario Raceway",
    "N64 Sherbet Land",
    "GBA Shy Guy Beach",
    "DS Delfino Square",
    "GCN Waluigi Stadium",
    "DS Desert Hills",
    "GBA Bowser Castle 3",
    "N64 DK's Jungle Parkway",
    "GCN Mario Circuit",
    "SNES Mario Circuit 3",
    "DS Peach Gardens",
    "GCN DK Mountain",
    "N64 Bowser's Castle"
]

MARIO_CIRCUIT_MSG_ID = 0x2454
MY_GHOST_MSG_ID = 0x1398
GHOST_CREATED_FOR_PLAYER_MSG_ID = 0x045B
MKCHANNEL_GHOST_SCREEN_RACE_THIS_GHOST_MSG_ID = 0x177B
MKCHANNEL_GHOST_SCREEN_WATCH_REPLAY_MSG_ID = 0x177C

track_filenames = [
    "beginner_course.szs",
    "farm_course.szs",
    "kinoko_course.szs",
    "factory_course.szs",
    "castle_course.szs",
    "shopping_course.szs",
    "boardcross_course.szs",
    "truck_course.szs",
    "senior_course.szs",
    "water_course.szs",
    "treehouse_course.szs",
    "volcano_course.szs",
    "desert_course.szs",
    "ridgehighway_course.szs",
    "koopa_course.szs",
    "rainbow_course.szs",
    "old_peach_gc.szs",
    "old_falls_ds.szs",
    "old_obake_sfc.szs",
    "old_mario_64.szs",
    "old_sherbet_64.szs",
    "old_heyho_gba.szs",
    "old_town_ds.szs",
    "old_waluigi_gc.szs",
    "old_desert_ds.szs",
    "old_koopa_gba.szs",
    "old_donkey_64.szs",
    "old_mario_gc.szs",
    "old_mario_sfc.szs",
    "old_garden_ds.szs",
    "old_donkey_gc.szs",
    "old_koopa_64.szs"
]

category_names = {
    CATEGORY_DEFAULT: "(Default)",
    CATEGORY_NORMAL: "Normal",
    CATEGORY_GLITCH: "Glitch",
    CATEGORY_NO_SHORTCUT: "No-shortcut",
    CATEGORY_NORMAL_200CC: "Normal (200cc)",
    CATEGORY_GLITCH_200CC: "Glitch (200cc)",
    CATEGORY_NO_SHORTCUT_200CC: "No-shortcut (200cc)",
    CATEGORY_SHORTCUT: "Shortcut"
}

category_names_no_200cc = {
    CATEGORY_DEFAULT: "(Default)",
    CATEGORY_NORMAL: "Normal",
    CATEGORY_GLITCH: "Glitch",
    CATEGORY_NO_SHORTCUT: "No-shortcut",
    CATEGORY_NORMAL_200CC: "Normal",
    CATEGORY_GLITCH_200CC: "Glitch",
    CATEGORY_NO_SHORTCUT_200CC: "No-shortcut",
    CATEGORY_SHORTCUT: "Shortcut"
}

vehicle_modifier_to_str = {
    "karts": "Kart",
    "bikes": "Bike"
}

location_names = {
    1: "Japan",
    8: "Anguilla",
    9: "Antigua and Barbuda",
    10: "Argentina",
    11: "Aruba",
    12: "Bahamas",
    13: "Barbados",
    14: "Belize",
    15: "Bolivia",
    16: "Brazil",
    17: "British Virgin Islands",
    18: "Canada",
    19: "Cayman Islands",
    20: "Chile",
    21: "Colombia",
    22: "Costa Rica",
    23: "Dominica",
    24: "Dominican Republic",
    25: "Ecuador",
    26: "El Salvador",
    27: "French Guiana",
    28: "Grenada",
    29: "Guadeloupe",
    30: "Guatemala",
    31: "Guyana",
    32: "Haiti",
    33: "Honduras",
    34: "Jamaica",
    35: "Martinique",
    36: "Mexico",
    37: "Monsterrat",
    38: "Netherlands Antilles",
    39: "Nicaragua",
    40: "Panama",
    41: "Paraguay",
    42: "Peru",
    43: "St. Kitts and Nevis",
    44: "St. Lucia",
    45: "St. Vincent and the Grenadines",
    46: "Suriname",
    47: "Trinidad and Tobago",
    48: "Turks and Caicos Islands",
    49: "United States",
    50: "Uruguay",
    51: "US Virgin Islands",
    52: "Venezuela",
    64: "Albania",
    65: "Australia",
    66: "Austria",
    67: "Belgium",
    68: "Bosnia and Herzegovina",
    69: "Botswana",
    70: "Bulgaria",
    71: "Croatia",
    72: "Cyprus",
    73: "Czech Republic",
    74: "Denmark",
    75: "Estonia",
    76: "Finland",
    77: "France",
    78: "Germany",
    79: "Greece",
    80: "Hungary",
    81: "Iceland",
    82: "Ireland",
    83: "Italy",
    84: "Latvia",
    85: "Lesotho",
    86: "Lichtenstein",
    87: "Lithuania",
    88: "Luxembourg",
    89: "F.Y.R of Macedonia",
    90: "Malta",
    91: "Montenegro",
    92: "Mozambique",
    93: "Namibia",
    94: "Netherlands",
    95: "New Zealand",
    96: "Norway",
    97: "Poland",
    98: "Portugal",
    99: "Romania",
    100: "Russia",
    101: "Serbia",
    102: "Slovakia",
    103: "Slovenia",
    104: "South Africa",
    105: "Spain",
    106: "Swaziland",
    107: "Sweden",
    108: "Switzerland",
    109: "Turkey",
    110: "United Kingdom",
    111: "Zambia",
    112: "Zimbabwe",
    113: "Azerbaijan",
    114: "Mauritania (Islamic Republic of Mauritania)",
    115: "Mali (Republic of Mali)",
    116: "Niger (Republic of Niger)",
    117: "Chad (Republic of Chad)",
    118: "Sudan (Republic of the Sudan)",
    119: "Eritrea (State of Eritrea)",
    120: "Djibouti (Republic of Djibouti)",
    121: "Somalia (Somali Republic)",
    128: "Taiwan",
    136: "South Korea",
    144: "Hong Kong",
    145: "Macao",
    152: "Indonesia",
    153: "Singapore",
    154: "Thailand",
    155: "Philippines",
    156: "Malaysia",
    160: "China",
    168: "U.A.E.",
    169: "India",
    170: "Egypt",
    171: "Oman",
    172: "Qatar",
    173: "Kuwait",
    174: "Saudi Arabia",
    175: "Syria",
    176: "Bahrain",
    177: "Jordan",
}

extended_symbols_to_utf8 = {
    0xE000: "Ⓐ",
    0xE001: "Ⓑ",
    0xE002: "Ⓧ",
    0xE003: "Ⓨ",
    0xE004: "Ⓛ",
    0xE005: "Ⓡ",
    0xE006: "✜",
    0xE007: "⏰",
    0xE008: "☺",
    0xE009: "😣",
    0xE00A: "☹",
    0xE00B: "😐",
    0xE00C: "☀",
    0xE00D: "☁",
    0xE00E: "☂",
    0xE00F: "☃",
    0xE010: "⚠",
    0xE011: "?",
    0xE012: "✉",
    0xE013: "📱",
    0xE014: "▣",
    0xE015: "♠",
    0xE016: "♦",
    0xE017: "♥",
    0xE018: "♣",
    0xE019: "→",
    0xE01A: "←",
    0xE01B: "↑",
    0xE01C: "↓",
    0xE028: "╳",
    0xE068: "ᵉ",
    0xE069: "ᵉ",
    0xE06A: "ᵉ",
    0xE06B: "�",
    0xF000: "�",
    0xF030: "②",
    0xF031: "②",
    0xF034: "Ⓐ",
    0xF035: "Ⓐ",
    0xF038: "ⓐ",
    0xF039: "ⓐ",
    0xF03C: "Ⓐ",
    0xF03D: "Ⓐ",
    0xF041: "Ⓑ",
    0xF043: "①",
    0xF044: "⊕",
    0xF047: "⊕",
    0xF050: "ⓑ",
    0xF058: "Ⓑ",
    0xF05E: "ⓢ",
    0xF05F: "ⓢ",
    0xF060: " ",
    0xF061: "★",
    0xF062: "⍣",
    0xF063: "⁂",
    0xF064: "☸",
    0xF065: "⍟",
    0xF066: "⍣",
    0xF067: "⁂",
    0xF068: "$",
    0xF069: "🎈",
    0xF06A: "🏆",
    0xF06B: "🏆",
    0xF06C: "🏆",
    0xF06D: "👑",
    0xF074: "☸",
    0xF075: "⍟",
    0xF076: "⍣",
    0xF077: "⁂",
    0xF078: "𝔸",
    0xF079: "𝔹",
    0xF07A: "ℂ",
    0xF07B: "𝔻",
    0xF07C: "𝔼",
    0xF102: " ",
    0xF103: "⓪",
    0xF107: "?",
    0xF108: "①",
    0xF109: "②",
    0xF10A: "③",
    0xF10B: "④",
    0xF10C: "①",
    0xF10D: "②",
    0xF10E: "③",
    0xF10F: "④",
    0xF110: "①",
    0xF111: "②",
    0xF112: "③",
    0xF113: "④",
    0xF114: "①",
    0xF115: "②",
    0xF116: "③",
    0xF117: "④",
    0xF118: "①",
    0xF119: "②",
    0xF11A: "③",
    0xF11B: "④",
    0xF11C: "①",
    0xF11D: "②",
    0xF11E: "③",
    0xF11F: "④",
    0xF120: "①",
    0xF121: "②",
    0xF122: "③",
    0xF123: "④",
    0xF124: "①",
    0xF125: "②",
    0xF126: "③",
    0xF127: "④",
    0xF128: "①",
    0xF129: "②",
    0xF12A: "③",
    0xF12B: "④",
    0xF12C: "①",
    0xF12D: "②",
    0xF12E: "③",
    0xF12F: "④",
    0x2460: "０",
    0x2461: "１",
    0x2462: "２",
    0x2463: "３",
    0x2464: "４",
    0x2465: "５",
    0x2466: "６",
    0x2467: "７",
    0x2468: "８",
    0x2469: "９",
    0x246A: "：",
    0x246B: "．",
    0x246C: "／",
    0x246D: "－",
    0x246E: "＋"
}

def replace_extended_symbols(input_str):
    output = []

    for c in input_str:
        replacement = extended_symbols_to_utf8.get(ord(c))
        if replacement is None:
            output.append(c)
        else:
            output.append(replacement)

    return "".join(output)

controller_names = {
    CONTROLLER_WII_WHEEL: "Wii Wheel",
    CONTROLLER_NUNCHUCK: "Nunchuk",
    CONTROLLER_CLASSIC: "Classic",
    CONTROLLER_GAMECUBE: "GameCube",
    CONTROLLER_UNKNOWN: "???"
}

def get_controller_name(controller_id, is_usb_gcn):
    if is_usb_gcn and controller_id == CONTROLLER_GAMECUBE:
        return "USB GameCube"
    else:
        return controller_names[controller_id]

def get_track_name_from_track_id(track_id):
    return track_names[track_id_to_human_track_id[track_id]]
