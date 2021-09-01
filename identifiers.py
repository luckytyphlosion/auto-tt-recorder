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

category_names = {
    -1: "(Default)",
    0: "Normal",
    1: "Glitch",
    2: "No-shortcut",
    16: "Shortcut"
}

def get_track_name_from_track_id(track_id):
    return track_names[track_id_to_human_track_id[track_id]]
