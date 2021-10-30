import configparser
import shutil
import pathlib
import subprocess
import os

#ISO_FILE 
#ORIGINAL_TRACK_FILES_DIR = "original-race-course"

class WbzConverter:
    __slots__ = ("iso_filename", "original_track_files_dirname", "wit_filename", "wszst_filename", "auto_add_dirname", "config_filename", "config")

    def __init__(self, iso_filename, original_track_files_dirname, wit_filename, wszst_filename, auto_add_containing_dirname, config_filename):
        self.iso_filename = iso_filename
        self.original_track_files_dirname = original_track_files_dirname
        self.wit_filename = wit_filename
        self.wszst_filename = wszst_filename
        self.auto_add_dirname = f"{auto_add_containing_dirname}/auto-add"
        #self.config_filename = config_filename
        #self.read_config()

    #def read_config(self):
    #    config_filepath = pathlib.Path(self.config_filename)
    #    config_filepath.parent.mkdir(parents=True, exist_ok=True)
    #    if config_filepath.is_file():
    #        with open(config_filepath, "r") as f:
    #            self.config = configparser.ConfigParser(allow_no_value=True)
    #            self.config.read_file(f)
    #    else:
    #        self.config = configparser.ConfigParser(allow_no_value=True)
    #        self.config["Main"] = {
    #            "AutoAddFilesExtracted": False,
    #        }
    #
    #        self.serialize_config()
    #
    #def serialize_config(self):
    #    with open(self.config_filename, "w+") as f:
    #        self.config.write(f)

    def are_auto_add_files_extracted(self):
        return self.calc_num_files_dirs_in_auto_add_dir() >= 288
        #return self.config["Main"]["AutoAddFilesExtracted"]

    #def set_auto_add_files_extracted(self):
    #    #self.config["Main"]["AutoAddFilesExtracted"] = True
    #    #self.serialize_config()

    def calc_num_szs_files_in_orig_track_files_dir(self):
        original_track_files_dirpath = pathlib.Path(self.original_track_files_dirname)
        if not original_track_files_dirpath.is_dir():
            return -1

        return sum(1 for direntry in os.scandir(self.original_track_files_dirname) if direntry.is_file() and pathlib.Path(direntry).suffix == ".szs")

    def calc_num_files_dirs_in_auto_add_dir(self):
        auto_add_dirpath = pathlib.Path(self.auto_add_dirname)

        if not auto_add_dirpath.is_dir():
            return -1

        return len(os.listdir(self.auto_add_dirname))

    def extract_auto_add_files(self):
        if self.are_auto_add_files_extracted():
            return

        # check if ISO is valid
        subprocess.run((self.wit_filename, "imgfiles", self.iso_filename, "-1", "--include", "RMC.01"), check=True)

        original_track_files_dirpath = pathlib.Path(self.original_track_files_dirname)
        if original_track_files_dirpath.is_dir():
            shutil.rmtree(original_track_files_dirpath)

        subprocess.run((self.wit_filename, "extract", self.iso_filename, "-q", "--DEST", self.original_track_files_dirname, "--flat", "--files", "+/files/Race/Course/*.szs"), check=True)

        num_szs_files_in_orig_track_files_dir = self.calc_num_szs_files_in_orig_track_files_dir()

        if num_szs_files_in_orig_track_files_dir < 99:
            raise RuntimeError(f"Expected at least 99 szs files from original track files extracted from ISO, but found only {num_szs_files_in_orig_track_files_dir} instead! ISO possibly damaged?")

        subprocess.run((self.wszst_filename, "autoadd", self.original_track_files_dirname, "-q", "--DEST", self.auto_add_dirname, "--remove-dest", "--preserve"), check=True)

        num_files_dirs_in_auto_add_dir = self.calc_num_files_dirs_in_auto_add_dir()

        if num_files_dirs_in_auto_add_dir < 288:
            raise RuntimeError(f"Expected at least 288 files and directories in auto-add extracted from original track files, but found only {num_files_dirs_in_auto_add_dir} instead! ISO possibly damaged?")

        shutil.rmtree(original_track_files_dirpath)

    def convert_wbz_to_szs(self, input_wbz_filename, dest_dirname=None):
        self.extract_auto_add_files()

        input_wbz_filepath = pathlib.Path(input_wbz_filename)
        if dest_dirname is None:
            output_szs_filepath = input_wbz_filepath.with_suffix(".szs")
        else:
            output_szs_filepath = pathlib.Path(f"{dest_dirname}/{input_wbz_filepath.with_suffix('.szs').name}")
        
        if not output_szs_filepath.is_file():
            #print(f"self.auto_add_dirname: {self.auto_add_dirname}")
            subprocess.run((self.wszst_filename, "normalize", input_wbz_filename, "--autoadd-path", self.auto_add_dirname, "--DEST", output_szs_filepath, "--szs", "--overwrite"))

def main():
    wbz_converter = WbzConverter(
        iso_filename="../../RMCE01/RMCE01.iso",
        original_track_files_dirname="storage/original-race-course",
        wit_filename="bin/wiimm/cygwin64/wit.exe",
        wszst_filename="bin/wiimm/cygwin64/wszst.exe",
        auto_add_containing_dirname="storage",
        config_filename="storage/wbz_converter_config.ini"
    )

    wbz_converter.convert_wbz_to_szs("Jungle Cliff v1.5 (Wine+Keiichi1996) [r73,Jasperr,Hollend,Rachy].wbz", dest_dirname="storage/szs")
    wbz_converter.convert_wbz_to_szs("ASDF Course RC2 (Guilmon) [r24,5laps,maczkopeti].wbz", dest_dirname="storage/szs")

if __name__ == "__main__":
    main()
