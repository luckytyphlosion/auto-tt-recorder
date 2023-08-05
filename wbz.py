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

import configparser
import shutil
import pathlib
import subprocess
import os
import requests

from stateclasses.wbz_classes import *

#ISO_FILE 
#ORIGINAL_TRACK_FILES_DIR = "original-race-course"

class WbzConverter:
    __slots__ = ("iso_filename", "original_track_files_dirname", "wit_filename", "wszst_filename", "auto_add_dirname", "auto_add_containing_dirname", "wbz_settings")

    def __init__(self, iso_filename, original_track_files_dirname, wit_filename, wszst_filename, auto_add_containing_dirname, wbz_settings):
        self.iso_filename = iso_filename
        self.original_track_files_dirname = original_track_files_dirname
        self.wit_filename = wit_filename
        self.wszst_filename = wszst_filename
        self.auto_add_dirname = f"{auto_add_containing_dirname}/auto-add"
        self.auto_add_containing_dirname = auto_add_containing_dirname
        self.wbz_settings = wbz_settings
        self.purge_auto_add_if_always_purge()

    def purge_auto_add_if_always_purge(self):
        if self.wbz_settings.purge_auto_add == PURGE_AUTO_ADD_ALWAYS:
            self.purge_auto_add()
            print(f"Removing auto-add directory \"{self.auto_add_dirname}\" as specified by purge-auto-add: always!")

    def purge_auto_add_if_onerror(self):
        if self.wbz_settings.purge_auto_add == PURGE_AUTO_ADD_ON_ERROR:
            self.purge_auto_add()
            print(f"Removing auto-add directory \"{self.auto_add_dirname}\" as specified by purge-auto-add: onerror!")
        else:
            self.purge_auto_add_if_always_purge()

    def purge_auto_add(self):
        auto_add_dirpath = pathlib.Path(self.auto_add_dirname)
        if auto_add_dirpath.is_dir():
            shutil.rmtree(auto_add_dirpath)
        elif auto_add_dirpath.is_file():
            auto_add_dirpath.unlink()

    def are_auto_add_files_extracted(self):
        return self.calc_num_files_dirs_in_auto_add_dir() >= 288

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

        original_track_files_dirpath = pathlib.Path(self.original_track_files_dirname)

        if self.wbz_settings.debug_manual_auto_add is None:
            #if self.wbz
            # check if ISO is valid
            try:
                completed_process = subprocess.run((self.wit_filename, "imgfiles", self.iso_filename, "-1", "--include", "RMC.01"), capture_output=True, encoding="utf-8")
            except OSError as e:
                raise RuntimeError(f"Command ran was ({(self.wit_filename, 'imgfiles', self.iso_filename, '-1', '--include', 'RMC.01')}).") from e
    
            print(completed_process.stdout)
            if completed_process.returncode != 0:
                raise RuntimeError(f"wit error occurred while checking for a valid ISO! error:\n\n{completed_process.stderr}")

            if original_track_files_dirpath.is_dir():
                shutil.rmtree(original_track_files_dirpath)
    
            completed_process = subprocess.run((self.wit_filename, "extract", self.iso_filename, "-q", "--DEST", self.original_track_files_dirname, "--flat", "--files", "+/files/Race/Course/*.szs"), capture_output=True, encoding="utf-8")
            print(completed_process.stdout)
            if completed_process.returncode != 0:
                raise RuntimeError(f"wit error occurred during ISO file extraction! error:\n\n{completed_process.stderr}")
    
            num_szs_files_in_orig_track_files_dir = self.calc_num_szs_files_in_orig_track_files_dir()
    
            if num_szs_files_in_orig_track_files_dir < 99 and not self.wbz_settings.ignore_auto_add_missing_files:
                self.purge_auto_add_if_onerror()
                raise RuntimeError(f"Was not able to extract all files needed for automatic SZS download via WBZ -> SZS patching. Your ISO may be damaged. If you would like to see if this matters, enable ignore-auto-add-missing-files: true.\n(Technical info: Expected at least 99 szs files from original track files extracted from ISO, but found only {num_szs_files_in_orig_track_files_dir} instead!)")
    
            completed_process = subprocess.run((self.wszst_filename, "autoadd", self.original_track_files_dirname, "-q", "--DEST", self.auto_add_dirname, "--remove-dest", "--preserve"), capture_output=True, encoding="utf-8")
            print(completed_process.stdout)
            if completed_process.returncode != 0:
                raise RuntimeError(f"wit error occurred during autoadd! error:\n\n{completed_process.stderr}")
        else:
            auto_add_dirpath = pathlib.Path(self.auto_add_dirname)
            if auto_add_dirpath.is_dir():
                shutil.rmtree(auto_add_dirpath)

            shutil.copytree(self.wbz_settings.debug_manual_auto_add, auto_add_dirpath)

        num_files_dirs_in_auto_add_dir = self.calc_num_files_dirs_in_auto_add_dir()

        if num_files_dirs_in_auto_add_dir < 288 and not self.wbz_settings.ignore_auto_add_missing_files:
            self.purge_auto_add_if_onerror()
            raise RuntimeError(f"Was not able to extract all files needed for automatic SZS download via WBZ -> SZS patching. Your ISO may be damaged. If you would like to see if this matters, enable ignore-auto-add-missing-files: true.\n(Technical info: Expected at least 288 files and directories in auto-add extracted from original track files, but found only {num_files_dirs_in_auto_add_dir} instead!)")

        if self.wbz_settings.debug_manual_auto_add is None:
            shutil.rmtree(original_track_files_dirpath)

    def get_wbz_filepath_from_track_id(self, track_id):
        return pathlib.Path(f"{self.auto_add_containing_dirname}/wbz/{track_id}.wbz")

    @staticmethod
    def get_output_szs_filepath(input_wbz_filepath, dest_dirname=None):
        if dest_dirname is None:
            output_szs_filepath = input_wbz_filepath.with_suffix(".szs")
        else:
            pathlib.Path(dest_dirname).mkdir(parents=True, exist_ok=True)
            output_szs_filepath = pathlib.Path(f"{dest_dirname}/{input_wbz_filepath.with_suffix('.szs').name}")

        return output_szs_filepath

    # necessary when manually adding tracks
    def get_output_szs_filepath_from_track_id(self, track_id, dest_dirname=None):
        wbz_filepath = self.get_wbz_filepath_from_track_id(track_id)
        output_szs_filepath = WbzConverter.get_output_szs_filepath(wbz_filepath, dest_dirname)

        return output_szs_filepath

    def download_wbz_get_filepath(self, track_id):
        wbz_filepath = self.get_wbz_filepath_from_track_id(track_id)
        if wbz_filepath.is_file():
            return wbz_filepath

        url = f"https://ct.wiimm.de/d/{track_id}"
        print(f"Downloading track {track_id}!")
        r = requests.get(url, allow_redirects=True)

        if r.headers["content-type"] != "application/octet-stream":
            raise RuntimeError("Wiimm's archive does not have track ID! You must supply the SZS file manually via the szs-filename command")

        wbz_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(wbz_filepath, 'wb+') as f:
            f.write(r.content)

        return wbz_filepath

    def convert_wbz_to_szs(self, input_wbz_filename, dest_dirname=None):
        self.extract_auto_add_files()

        input_wbz_filepath = pathlib.Path(input_wbz_filename)
        output_szs_filepath = WbzConverter.get_output_szs_filepath(input_wbz_filepath, dest_dirname)

        if not output_szs_filepath.is_file():
            completed_process = subprocess.run((self.wszst_filename, "normalize", input_wbz_filename, "--autoadd-path", self.auto_add_dirname, "--DEST", output_szs_filepath, "--szs", "--overwrite"), capture_output=True, encoding="utf-8")
            print(completed_process.stdout)
            if completed_process.returncode != 0:
                self.purge_auto_add_if_onerror()
                raise RuntimeError(f"wszst error occurred during conversion from wbz to szs! error:\n\n{completed_process.stderr}")

        return output_szs_filepath

    def download_wbz_convert_to_szs_get_szs_filename(self, track_id, use_auto_add_containing_dirname_as_dest=False):
        if use_auto_add_containing_dirname_as_dest:
            dest_dirname = f"{self.auto_add_containing_dirname}/szs"
        else:
            dest_dirname = None

        output_szs_filepath = self.get_output_szs_filepath_from_track_id(track_id, dest_dirname)
        if not output_szs_filepath.is_file():
            wbz_filepath = self.download_wbz_get_filepath(track_id)
            output_szs_filepath = self.convert_wbz_to_szs(wbz_filepath, dest_dirname)

        return str(output_szs_filepath)

def main():
    wbz_converter = WbzConverter(
        iso_filename="../../RMCE01/RMCE01.iso",
        original_track_files_dirname="storage/original-race-course",
        wit_filename="bin/wiimm/cygwin64/wit.exe",
        wszst_filename="bin/wiimm/cygwin64/wszst.exe",
        auto_add_containing_dirname="storage"
    )

    wbz_converter.convert_wbz_to_szs("Jungle Cliff v1.5 (Wine+Keiichi1996) [r73,Jasperr,Hollend,Rachy].wbz", dest_dirname="storage/szs")
    wbz_converter.convert_wbz_to_szs("ASDF Course RC2 (Guilmon) [r24,5laps,maczkopeti].wbz", dest_dirname="storage/szs")

if __name__ == "__main__":
    main()

