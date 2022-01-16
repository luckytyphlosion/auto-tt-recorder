import yaml
import legacyrecords_staticconfig

iso_filename = None
music_list_link = None
censored_players = None

def load():
    global iso_filename
    global music_list_link
    global censored_players

    with open("legacy_records.yml", "r") as f:
        static_config = yaml.safe_load(f)

    iso_filename = static_config["iso_filename"]
    music_list_link = static_config["music_list_link"]
    censored_players = static_config["censored_players"]

legacyrecords_staticconfig.load()
