# This code was translated from Thakis' C++ Yaz0 decoder into python

def decode_RKG(src):
	readBytes = 0
	srcSize = len(src)
	decodedBytes = []
	header = []

	# search yaz1 block
	start_text = src[readBytes:readBytes+4]
	start_found = False
	while readBytes + 3 < srcSize:
		try:
			start_found = start_text.decode() == "Yaz1"
		except UnicodeDecodeError:
			pass
		if start_found:
			break
		
		readBytes += 1
		start_text = src[readBytes:readBytes+4]

	if readBytes + 3 >= srcSize:
		return decodedBytes # nothing left to decode

	header = list(src)[:readBytes]
	readBytes += 4

	og = src[readBytes:readBytes+4]
	size = (og[0] << 24) + (og[1] << 16) + (og[2] << 8) + og[3]
	readBytes += 12; # 4 byte size, 8 byte unused
	decodedBytes = decode_Yaz1(src, readBytes, size)

	return header + decodedBytes

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