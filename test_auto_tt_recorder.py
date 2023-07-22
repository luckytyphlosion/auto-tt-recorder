import yaml
import subprocess
import pathlib
import random
import glob

test_config_include_indices = {

}
test_config_exclude_indices = {
    
}

class RegionFilenameAndName:
    __slots__ = ("filename", "name")

    def __init__(self, filename, name):
        self.filename = filename
        self.name = name

region_filenames_and_names = (
    RegionFilenameAndName("RMCE01.iso", "NTSC-U"),
    RegionFilenameAndName("RMCP01.wbfs", "PAL"),
    RegionFilenameAndName("RMCJ01.wbfs", "NTSC-J"),
    RegionFilenameAndName("RMCK01.wbfs", "NTSC-K")
)

region_names_except_selected = {
    "NTSC-U": ("PAL", "NTSC-J", "NTSC-K"),
    "PAL": ("NTSC-U", "NTSC-J", "NTSC-K"),
    "NTSC-J": ("NTSC-U", "PAL", "NTSC-K"),
    "NTSC-K": ("NTSC-U", "PAL", "NTSC-J")
}

TEST_MULTIPLE_REGIONS = False

def main():
    pathlib.Path("temp").mkdir(exist_ok=True)
    pathlib.Path("test_vids").mkdir(exist_ok=True)
    test_config_include_indices_len = len(test_config_include_indices)

    for config_filename in glob.glob("test_ymls/*.yml"):
        config_basename = pathlib.Path(config_filename).name
        config_index = int(config_basename.split("_", maxsplit=1)[0])
        if test_config_include_indices_len != 0 and config_index not in test_config_include_indices:
            continue
        elif config_index in test_config_exclude_indices:
            continue

        with open(config_filename, "r") as f:
            config = yaml.safe_load(f)

        output_video_filepath_extension = config["output-video-filename"]
        output_video_filepath_stem = pathlib.Path(config_basename).stem

        if TEST_MULTIPLE_REGIONS:
            cur_region_filenames_and_names = region_filenames_and_names
        else:
            cur_region_filenames_and_names = (random.choice(region_filenames_and_names),)
            #cur_region_filenames_and_names = (region_filenames_and_names[0],)

        for region_filename_and_name in cur_region_filenames_and_names:
            print(f"Testing region {region_filename_and_name.name}, config {config_basename}")
            config["iso-filename"] = f"../../RMCE 01/{region_filename_and_name.filename}"
            config["output-video-filename"] = f"test_vids/{output_video_filepath_stem}_{region_filename_and_name.name}.{output_video_filepath_extension}"

            extra_gecko_codes_filename = config.get("extra-gecko-codes-filename")
            if extra_gecko_codes_filename is not None and extra_gecko_codes_filename not in { "malformed_gecko_codes.ini", "colliding_gecko_codes.ini"}:
                extra_gecko_codes_filepath = pathlib.Path(extra_gecko_codes_filename)
                extra_gecko_codes_filename = f"{extra_gecko_codes_filepath.stem}_{region_filename_and_name.name}{extra_gecko_codes_filepath.suffix}"
                config["extra-gecko-codes-filename"] = extra_gecko_codes_filename

            top_10_gecko_code_filename = config.get("top-10-gecko-code-filename")
            if top_10_gecko_code_filename == "wrong_region.txt":
                wrong_region_name = random.choice(region_names_except_selected[region_filename_and_name.name])
                top_10_gecko_code_filename = f"gba_bc3_tops_{wrong_region_name}.txt"
                config["top-10-gecko-code-filename"] = top_10_gecko_code_filename
            elif top_10_gecko_code_filename == "gba_bc3_tops.txt":
                top_10_gecko_code_filepath = pathlib.Path(top_10_gecko_code_filename)
                top_10_gecko_code_filename = f"{top_10_gecko_code_filepath.stem}_{region_filename_and_name.name}{top_10_gecko_code_filepath.suffix}"
                config["top-10-gecko-code-filename"] = top_10_gecko_code_filename

            temp_config_filename = f"temp/{config_basename}"
            with open(temp_config_filename, "w+") as f:
                yaml.dump(config, f)

            completed_process = subprocess.run(("python3", "record_ghost.py", "-cfg", temp_config_filename))
            if completed_process.returncode == 0:
                print(f"SUCCESS: region {region_filename_and_name.name}, config {config_basename}")
            else:
                print(f"FAILURE: region {region_filename_and_name.name}, config {config_basename}")


if __name__ == "__main__":
    main()
