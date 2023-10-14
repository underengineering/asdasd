
import asyncio
from typing import Any, List, Tuple

class IStreamReader:
	def at_eof(self) -> bool:
		raise NotImplementedError()

	async def read_line(self) -> bytes:
		raise NotImplementedError()

	async def read_until(self, separator: str = b"\n") -> bytes:
		raise NotImplementedError()

	async def read(self, num_bytes: int = -1) -> bytes:
		raise NotImplementedError()

	async def read_exactly(self, num_bytes: int) -> bytes:
		raise NotImplementedError()

class IStreamWriter:
	def write(self, data: bytes) -> None:
		raise NotImplementedError()

	def write_lines(self, lines: List[bytes]) -> None:
		raise NotImplementedError()

	def write_eof(self) -> None:
		raise NotImplementedError()

	def can_write_eof(self) -> bool:
		raise NotImplementedError()

	async def flush(self) -> None:
		raise NotImplementedError()

	async def wait_closed(self) -> None:
		raise NotImplementedError()

	def close(self) -> None:
		raise NotImplementedError()

	def is_closing(self) -> bool:
		raise NotImplementedError()

class AsyncIOStreamReader(IStreamReader):
	def __init__(self, stream: asyncio.StreamReader):
		self._stream = stream

	def at_eof(self) -> bool:
		return self._stream.at_eof()

	async def read_line(self) -> bytes:
		return await self._stream.readline()

	async def read_until(self, separator: str = b"\n") -> bytes:
		return await self._stream.readuntil(separator)

	async def read(self, num_bytes: int = -1) -> bytes:
		return await self._stream.read(num_bytes)

	async def read_exactly(self, num_bytes: int) -> bytes:
		return await self._stream.readexactly(num_bytes)

class AsyncIOStreamWriter(IStreamWriter):
	def __init__(self, stream: asyncio.StreamWriter):
		self._stream = stream

	def write(self, data: bytes) -> None:
		self._stream.write(data)

	def write_lines(self, lines: List[bytes]) -> None:
		self._stream.writelines(lines)

	def write_eof(self) -> None:
		self._stream.write_eof()

	def can_write_eof(self) -> bool:
		return self._stream.can_write_eof()

	async def flush(self) -> None:
		await self._stream.drain()

	async def wait_closed(self) -> None:
		await self._stream.wait_closed()

	def close(self) -> None:
		self._stream.close()

	def is_closing(self) -> bool:
		return self._stream.is_closing()

class ByteArrayStreamReader(IStreamWriter):
	def __init__(self, buffer: bytearray):
		self._buffer = buffer

	def at_eof(self) -> bool:
		return len(self._buffer) > 0

	async def read_line(self) -> bytes:
		newline_pos = self._buffer.find(b"\n")
		if newline_pos == -1:
			raise EOFError()

		return await self.read(newline_pos)

	# TODO
	async def read_until(self, separator: str = b"\n") -> bytes:
		raise NotImplementedError()

	async def read(self, num_bytes: int = -1) -> bytes:
		return await self.read_exactly(num_bytes)

	async def read_exactly(self, num_bytes: int) -> bytes:
		if len(self._buffer) < num_bytes:
			raise EOFError()

		data = self._buffer[:num_bytes]
		del self._buffer[:num_bytes]

		return data

class ByteArrayStreamWriter(IStreamWriter):
	def __init__(self, buffer: bytearray):
		self._buffer = buffer

	def write(self, data: bytes) -> None:
		self._buffer.extend(data)

	def write_lines(self, lines: List[bytes]) -> None:
		for line in lines:
			self.write(line)

	def write_eof(self) -> None:
		raise NotImplementedError()

	def can_write_eof(self) -> bool:
		raise NotImplementedError()

	async def flush(self) -> None:
		pass

	async def wait_closed(self) -> None:
		pass

	def close(self) -> None:
		pass

	def is_closing(self) -> bool:
		return False

# pylint: disable=abstract-method
class ByteArrayStreamReaderWriter(ByteArrayStreamReader, ByteArrayStreamWriter):
	pass
