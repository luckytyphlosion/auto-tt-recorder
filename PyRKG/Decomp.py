# This code was translated from Thakis' C++ Yaz0 decoder into python

def decode_RKG(ghost_src):
    # check uncompressed
    if (ghost_src[0xc] >> 3) & 1 == 0:
        return list(ghost_src[0x88:])
    else:
        uncompressed_size = (ghost_src[0x90] << 24) + (ghost_src[0x91] << 16) + (ghost_src[0x92] << 8) + ghost_src[0x93]
        return decode_Yaz1(ghost_src, 0x9c, uncompressed_size)

def decode_Yaz1(src, offset, uncompressedSize):
	srcPos = offset
	validBitCount = 0 # number of valid bits left in "code" byte
	currCodeByte = src[offset + srcPos]
	dst = []
	
	while len(dst) < uncompressedSize:
		# read new "code" byte if the current one is used up
		if validBitCount == 0:
			currCodeByte = src[srcPos]
			srcPos += 1
			validBitCount = 8

		if (currCodeByte & 0x80) != 0:
			# straight copy
			dst.append(src[srcPos])
			srcPos += 1
		else:
			# RLE part
			byte1 = src[srcPos]
			byte2 = src[srcPos + 1]
			srcPos += 2

			dist = ((byte1 & 0xF) << 8) | byte2
			copySource = len(dst) - (dist + 1)

			numBytes = byte1 >> 4
			if numBytes == 0:
				numBytes = src[srcPos] + 0x12
				srcPos += 1
			else:
				numBytes += 2

			# copy run
			for _ in range(numBytes):
				print(len(dst), copySource)
				dst.append(dst[copySource])
				copySource += 1

		# use next bit from "code" byte
		currCodeByte <<= 1
		validBitCount -= 1

	return dst

if __name__ == "__main__":
	file_name = "01m08s7732250 Cole.rkg"
	with open(file_name, "rb") as f:
		src = f.read()

	result = decode_RKG(src)
	print(result)