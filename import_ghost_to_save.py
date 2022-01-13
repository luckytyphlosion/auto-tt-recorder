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

# Much of this code was inspired and/or adapted from https://github.com/AtishaRibeiro/TT-Rec-Tools/tree/dev/ghostmanager
# Below is said code's license

# MIT License
# 
# Copyright (c) 2020 AtishaRibeiro
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import crclib
from abc import ABC, abstractmethod
import pathlib
import util
import identifiers

from stateclasses.split_classes import *

RKG_SIZE = 0x2800
MII_SIZE = 0x4a

BIG_ENDIAN = 0
LITTLE_ENDIAN = 1

class BitManipulator(ABC):
    __slots__ = ("data", "filename")

    def __init__(self, filename_or_data):
        if type(filename_or_data) == str:
            self.filename = filename_or_data
            with open(self.filename, "rb") as f:
                self.data = bytearray(f.read())
        elif type(filename_or_data) in (bytes, bytearray):
            self.filename = "<bytes>"
            self.data = bytearray(filename_or_data)
        else:
            raise RuntimeError("Input not filename or bytes-like object!")

    def read(self, offset):
        return self._read_unpacked(offset.byte_offset, offset.bit_offset, offset.size)

    def _read_unpacked(self, byte_offset, bit_offset, size):
        if bit_offset is not None:
            # read_bit is different than read_bits with size=1
            # because read_bit returns bool while read_bits returns int
            if size is not None:
                return self.read_bits(byte_offset, bit_offset, size)
            else:
                return self.read_bit(byte_offset, bit_offset)
        else:
            return self.read_num(byte_offset, size if size is not None else 1)

    def read_plus_byte_offset(self, offset, byte_offset):
        return self._read_unpacked(offset.byte_offset + byte_offset, offset.bit_offset, offset.size)

    def read_bit(self, byte_offset, bit_offset):
        # bit_range_check(bit_offset)
        return ((self.data[byte_offset] >> (7 - bit_offset)) & 1) == 1

    def read_num(self, byte_offset, size=1):
        if size == 1:
            return self.data[byte_offset]
        elif size == 2:
            return self.data[byte_offset] << 8 | self.data[byte_offset+1]
        elif size == 3:
            return self.data[byte_offset] << 16 | self.data[byte_offset+1] << 8 | self.data[byte_offset+2]
        elif size == 4:
            return self.data[byte_offset] << 24 | self.data[byte_offset+1] << 16 | self.data[byte_offset+2] << 8 | self.data[byte_offset+3]
        else:
            raise RuntimeError(f"Unsupported size {size}!")

    def read_bits(self, byte_offset, bit_offset, size):
        byte_offset_end = byte_offset + (bit_offset + size) // 8
        bit_offset_end = (bit_offset + size) % 8

        byte_offset_diff = byte_offset_end - byte_offset
        if byte_offset_diff == 0:
            result = ((self.data[byte_offset] << bit_offset) & 0xff) >> (8 - bit_offset_end + bit_offset)
        elif byte_offset_diff == 1:
            hi_part = ((self.data[byte_offset] << bit_offset) & 0xff) >> bit_offset
            lo_part = self.data[byte_offset+1] >> (8 - bit_offset_end)
            result = (hi_part << bit_offset_end) | lo_part
        elif byte_offset_diff > 1:
            hi_part = ((self.data[byte_offset] << bit_offset) & 0xff) >> bit_offset
            hi_part = hi_part << ((byte_offset_diff - 1) * 8 + bit_offset_end)
            
            for i in range(byte_offset_diff - 2, -1, -1):
                hi_part |= self.data[byte_offset+i+1] << (i * 8 + bit_offset_end)

            lo_part = self.data[byte_offset+byte_offset_diff] >> (8 - bit_offset_end)
            result = hi_part | lo_part
        else:
            raise RuntimeError(f"byte_offset_diff is negative! byte_offset_diff: {byte_offset_diff}")

        return result

    def read_range(self, offset):
        return self.data[offset.byte_offset:offset.byte_offset + offset.size]

    def write(self, offset, value):
        if offset.bit_offset is not None:
            self.write_bits(offset.byte_offset, offset.bit_offset, offset.size if offset.size is not None else 1, value)
        else:
            self.write_num(offset.byte_offset, offset.size, value)

    def write_bit(self, byte_offset, bit_offset, value):
        if value:
            self.set_bit(byte_offset, bit_offset)
        else:
            self.reset_bit(byte_offset, bit_offset)

    def write_num(self, byte_offset, size, value):
        if size == 1:
            self.data[byte_offset] = value
        elif size == 2:
            assert value < 65536
            self.data[byte_offset] = value >> 8
            self.data[byte_offset+1] = value & 0xff
        elif size == 3:
            assert value < 16777216
            self.data[byte_offset] = value >> 16
            self.data[byte_offset+1] = (value >> 8) & 0xff
            self.data[byte_offset+2] = value & 0xff
        elif size == 4:
            assert value <= 4294967295
            self.data[byte_offset] = value >> 24
            self.data[byte_offset+1] = (value >> 16) & 0xff
            self.data[byte_offset+2] = (value >> 8) & 0xff
            self.data[byte_offset+3] = value & 0xff
        else:
            raise RuntimeError(f"Unsupported size {size}!")

    def write_bits(self, byte_offset, bit_offset, size, value):
        while size > 0:
            size -= 1
            self.write_bit(byte_offset, bit_offset, (value >> size) & 1 == 1)
            bit_offset += 1
            if bit_offset == 8:
                bit_offset = 0
                byte_offset += 1

        #byte_offset_end = (bit_offset + size) // 8
        #bit_offset_end = (bit_offset + size) % 8
        #
        #byte_offset_diff = byte_offset_end - byte_offset
        #if byte_offset_diff == 0:
        #    mask = (((1 << size) - 1) ^ 0xff) << (8 - bit_offset_end)
        #    self.data[byte_offset] &= mask
        #    self.data[byte_offset] |= value << (8 - bit_offset_end)
        #elif byte_offset_diff == 1:
        #    lo_mask = 
        #    hi_part = ((self.data[byte_offset] << bit_offset) & 0xff) >> bit_offset
        #    lo_part = self.data[byte_offset+1] >> (8 - bit_offset_end)
        #    result = (hi_part << bit_offset_end) | lo_part
        #else:
        #    hi_part = ((self.data[byte_offset] << bit_offset) & 0xff) >> bit_offset
        #    hi_part = hi_part << ((byte_offset_diff - 1) * 8 + bit_offset_end)
        #    
        #    for i in range(byte_offset_diff - 2, -1, -1):
        #        hi_part |= self.data[byte_offset+i+1] << (i * 8 + bit_offset_end)
        #
        #    lo_part = self.data[byte_offset+byte_offset_diff] >> (8 - bit_offset_end)
        #    result = hi_part | lo_part

    def write_range(self, offset, value):
        self.data[offset.byte_offset:offset.byte_offset + offset.size] = value

    #def write_array_offset_range(self, array_offset, array_entry_size, 

    @staticmethod
    def bit_range_check(bit_offset):
        if not 0 <= bit_offset <= 7:
            raise RuntimeError(f"Bit offset out of range [0:7]! bit_offset: {bit_offset}")        

    def set_bit(self, byte_offset, bit_offset, endianness=BIG_ENDIAN, byte_range=None):
        #bit_range_check(bit_offset)

        if endianness == BIG_ENDIAN:
            byte_offset += bit_offset // 8
            bit_offset %= 8

            self.data[byte_offset] |= (1 << (7 - bit_offset))
        else:
            byte_offset += byte_range - 1 - bit_offset // 8
            bit_offset %= 8

            self.data[byte_offset] |= (1 << bit_offset)

    def reset_bit(self, byte_offset, bit_offset):
        #bit_range_check(bit_offset)

        byte_offset += bit_offset // 8
        bit_offset %= 8

        self.data[byte_offset] &= (1 << (7 - bit_offset)) ^ 0xff

# offset types:
# byte offset
# bit offset
# if bit_offset is defined, then this is a BitOffset
# otherwise, it is a byte_offset
class Offset:
    __slots__ = ("byte_offset", "bit_offset", "size")

    def __init__(self, byte_offset, bit_offset=None, size=None):
        self.byte_offset = byte_offset
        self.bit_offset = bit_offset
        self.size = size

    def get_array_offset(self, index):
        #if bit_offset is not None:
        #    raise RuntimeError("Method not valid for bit offset!")

        return Offset(self.byte_offset + index * self.size, self.bit_offset, self.size)

    def get_struct_offset(self, sub_offset):
        return Offset(self.byte_offset + sub_offset.byte_offset, sub_offset.bit_offset, sub_offset.size)

class Rkg(BitManipulator):
    oMINUTES = Offset(0x4, bit_offset=0, size=7)
    oSECONDS = Offset(0x4, bit_offset=7, size=7)
    oMILLISECONDS = Offset(0x5, bit_offset=6, size=10)
    oFINISH_TIME = Offset(0x4, None, 3)
    oTRACK_ID = Offset(0x7, bit_offset=0, size=6)
    oVEHICLE_ID = Offset(0x8, 0, 6)
    oCHARACTER_ID = Offset(0x8, 6, 6)
    oYEAR = Offset(0x9, 4, 7)
    oCONTROLLER_ID = Offset(0xb, 4, 4)
    oCOMPRESSED = Offset(0xc, 4)
    oGHOST_TYPE = Offset(0xc, 7, 7)
    oDRIFT_TYPE = Offset(0xd, 6)

    oLAP_COUNT = Offset(0x10)

    oLAP_1_SPLIT_MINUTES = Offset(0x11, 0, 7)
    oLAP_1_SPLIT_SECONDS = Offset(0x11, 7, 7)
    oLAP_1_SPLIT_MILLISECONDS = Offset(0x12, 6, 10)

    oCOUNTRY_CODE = Offset(0x34)
    oMII_DATA = Offset(0x3c, None, 0x4a)

    oCOMPRESSED_LEN = Offset(0x88, None, 4)
    oUNCOMPRESSED_LEN = Offset(0x90, None, 4)

    oINPUTS_byte_offset = 0x88
    oCOMPRESSED_INPUTS_HEADER_byte_offset = 0x8c
    oCOMPRESSED_INPUTS_DATA_byte_offset = 0x9c
    #oMII_DATA_END = oMII_DATA + oMII_SIZE

    GHOST_TYPE_PB = 1

    __slots__ = ("filename", "data", "rkg_file", "_track_id", "_compressed", "data",
        "_compressed_len", "_uncompressed_len", "_has_ctgp_data", "_mii", "_ghost_type", "_vehicle_id",
        "_character_id", "_controller", "_track_by_ghost_slot", "_drift_type", "_track_by_human_id",
        "_year", "_minutes", "_seconds", "_milliseconds", "_splits", "_lap_count", "_finish_time",
        "_country_code")

    def __init__(self, filename_or_data, apply_crc_every_write=False):
        super().__init__(filename_or_data)

        self._set_compressed_from_data()
        self._track_id = self.read(Rkg.oTRACK_ID)
        self._track_by_ghost_slot = identifiers.track_id_to_ghost_slot[self.track_id]
        self._track_by_human_id = identifiers.track_id_to_human_track_id[self.track_id]

        self._mii = self.read_range(Rkg.oMII_DATA)

        self._ghost_type = self.read(Rkg.oGHOST_TYPE)
        self._vehicle_id = self.read(Rkg.oVEHICLE_ID)
        self._character_id = self.read(Rkg.oCHARACTER_ID)
        self._controller = self.read(Rkg.oCONTROLLER_ID)
        self._drift_type = self.read(Rkg.oDRIFT_TYPE)
        self._has_ctgp_data = True
        self._year = self.read(Rkg.oYEAR)

        self._minutes = self.read(Rkg.oMINUTES)
        self._seconds = self.read(Rkg.oSECONDS)
        self._milliseconds = self.read(Rkg.oMILLISECONDS)
        self._finish_time = Split(self._minutes, self._seconds, self._milliseconds)

        self._lap_count = self.read(Rkg.oLAP_COUNT)

        splits = []

        for i in range(3):
            split_minutes = self.read_plus_byte_offset(Rkg.oLAP_1_SPLIT_MINUTES, i * 3)
            split_seconds = self.read_plus_byte_offset(Rkg.oLAP_1_SPLIT_SECONDS, i * 3)
            split_milliseconds = self.read_plus_byte_offset(Rkg.oLAP_1_SPLIT_MILLISECONDS, i * 3)
            splits.append(Split(split_minutes, split_seconds, split_milliseconds))

        self._splits = splits
        self._country_code = self.read(Rkg.oCOUNTRY_CODE)

    @property
    def year(self):
        return self._year

    @property
    def minutes(self):
        return self._minutes

    @property
    def seconds(self):
        return self._seconds

    @property
    def milliseconds(self):
        return self._milliseconds

    def time(self):
        return util.min_sec_ms_to_time(self.minutes, self.seconds, self.milliseconds)

    # track id
    @property
    def track_id(self):
        return self._track_id

    @property
    def track_id_by_ghost_slot(self):
        return self._track_by_ghost_slot

    @property
    def track_by_human_id(self):
        return self._track_by_human_id

    @property
    def compressed(self):
        return self._compressed    

    @compressed.setter
    def compressed(self, compressed):
        self._compressed = compressed
        self.write(Rkg.oCOMPRESSED, compressed)

    @property
    def ghost_type(self):
        return self._ghost_type

    @ghost_type.setter
    def ghost_type(self, ghost_type):
        self._ghost_type = ghost_type
        self.write(Rkg.oGHOST_TYPE, ghost_type)

    @property
    def vehicle_id(self):
        return self._vehicle_id

    @property
    def character_id(self):
        return self._character_id

    @property
    def controller(self):
        return self._controller

    @property
    def drift_type(self):
        return self._drift_type

    @property
    def mii(self):
        return self._mii

    @property
    def compressed_len(self):
        return self._compressed_len

    @property
    def uncompressed_len(self):
        return self._uncompressed_len

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, year):
        self._year = year
        self.write(Rkg.oYEAR, year)

    @property
    def splits(self):
        return self._splits

    @property
    def lap_count(self):
        return self._lap_count

    @property
    def finish_time(self):
        return self._finish_time

    @property
    def country_code(self):
        return self._country_code

    def _set_compressed_from_data(self):
        self._compressed = self.read(Rkg.oCOMPRESSED)
        if self.compressed:
            self._compressed_len = self.read(Rkg.oCOMPRESSED_LEN)
            self._uncompressed_len = self.read(Rkg.oUNCOMPRESSED_LEN)

    def remove_ctgp_data(self):
        # maybe all ctgp ghosts are compressed?
        if self.compressed and self._has_ctgp_data:
            #print(f"self.data len: {len(self.data)}")
            del self.data[self.compressed_len + Rkg.oCOMPRESSED_INPUTS_HEADER_byte_offset + 4:]
            #print(f"self.data len: {len(self.data)}")
            self._has_ctgp_data = False

    def decompress_inputs(self):
        if self.compressed:
            self.remove_ctgp_data()
            # + 4 to skip over Yaz1 header
            src_pos, dst_pos, dst = decode_yaz1(self.data, Rkg.oCOMPRESSED_INPUTS_DATA_byte_offset, self.compressed_len, self.uncompressed_len)
            del self.data[Rkg.oINPUTS_byte_offset:]
            self.data.extend(dst)
            self.compressed = False

    def prepare_for_import(self, is_pb_ghost, ghost_index=None):
        if is_pb_ghost:
            self.ghost_type = Rkg.GHOST_TYPE_PB
        else:
            self.ghost_type = ghost_index + 7

        pad_size = RKG_SIZE - 4 - len(self.data)
        if pad_size >= 0:
            self.data.extend(bytes(pad_size))
        else:
            del self.data[RKG_SIZE - 4:]

    def apply_crc(self):
        crc = crclib.crc32(self.data)
        self.data.extend(crc.to_bytes(length=4, byteorder="big"))

#class Mii:
#    oNAME = Offset(0x2, None, 20)
#    oID = Offset(0x18, None, 4)
#    oSYSTEM_ID = Offset(0x1c, None, 4)

class Rksys(BitManipulator):
    oCRC = Offset(0x27ffc, None, 4)
    oTL_LICENSE_GHOSTS = Offset(0x28000, None, RKG_SIZE)
    oTL_DOWNLOADED_GHOSTS = Offset(0x28000 + 0x50000, None, RKG_SIZE)
    oTL_LICENSE_LB_ENTRIES_BASE = Offset(0xdc0 + 0x8, None, 0x60)
    oTL_LICENSE_MII_NAME = Offset(0x14 + 0x8, None, 0x14)
    oTL_LICENSE_MII_ID = Offset(0x28 + 0x8, None, 4)
    oTL_LICENSE_MII_SYSTEM_ID = Offset(0x2c + 0x8, None, 4)
    oLB_ENTRY_TIME = Offset(0x4c, None, 3)
    oLB_VEHICLE_ID = Offset(0x4f, 0, 6)
    oLB_ENABLED = Offset(0x50, 0)
    oLB_CHARACTER_ID = Offset(0x50, 1, 7)
    oLB_CONTROLLER_ID = Offset(0x51, 0, 3)

    oTL_LICENSE_PB_FLAGS_byte_offset = 0x4 + 0x8
    oTL_LICENSE_DOWNLOADED_GHOST_FLAGS_byte_offset = 0x8 + 0x8

    def __init__(self, filename_or_data):
        super().__init__(filename_or_data)

    def set_pb_ghost_and_mii(self, rkg):
        self.write_range(Rksys.oTL_LICENSE_GHOSTS.get_array_offset(rkg.track_id_by_ghost_slot), rkg.data)
        #ghost_addr = Rksys.oTL_LICENSE_GHOSTS + rkg.track_id_by_ghost_slot * RKG_SIZE
        #self.data[ghost_addr:ghost_addr+RKG_SIZE] = rkg.data
        self.set_bit(Rksys.oTL_LICENSE_PB_FLAGS_byte_offset, rkg.track_id_by_ghost_slot, endianness=LITTLE_ENDIAN, byte_range=4)

        #lb_entries_addr = Rksys.oTL_LICENSE_LB_ENTRIES_BASE + 0x60 * rkg.track_id_by_ghost_slot

        self.write_range(
            Rksys.oTL_LICENSE_LB_ENTRIES_BASE
                .get_array_offset(rkg.track_id_by_ghost_slot)
                .get_struct_offset(Rksys.oLB_ENTRY_TIME),
            rkg.read_range(Rkg.oFINISH_TIME)
        )

        self.write(Rksys.oLB_VEHICLE_ID, rkg.vehicle_id)
        self.write(Rksys.oLB_ENABLED, 1)
        self.write(Rksys.oLB_CHARACTER_ID, rkg.character_id)
        self.write(Rksys.oLB_CONTROLLER_ID, rkg.controller)

        # TODO fix me!
        self.write_range(Rksys.oTL_LICENSE_MII_NAME, rkg.mii[0x2:0x16])
        self.write_range(Rksys.oTL_LICENSE_MII_ID, rkg.mii[0x18:0x1c])
        self.write_range(Rksys.oTL_LICENSE_MII_SYSTEM_ID, rkg.mii[0x1c:0x20])

        self.apply_crc()

    def set_downloaded_ghost_0(self, rkg):
        if rkg is None:
            return

        self.write_range(Rksys.oTL_DOWNLOADED_GHOSTS, rkg.data)

        self.set_bit(Rksys.oTL_LICENSE_DOWNLOADED_GHOST_FLAGS_byte_offset, 0, endianness=LITTLE_ENDIAN, byte_range=4)
        self.apply_crc()

    def apply_crc(self):
        crc = crclib.crc32(self.data, Rksys.oCRC.byte_offset)
        self.write_range(Rksys.oCRC, crc.to_bytes(length=4, byteorder="big"))

    def write_to_file(self, filename):
        pathlib.Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, "wb+") as f:
            f.write(self.data)

# Translated from https://github.com/AtishaRibeiro/TT-Rec-Tools/blob/56f020ea4072d246960b2976be5ee379d441fcd1/ghostmanager/Scripts/YAZ1_decomp.js#L3
def decode_yaz1(src, offset, src_size, uncompressed_size):
    dst = bytearray(uncompressed_size)

    src_pos = 0
    dst_pos = 0
    # current read/write positions
    src_place = 0
    dst_place = 0

    valid_bit_count = 0 # number of valid bits left in "code" byte
    cur_code_byte = src[offset + src_pos]
    #print(f"cur_code_byte: {cur_code_byte}")
    while dst_pos < uncompressed_size:
        #read new "code" byte if the current one is used up
        if valid_bit_count == 0:
            cur_code_byte = src[offset + src_pos]
            src_pos += 1
            valid_bit_count = 8

        if cur_code_byte & 0x80 != 0:
            #straight copy
            #print(f"dst_pos: {dst_pos}, offset: {offset}, src_pos: {src_pos}")
            dst[dst_pos] = src[offset + src_pos]
            dst_pos += 1
            src_pos += 1
            #if(src_pos >= src_size)
            #  return r
        else:
            #RLE part
            byte1 = src[offset + src_pos]
            byte2 = src[offset + src_pos + 1]
            src_pos += 2
            #if(src_pos >= src_size)
            #  return r

            dist = ((byte1 & 0xF) << 8) | byte2
            copy_src = dst_pos - (dist + 1)

            num_bytes = byte1 >> 4
            if num_bytes == 0:
                num_bytes = src[offset + src_pos] + 0x12
                src_pos += 1
                #if(src_pos >= src_size)
                #  return r
            else:
                num_bytes += 2

            #copy run
            for i in range(num_bytes):
                #print(f"dst_pos: {dst_pos}, copy_src: {copy_src}")
                dst[dst_pos] = dst[copy_src]
                copy_src += 1
                dst_pos += 1

        #use next bit from "code" byte
        cur_code_byte <<= 1
        valid_bit_count -= 1

    return src_pos, dst_pos, dst

def import_ghost_to_save(rksys_file, rkg_file_or_data, rksys_out_file, rfl_db_out_file, rkg_file_comparison=None):
    rkg = Rkg(rkg_file_or_data)

    rkg.remove_ctgp_data()
    rkg.decompress_inputs()
    rkg.prepare_for_import(True)
    rkg.apply_crc()

    if rkg_file_comparison is not None:
        rkg_comparison = Rkg(rkg_file_comparison)
        rkg_comparison.remove_ctgp_data()
        rkg_comparison.decompress_inputs()
        # todo, maybe centralize ghost download slot?
        rkg_comparison.prepare_for_import(False, 0)
        rkg_comparison.apply_crc()
    else:
        rkg_comparison = None

    rfl_db = bytearray(0x1f1de)
    rfl_db[:4] = b'RNOD'
    rfl_db[4:4+MII_SIZE] = rkg.mii
    rfl_db[0x1d00:0x1d04] = b'RNHD'
    crc = crclib.crc16_ccitt(rfl_db)
    rfl_db.extend(crc.to_bytes(length=2, byteorder="big"))

    pathlib.Path(rfl_db_out_file).parent.mkdir(parents=True, exist_ok=True)
    with open(rfl_db_out_file, "wb+") as f:
        f.write(rfl_db)

    rksys = Rksys(rksys_file)
    rksys.set_pb_ghost_and_mii(rkg)
    rksys.set_downloaded_ghost_0(rkg_comparison)

    rksys.write_to_file(rksys_out_file)

    return rkg, rkg_comparison

def test_read_bits():
    rkg_filename = "01m08s7732250 Cole.rkg"
    rkg = Rkg(rkg_filename)
    
    expected = 774
    actual = rkg.read_bits(0x5, 6, 10)
    print(f"milliseconds: expected: {expected}, actual: {actual}")

    expected = 0x16
    actual = rkg.read_bits(0x8, 6, 6)
    print(f"character: expected: {expected}, actual: {actual}")

    rkg.year = 60
    expected = 60
    actual = rkg.read_bits(0x9, 4, 7)
    print(f"year: expected: {expected}, actual: {actual}")

def main():
    MODE = 2

    if MODE == 0:
        import_ghost_to_save("rksys.dat", "01m08s7732250 Cole.rkg",
            "dolphin/User/Wii/title/00010004/524d4345/data/rksys.dat",
            "dolphin/User/Wii/shared2/menu/FaceLib/RFL_DB.dat")
    elif MODE == 1:
        import_ghost_to_save("rksys.dat", "bob_rpg_piranha_prowler.rkg",
            "dolphin/User/Wii/title/00010004/524d4345/data/rksys.dat",
            "dolphin/User/Wii/shared2/menu/FaceLib/RFL_DB.dat")
    elif MODE == 2:
        test_read_bits()
    else:
        print("No mode selected!")

if __name__ == "__main__":
    main()
