import crclib
from abc import ABC, abstractmethod
import pathlib
import util
import identifiers

RKG_SIZE = 0x2800
MII_SIZE = 0x4a

BIG_ENDIAN = 0
LITTLE_ENDIAN = 1

class BitManipulator(ABC):
    __slots__ = ("data", "filename")

    def __init__(self, filename):
        self.filename = filename
        with open(filename, "rb") as f:
            self.data = bytearray(f.read())

    def read_bit(self, byte_offset, bit_offset):
        # bit_range_check(bit_offset)

        return ((self.data[byte_offset] >> (7 - bit_offset)) & 1) == 1

    def read_num(self, byte_offset, size):
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

    def write_bit(self, byte_offset, bit_offset, value):
        if value:
            self.set_bit(byte_offset, bit_offset)
        else:
            self.reset_bit(byte_offset, bit_offset)

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

class Split:
    __slots__ = ("minutes", "seconds", "milliseconds")

    def __init__(self, minutes, seconds, milliseconds):
        self.minutes = minutes
        self.seconds = seconds
        self.milliseconds = milliseconds

    def pretty(self):
        return f"{self.minutes:02d}:{self.seconds:02d}.{self.milliseconds:03d}"

class Rkg(BitManipulator):
    oMINUTES = 0x4
    oMINUTES_bit = 0
    oMINUTES_size = 7

    oSECONDS = 0x4
    oSECONDS_bit = 7
    oSECONDS_size = 7

    oMILLISECONDS = 0x5
    oMILLISECONDS_bit = 6
    oMILLISECONDS_size = 10

    oTRACK_ID = 0x7
    oTRACK_ID_bit = 0
    oTRACK_ID_size = 6

    oVEHICLE_ID = 0x8
    oVEHICLE_ID_bit = 0
    oVEHICLE_ID_size = 6

    oCHARACTER_ID = 0x8
    oCHARACTER_ID_bit = 6
    oCHARACTER_ID_size = 6

    oYEAR = 0x9
    oYEAR_bit = 4
    oYEAR_size = 7

    oCONTROLLER_ID = 0xb
    oCONTROLLER_ID_bit = 4
    oCONTROLLER_ID_size = 4

    oCOMPRESSED = 0xc
    oCOMPRESSED_bit = 4

    oGHOST_TYPE = 0xc
    oGHOST_TYPE_bit = 7
    oGHOST_TYPE_size = 7

    oDRIFT_TYPE = 0xd
    oDRIFT_TYPE_bit = 6

    oLAP_COUNT = 0x10

    oLAP_1_SPLIT_MINUTES = 0x11
    oLAP_1_SPLIT_MINUTES_bit = 0
    oLAP_1_SPLIT_MINUTES_size = 7

    oLAP_1_SPLIT_SECONDS = 0x11
    oLAP_1_SPLIT_SECONDS_bit = 7
    oLAP_1_SPLIT_SECONDS_size = 7

    oLAP_1_SPLIT_MILLISECONDS = 0x12
    oLAP_1_SPLIT_MILLISECONDS_bit = 6
    oLAP_1_SPLIT_MILLISECONDS_size = 10

    oINPUTS = 0x88
    oCOMPRESSED_LEN = 0x88
    oCOMPRESSED_INPUTS_HEADER = 0x8c
    oUNCOMPRESSED_LEN = 0x90
    oCOMPRESSED_INPUTS_DATA = 0x9c
    oMII_DATA = 0x3c
    oMII_SIZE = 0x4a
    oMII_DATA_END = oMII_DATA + oMII_SIZE

    GHOST_TYPE_PB = 1

    __slots__ = ("filename", "data", "rkg_file", "_track_id", "_compressed", "data",
        "_compressed_len", "_uncompressed_len", "_has_ctgp_data", "_mii", "_ghost_type", "_vehicle_id",
        "_character_id", "_controller", "_track_by_ghost_slot", "_drift_type", "_track_by_human_id",
        "_year", "_minutes", "_seconds", "_milliseconds", "_splits", "_lap_count")

    def __init__(self, filename, apply_crc_every_write=False):
        super().__init__(filename)

        self._set_compressed_from_data()
        self._track_id = self.read_bits(Rkg.oTRACK_ID, Rkg.oTRACK_ID_bit, Rkg.oTRACK_ID_size)
        self._track_by_ghost_slot = identifiers.track_id_to_ghost_slot[self.track_id]
        self._track_by_human_id = identifiers.track_id_to_human_track_id[self.track_id]

        self._mii = self.data[Rkg.oMII_DATA:Rkg.oMII_DATA_END]

        self._ghost_type = self.read_bits(Rkg.oGHOST_TYPE, Rkg.oGHOST_TYPE_bit, Rkg.oGHOST_TYPE_size)
        self._vehicle_id = self.read_bits(Rkg.oVEHICLE_ID, Rkg.oVEHICLE_ID_bit, Rkg.oVEHICLE_ID_size)
        self._character_id = self.read_bits(Rkg.oCHARACTER_ID, Rkg.oCHARACTER_ID_bit, Rkg.oCHARACTER_ID_size)
        self._controller = self.read_bits(Rkg.oCONTROLLER_ID, Rkg.oCONTROLLER_ID_bit, Rkg.oCONTROLLER_ID_size)
        self._drift_type = self.read_bit(Rkg.oDRIFT_TYPE, Rkg.oDRIFT_TYPE_bit)
        self._has_ctgp_data = True
        self._year = self.read_bits(Rkg.oYEAR, Rkg.oYEAR_bit, Rkg.oYEAR_size)
        self._minutes = self.read_bits(Rkg.oMINUTES, Rkg.oMINUTES_bit, Rkg.oMINUTES_size)
        self._seconds = self.read_bits(Rkg.oSECONDS, Rkg.oSECONDS_bit, Rkg.oSECONDS_size)
        self._milliseconds = self.read_bits(Rkg.oMILLISECONDS, Rkg.oMILLISECONDS_bit, Rkg.oMILLISECONDS_size)

        self._lap_count = self.read_num(Rkg.oLAP_COUNT, 1)

        splits = []

        for i in range(3):
            split_minutes = self.read_bits(Rkg.oLAP_1_SPLIT_MINUTES + i * 3, Rkg.oLAP_1_SPLIT_MINUTES_bit, Rkg.oLAP_1_SPLIT_MINUTES_size)
            split_seconds = self.read_bits(Rkg.oLAP_1_SPLIT_SECONDS + i * 3, Rkg.oLAP_1_SPLIT_SECONDS_bit, Rkg.oLAP_1_SPLIT_SECONDS_size)
            split_milliseconds = self.read_bits(Rkg.oLAP_1_SPLIT_MILLISECONDS + i * 3, Rkg.oLAP_1_SPLIT_MILLISECONDS_bit, Rkg.oLAP_1_SPLIT_MILLISECONDS_size)
            splits.append(Split(split_minutes, split_seconds, split_milliseconds))

        self._splits = splits

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
        self.write_bit(Rkg.oCOMPRESSED, Rkg.oCOMPRESSED_bit, compressed)

    @property
    def ghost_type(self):
        return self._ghost_type

    @ghost_type.setter
    def ghost_type(self, ghost_type):
        self._ghost_type = ghost_type
        self.write_bits(Rkg.oGHOST_TYPE, Rkg.oGHOST_TYPE_bit, Rkg.oGHOST_TYPE_size, ghost_type)

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
        self.write_bits(Rkg.oYEAR, Rkg.oYEAR_bit, Rkg.oYEAR_size, year)

    @property
    def splits(self):
        return self._splits

    @property
    def lap_count(self):
        return self._lap_count

    def _set_compressed_from_data(self):
        self._compressed = self.read_bit(Rkg.oCOMPRESSED, Rkg.oCOMPRESSED_bit)
        if self.compressed:
            self._compressed_len = self.read_num(Rkg.oCOMPRESSED_LEN, 4)
            self._uncompressed_len = self.read_num(Rkg.oUNCOMPRESSED_LEN, 4)

    def remove_ctgp_data(self):
        # maybe all ctgp ghosts are compressed?
        if self.compressed and self._has_ctgp_data:
            #print(f"self.data len: {len(self.data)}")
            del self.data[self.compressed_len + Rkg.oCOMPRESSED_INPUTS_HEADER + 4:]
            #print(f"self.data len: {len(self.data)}")
            self._has_ctgp_data = False

    def decompress_inputs(self):
        if self.compressed:
            self.remove_ctgp_data()
            # + 4 to skip over Yaz1 header
            src_pos, dst_pos, dst = decode_yaz1(self.data, Rkg.oCOMPRESSED_INPUTS_DATA, self.compressed_len, self.uncompressed_len)
            del self.data[Rkg.oINPUTS:]
            self.data.extend(dst)
            self.compressed = False

    def prepare_for_import(self, is_pb_ghost, ghost_index=None):
        if is_pb_ghost:
            self.ghost_type = Rkg.GHOST_TYPE_PB
        else:
            self.ghost_type = ghost_index + 7

        self.data.extend(bytes(RKG_SIZE - 4 - len(self.data)))

    def apply_crc(self):
        crc = crclib.crc32(self.data)
        self.data.extend(crc.to_bytes(length=4, byteorder="big"))

class Rksys(BitManipulator):
    oCRC = 0x27ffc
    oCRC_size = 4
    oCRC_end = oCRC + oCRC_size

    oTL_LICENSE_GHOSTS = 0x28000
    oTL_DOWNLOADED_GHOSTS = 0x28000 + 0x50000

    oTL_LICENSE_PB_FLAGS = 0x4 + 0x8
    oTL_LICENSE_LB_ENTRIES_BASE = 0xdc0 + 0x8

    oTL_LICENSE_DOWNLOADED_GHOST_FLAGS = 0x8 + 0x8

    oTL_LICENSE_MII_NAME = 0x14 + 0x8
    oTL_LICENSE_MII_NAME_size = 0x14
    oTL_LICENSE_MII_NAME_end = oTL_LICENSE_MII_NAME + oTL_LICENSE_MII_NAME_size

    oTL_LICENSE_MII_ID = 0x28 + 0x8
    oTL_LICENSE_MII_ID_size = 4
    oTL_LICENSE_MII_ID_end = oTL_LICENSE_MII_ID + oTL_LICENSE_MII_ID_size

    oTL_LICENSE_MII_SYSTEM_ID = 0x2c + 0x8
    oTL_LICENSE_MII_SYSTEM_ID_size = 4
    oTL_LICENSE_MII_SYSTEM_ID_end = oTL_LICENSE_MII_SYSTEM_ID + oTL_LICENSE_MII_SYSTEM_ID_size

    oLB_ENTRY_TIME = 0x4c
    oLB_ENTRY_TIME_END = 0x4f

    oLB_VEHICLE_ID = 0x4f
    oLB_VEHICLE_ID_bit = 0
    oLB_VEHICLE_ID_size = 6

    oLB_ENABLED = 0x50
    oLB_ENABLED_bit = 0

    oLB_CHARACTER_ID = 0x50
    oLB_CHARACTER_ID_bit = 1
    oLB_CHARACTER_ID_size = 7

    oLB_CONTROLLER_ID = 0x51
    oLB_CONTROLLER_ID_bit = 0
    oLB_CONTROLLER_ID_size = 3

    def __init__(self, filename):
        super().__init__(filename)

    def set_pb_ghost_and_mii(self, rkg):
        ghost_addr = Rksys.oTL_LICENSE_GHOSTS + rkg.track_id_by_ghost_slot * RKG_SIZE
        self.data[ghost_addr:ghost_addr+RKG_SIZE] = rkg.data
        self.set_bit(Rksys.oTL_LICENSE_PB_FLAGS, rkg.track_id_by_ghost_slot, endianness=LITTLE_ENDIAN, byte_range=4)

        lb_entries_addr = Rksys.oTL_LICENSE_LB_ENTRIES_BASE + 0x60 * rkg.track_id_by_ghost_slot

        # TODO fix me!
        self.data[lb_entries_addr + Rksys.oLB_ENTRY_TIME:lb_entries_addr + Rksys.oLB_ENTRY_TIME_END] = rkg.data[0x4:0x7]
        self.write_bits(Rksys.oLB_VEHICLE_ID, Rksys.oLB_VEHICLE_ID_bit, Rksys.oLB_VEHICLE_ID_size, rkg.vehicle_id)
        self.set_bit(Rksys.oLB_ENABLED, Rksys.oLB_ENABLED_bit)
        self.write_bits(Rksys.oLB_CHARACTER_ID, Rksys.oLB_CHARACTER_ID_bit, Rksys.oLB_CHARACTER_ID_size, rkg.character_id)
        self.write_bits(Rksys.oLB_CONTROLLER_ID, Rksys.oLB_CONTROLLER_ID_bit, Rksys.oLB_CONTROLLER_ID_size, rkg.controller)

        self.data[Rksys.oTL_LICENSE_MII_NAME:Rksys.oTL_LICENSE_MII_NAME_end] = rkg.mii[0x2:0x16]
        self.data[Rksys.oTL_LICENSE_MII_ID:Rksys.oTL_LICENSE_MII_ID_end] = rkg.mii[0x18:0x1c]
        self.data[Rksys.oTL_LICENSE_MII_SYSTEM_ID:Rksys.oTL_LICENSE_MII_SYSTEM_ID_end] = rkg.mii[0x1c:0x20]
        self.apply_crc()

    def set_downloaded_ghost_0(self, rkg):
        if rkg is None:
            return

        ghost_addr = Rksys.oTL_DOWNLOADED_GHOSTS
        self.data[ghost_addr:ghost_addr+RKG_SIZE] = rkg.data

        self.set_bit(Rksys.oTL_LICENSE_DOWNLOADED_GHOST_FLAGS, 0, endianness=LITTLE_ENDIAN, byte_range=4)
        self.apply_crc()

    def apply_crc(self):
        crc = crclib.crc32(self.data, Rksys.oCRC)
        self.data[Rksys.oCRC:Rksys.oCRC_end] = crc.to_bytes(length=4, byteorder="big")
        
    def write_to_file(self, filename):
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

def import_ghost_to_save(rksys_file, rkg_file, rksys_out_file, rfl_db_out_file, rkg_file_comparison=None):
    rkg = Rkg(rkg_file)
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
