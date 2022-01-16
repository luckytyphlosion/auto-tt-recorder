import yaml

iso_filename = None

def load():
    global iso_filename
    with open("legacy.yml", "r") as f:
        static_config = yaml.safe_load(f)

    iso_filename = static_config["iso_filename"]
