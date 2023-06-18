import yaml
import subprocess
import pathlib
import random

test_config_filenames = (
    #"test_comparison_fancy_xz_som_d1_folders1.yml",
    #"test_150cc_top10_region_filter_nohighlight_ht_standard_som_xz_main_ghost_auto_comparison_ghost_auto_no_bloom_folders2.yml",
    #"test_200cc_fancy_som_d0_chadsoft_cached_folder_nested_folders3.yml",
    "test_200cc_top10_3rd_comparison_censors_regular_xyz_som_malaysia_no_bloom_no_blur_chadsoft_cached.yml",
    "test_150cc_default_drift_standard_som_no_bgm_lapmod.yml",
    "test_200cc_regular_som_d0_comparison_no_blur.yml",
)

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

    for config_filename in test_config_filenames:
        with open(f"test_ymls/{config_filename}", "r") as f:
            config = yaml.safe_load(f)

        output_video_filepath_extension = config["output-video-filename"]
        output_video_filepath_stem = pathlib.Path(config_filename).stem

        if TEST_MULTIPLE_REGIONS:
            cur_region_filenames_and_names = region_filenames_and_names
        else:
            cur_region_filenames_and_names = (random.choice(region_filenames_and_names),)

        for region_filename_and_name in cur_region_filenames_and_names:
            print(f"Testing region {region_filename_and_name.name}, config {config_filename}")
            config["iso-filename"] = f"../../RMCE 01/{region_filename_and_name.filename}"
            config["output-video-filename"] = f"test_vids/{output_video_filepath_stem}_{region_filename_and_name.name}.{output_video_filepath_extension}"

            temp_config_filename = f"temp/{config_filename}"
            with open(temp_config_filename, "w+") as f:
                yaml.dump(config, f)

            completed_process = subprocess.run(("python3", "record_ghost.py", "-cfg", temp_config_filename))
            if completed_process.returncode == 0:
                print(f"SUCCESS: region {region_filename_and_name.name}, config {config_filename}")
            else:
                print(f"FAILURE: region {region_filename_and_name.name}, config {config_filename}")                

if __name__ == "__main__":
    main()
