import yaml
import subprocess
import pathlib
import random
import glob

test_config_indices = {
    8, 11
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

TEST_MULTIPLE_REGIONS = False

def main():
    pathlib.Path("temp").mkdir(exist_ok=True)
    pathlib.Path("test_vids").mkdir(exist_ok=True)

    for config_filename in glob.glob("test_ymls/*.yml"):
        config_basename = pathlib.Path(config_filename).name
        config_index = int(config_basename.split("_", maxsplit=1)[0])
        if config_index not in test_config_indices:
            continue

        with open(config_filename, "r") as f:
            config = yaml.safe_load(f)

        output_video_filepath_extension = config["output-video-filename"]
        output_video_filepath_stem = pathlib.Path(config_basename).stem

        if TEST_MULTIPLE_REGIONS:
            cur_region_filenames_and_names = region_filenames_and_names
        else:
            cur_region_filenames_and_names = (random.choice(region_filenames_and_names),)

        for region_filename_and_name in cur_region_filenames_and_names:
            print(f"Testing region {region_filename_and_name.name}, config {config_basename}")
            config["iso-filename"] = f"../../RMCE 01/{region_filename_and_name.filename}"
            config["output-video-filename"] = f"test_vids/{output_video_filepath_stem}_{region_filename_and_name.name}.{output_video_filepath_extension}"

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
