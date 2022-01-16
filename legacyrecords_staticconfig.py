import yaml
import legacyrecords_staticconfig

iso_filename = None
music_list_link = None
censored_players = None
output_video_directory = None
dolphin_resolution = None

def load():
    global iso_filename
    global music_list_link
    global censored_players
    global output_video_directory
    global dolphin_resolution

    with open("legacy_records.yml", "r") as f:
        static_config = yaml.safe_load(f)

    iso_filename = static_config["iso_filename"]
    music_list_link = static_config["music_list_link"]
    censored_players = static_config["censored_players"]
    output_video_directory = static_config["output_video_directory"]
    dolphin_resolution = static_config["dolphin_resolution"]

legacyrecords_staticconfig.load()
