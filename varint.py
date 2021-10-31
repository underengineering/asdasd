
from asyncraft.streams import IStreamWriter, IStreamReader

class VarIntTooBigError(ValueError):
	pass

class VarInt:
	SIZE: int = 4

	@classmethod
	async def read_from(cls, stream: IStreamReader) -> int:
		value = 0
		offset = 0

		while True:
			if offset >= cls.SIZE * 8:
				raise VarIntTooBigError()

			byte = await stream.read_exactly(1)
			value |= (byte & 0x7F) << offset

			offset += 7

			if byte & 0x80 == 0:
				break

		max_value = 2 ** (cls.SIZE * 8 - 1) - 1
		if value >= max_value:
			value = -value + max_value

		return value

	@classmethod
	def write_to(cls, value: int, stream: IStreamWriter) -> bytes:
		max_value = 2 ** (cls.SIZE * 8 - 1)
		if value >= max_value:
			raise VarIntTooBigError()

		if value < -max_value:
			raise VarIntTooBigError()

		# Convert to unsigned
		bit_mask = 2 ** (cls.SIZE * 8) - 1
		value &= bit_mask

		buffer = bytearray()

		offset = 0
		while True:
			if value <= 0x7F:
				buffer.append(value)
				break

			buffer.append(value & 0x7F | 0x80)
			value >>= 7
			offset += 7

		stream.write(bytes(buffer))

class VarLong(VarInt):
	SIZE: int = 8
