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

import struct
import os
import pathlib

REGION_PAL = "PAL"
REGION_NTSC_U = "NTSC-U"
REGION_NTSC_J = "NTSC-J"
REGION_NTSC_K = "NTSC-K"

TITLE_ID_PAL = "RMCP01"
TITLE_ID_NTSC_U = "RMCE01"
TITLE_ID_NTSC_J = "RMCJ01"
TITLE_ID_NTSC_K = "RMCK01"

title_code_to_region = {
    TITLE_ID_PAL: REGION_PAL,
    TITLE_ID_NTSC_U: REGION_NTSC_U,
    TITLE_ID_NTSC_J: REGION_NTSC_J,
    TITLE_ID_NTSC_K: REGION_NTSC_K
}

all_regions = set((REGION_PAL, REGION_NTSC_U, REGION_NTSC_J, REGION_NTSC_K))
all_title_ids = set((TITLE_ID_PAL, TITLE_ID_NTSC_U, TITLE_ID_NTSC_J, TITLE_ID_NTSC_K))

ISO_FORMAT_ISO = 0
ISO_FORMAT_WBFS = 1

good_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-/.\\:")

class IsMkwIsoResult:
    __slots__ = ("result", "reason")

    def __init__(self, result, reason=None):
        self.result = result
        self.reason = reason

class Iso:
    __slots__ = ("iso_filename", "format", "title_id", "region")

    def __init__(self, iso_filename):
        self.iso_filename = Iso.sanitize_and_check_iso_exists(iso_filename)

        is_mkw_iso = self.check_if_mkw_iso()

        if not is_mkw_iso.result:
            raise RuntimeError(f"{self.iso_filename} is not a valid Mario Kart Wii ISO! {is_mkw_iso.reason}")

        self.region = title_code_to_region[self.title_id]

    def check_if_mkw_iso(self):
        not_mkw_iso_reason = ""
        is_mkw_iso = True

        with open(self.iso_filename, "rb") as f:
            iso_first_6_bytes = f.read(6)
            potential_wbfs_magic = iso_first_6_bytes[:4].decode("ascii")

            if potential_wbfs_magic == "WBFS":
                self.format = ISO_FORMAT_WBFS
                # lol at wbfs documentation
                f.seek(8) # hd_sector_shift
                hd_sector_shift = ord(f.read(1))
                if hd_sector_shift >= 0x20:
                    return IsMkwIsoResult(False, "(Impossible hd_sector_shift value)")

                wii_header_offset = 1 << hd_sector_shift
                f.seek(wii_header_offset)
                iso_first_6_bytes = f.read(6)
                if len(iso_first_6_bytes) < 6:
                    return IsMkwIsoResult(False, "(Reached end of file while checking header)")
            else:
                self.format = ISO_FORMAT_ISO
                wii_header_offset = 0

            try:
                title_id = iso_first_6_bytes.decode("ascii")
            except UnicodeDecodeError:
                return IsMkwIsoResult(False, "(Garbage or corrupted title ID)")

            if title_id not in all_title_ids:
                return IsMkwIsoResult(False, "(Wrong title ID)")

            f.seek(wii_header_offset + 0x18)
            wii_magicword_as_bytes = f.read(4)
            if len(wii_magicword_as_bytes) < 4:
                return IsMkwIsoResult(False, "(Reached end of file while checking header)")

            wii_magicword = struct.unpack(">I", wii_magicword_as_bytes)[0]
            if wii_magicword != 0x5D1C9EA3:
                return IsMkwIsoResult(False, "(Wii disc identifier not found)")

            self.title_id = title_id

            return IsMkwIsoResult(True)

    @staticmethod
    def sanitize_and_check_iso_exists(iso_filename):
        # bug in Dolphin Lua Core will cause Dolphin's memory and disk usage to spike extremely
        # if the filename ends with spaces
        iso_filename = iso_filename.strip()
    
        #if not all(c in good_chars for c in iso_filename):
        #    bad_chars = set()
        #    for c in iso_filename:
        #        if c not in good_chars:
        #            bad_chars.add(c)
        #
        #    bad_chars_msg = ", ".join(f'"{c}"' for c in bad_chars)
        #
        #    raise RuntimeError(f"Found illegal characters in ISO path \"{iso_filename}\" to file (safeguard against shell injection)! Remove the following characters from your ISO filename: {bad_chars_msg}")
    
        iso_filepath = pathlib.Path(iso_filename)
        if not iso_filepath.exists():
            raise RuntimeError(f"Iso filename \"{iso_filename}\" does not exist!")

        # sanity size check so that future code doesn't reach end of file
        file_size = os.path.getsize(iso_filepath)
        if file_size < 0x300:
            raise RuntimeError("File \"{iso_filename}\" is too small to be a Mario Kart Wii ISO!")

        return iso_filename
