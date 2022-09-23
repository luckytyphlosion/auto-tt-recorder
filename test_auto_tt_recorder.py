import yaml
import subprocess
import pathlib

test_config_filenames = (
    "test_150cc_default_drift_standard_som_no_bgm_lapmod.yml",
    "test_150cc_top10_region_filter_nohighlight_ht_standard_som_xz_main_ghost_auto_comparison_ghost_auto.yml",
    "test_200cc_regular_som_d0_comparison.yml",
    "test_200cc_top10_3rd_comparison_censors_regular_xyz_som_malaysia.yml",
    "test_200cc_fancy_som_d0.yml",
    "test_comparison_fancy_xz_som_d1.yml"
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

def main():
    pathlib.Path("temp").mkdir(exist_ok=True)

    for config_filename in test_config_filenames:
        with open(f"sample_ymls/{config_filename}", "r") as f:
            config = yaml.safe_load(f)

        output_video_filepath_unaltered = pathlib.Path(config["output-video-filename"])
        for region_filename_and_name in region_filenames_and_names:
            print(f"Testing region {region_filename_and_name.name}, config {config_filename}")
            config["iso-filename"] = f"../../RMCE 01/{region_filename_and_name.filename}"
            config["output-video-filename"] = f"{output_video_filepath_unaltered.stem}_{region_filename_and_name.name}{output_video_filepath_unaltered.suffix}"

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
