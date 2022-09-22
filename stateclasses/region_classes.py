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

from constants.regions import *

title_id_to_region = {
    TITLE_ID_PAL: REGION_PAL,
    TITLE_ID_NTSC_U: REGION_NTSC_U,
    TITLE_ID_NTSC_J: REGION_NTSC_J,
    TITLE_ID_NTSC_K: REGION_NTSC_K
}

title_id_to_hex_title_id = {
    TITLE_ID_PAL: "524d4350",
    TITLE_ID_NTSC_U: "524d4345",
    TITLE_ID_NTSC_J: "524d434a",
    TITLE_ID_NTSC_K: "524d434b"
}

class Region:
    __slots__ = ("name", "title_id", "hex_title_id")

    def __init__(self, title_id):
        self.title_id = title_id
        self.name = title_id_to_region[self.title_id]
        self.hex_title_id = title_id_to_hex_title_id[self.title_id]
