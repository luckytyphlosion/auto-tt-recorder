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

dolphin_dirname = "dolphin"
storage_dirname = "storage"
temp_dirname = "temp"
wiimm_dirname = "bin/wiimm"

def set_dirnames(_dolphin_dirname, _storage_dirname, _temp_dirname, _wiimm_dirname):
    global dolphin_dirname, storage_dirname, temp_dirname, wiimm_dirname

    dolphin_dirname = _dolphin_dirname
    storage_dirname = _storage_dirname
    temp_dirname = _temp_dirname
    wiimm_dirname = _wiimm_dirname
