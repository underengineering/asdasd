
class VarIntTooBigError(ValueError):
	pass

class VarInt:
	SIZE: int = 4

	@classmethod
	def read_from(cls, buffer: bytearray) -> int:
		value = 0
		offset = 0

		while True:
			if offset >= cls.SIZE * 8:
				raise VarIntTooBigError()

			byte = buffer.pop(0)
			value |= (byte & 0x7F) << offset

			offset += 7

			if byte & 0x80 == 0:
				break

		max_value = 2 ** (cls.SIZE * 8 - 1) - 1
		if value >= max_value:
			value = -value + max_value

		return value

	@classmethod
	def write_to(cls, value: int, buffer: bytearray) -> bytes:
		print(cls)
		max_value = 2 ** (cls.SIZE * 8 - 1)
		if value >= max_value:
			raise VarIntTooBigError()

		if value < -max_value:
			raise VarIntTooBigError()

		# Convert to unsigned
		bit_mask = 2 ** (cls.SIZE * 8) - 1
		value &= bit_mask

		offset = 0
		while True:
			if value <= 0x7F:
				buffer.append(value)
				return

			buffer.append(value & 0x7F | 0x80)
			value >>= 7
			offset += 7

	@classmethod
	def from_bytes(cls, buffer: bytes) -> int:
		return cls.read_from(bytearray(buffer))

	@classmethod
	def to_bytes(cls, value: int) -> bytes:
		buffer = bytearray()
		cls.write_to(value, buffer)
		return bytes(buffer)

class VarLong(VarInt):
	SIZE: int = 8
