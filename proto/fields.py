
import struct
import json
from dataclasses import dataclass
from typing import Any, Dict, Tuple
from enum import IntEnum

from asyncraft.varint import VarInt, VarLong
from asyncraft.streams import IStreamWriter, IStreamReader, ByteArrayStreamWriter
from asyncraft.utils import unsigned_to_signed

__all__ = (
	"Bool", "Byte", "UByte",
	"Short", "UShort", "Int",
	"UInt", "Long", "ULong",
	"Float", "Double", "String",
	"VarIntField", "VarLongField",
	"Position", "Angle", "ChatColor",
	"ChatComponent", "ChatString", "InvalidIdentifierError",
	"Identifier"
)

# pylint: disable=abstract-method,bad-staticmethod-argument

class PacketField:
	def __init__(self, *args, **kwargs):
		raise NotImplementedError()

	def setter(self, value: Any) -> None:
		raise NotImplementedError()

	def getter(self) -> Any:
		raise NotImplementedError()

	@staticmethod
	async def _read_from_impl(self, stream: IStreamReader) -> Any:
		raise NotImplementedError()

	@classmethod
	async def read_from(cls, stream: IStreamReader) -> Any:
		""" Creates field from stream
		"""

		field = cls.__new__(cls)
		await cls._read_from_impl(field, stream)
		return field

	def write_to(self, stream: IStreamWriter) -> None:
		raise NotImplementedError

	def to_bytes(self) -> bytes:
		buffer = bytearray()
		stream = ByteArrayStreamWriter(buffer)
		self.write_to(stream)

		return bytes(buffer)

def _auto_pack(fmt: str):
	# All data sent over the network (except for VarInt and VarLong) is big-endian
	fmt = "!" + fmt

	def decorator(cls):
		async def custom_read_from_impl(self, stream: IStreamReader) -> Any:
			size = struct.calcsize(fmt)
			self.value = struct.unpack(fmt, await stream.read_exactly(size))[0]

		def custom_write_to(self, stream: IStreamWriter) -> None:
			data = struct.pack(fmt, self.value)
			stream.write(data)

		setattr(cls, "_read_from_impl", custom_read_from_impl)
		setattr(cls, "write_to", custom_write_to)

		return cls

	return decorator

def _auto_getset(cls):
	def custom_setter(self, value: Any) -> None:
		self.value = value

	def custom_getter(self) -> Any:
		return self.value

	setattr(cls, "setter", custom_setter)
	setattr(cls, "getter", custom_getter)

	return cls

@dataclass(slots = True)
@_auto_pack("?")
@_auto_getset
class Bool(PacketField):
	value: bool = 0

@dataclass(slots = True)
@_auto_pack("b")
@_auto_getset
class Byte(PacketField):
	value: int = 0

@dataclass(slots = True)
@_auto_pack("B")
@_auto_getset
class UByte(PacketField):
	value: int = 0

@dataclass(slots = True)
@_auto_pack("h")
@_auto_getset
class Short(PacketField):
	value: int = 0

@dataclass(slots = True)
@_auto_pack("H")
@_auto_getset
class UShort(PacketField):
	value: int = 0

@dataclass(slots = True)
@_auto_pack("i")
@_auto_getset
class Int(PacketField):
	value: int = 0

@dataclass(slots = True)
@_auto_pack("I")
@_auto_getset
class UInt(PacketField):
	value: int = 0

@dataclass(slots = True)
@_auto_pack("q")
@_auto_getset
class Long(PacketField):
	value: int = 0

@dataclass(slots = True)
@_auto_pack("Q")
@_auto_getset
class ULong(PacketField):
	value: int = 0

@dataclass(slots = True)
@_auto_pack("f")
@_auto_getset
class Float(PacketField):
	value: float = 0

@dataclass(slots = True)
@_auto_pack("d")
@_auto_getset
class Double(PacketField):
	value: float = 0

@dataclass(init = False, slots = True)
@_auto_getset
class String(PacketField):
	value: str = ""

	# pylint: disable=super-init-not-called
	def __init__(self, text: str):
		self.value = text

	@staticmethod
	async def _read_from_impl(self, stream: IStreamReader) -> None:
		length = await VarInt.read_from(stream)
		self.value = (await stream.read_exactly(length)).decode("utf-8")

	def write_to(self, stream: IStreamWriter) -> None:
		length = len(self.value.encode("utf-8"))
		VarInt.write_to(length, stream)
		stream.write(self.value.encode("utf-8"))

@dataclass(slots = True)
@_auto_getset
class VarIntField(PacketField):
	value: int = 0

	@staticmethod
	async def _read_from_impl(self, stream: IStreamReader) -> Any:
		self.value = await VarInt.read_from(stream)

	def write_to(self, stream: IStreamWriter) -> None:
		VarInt.write_to(self.value, stream)

@dataclass(slots = True)
@_auto_getset
class VarLongField(PacketField):
	value: int = 0

	@staticmethod
	async def _read_from_impl(self, stream: IStreamReader) -> Any:
		self.value = await VarLong.read_from(stream)

	def write_to(self, stream: IStreamWriter) -> None:
		VarLong.write_to(self.value, stream)

@dataclass(slots = True)
@_auto_getset
class VarByteArray(PacketField):
	value: bytearray

	@staticmethod
	async def _read_from_impl(self, stream: IStreamReader) -> Any:
		length = await VarInt.read_from(stream)
		self.value = await stream.read_exactly(length)

	def write_to(self, stream: IStreamWriter) -> None:
		VarInt.write_to(self.value, stream)

@dataclass(slots = True)
class Position(PacketField):
	x: int = 0
	y: int = 0
	z: int = 0

	def setter(self, value: Tuple[int, int, int]) -> None:
		self.x, self.y, self.z = value

	def getter(self):
		return self

	@staticmethod
	async def _read_from_impl(self, stream: IStreamReader) -> Any:
		xyz = struct.unpack_from("!Q", await stream.read_exactly(8))

		self.x = unsigned_to_signed(xyz >> 38, 26)
		self.y = unsigned_to_signed(xyz & 0xFFF, 12)
		self.z = unsigned_to_signed(xyz << 26 >> 38, 26)

	def write_to(self, stream: IStreamWriter) -> None:
		long = (self.x & 0x3FFFFFF) << 38	|	\
				(self.z & 0x3FFFFFF) << 12	|	\
				(self.y & 0xFFF)

		data = struct.pack("!q", long)
		stream.write(data)

Angle = Byte

class ChatColor(IntEnum):
	BLACK = 0
	DARK_BLUE = 1
	DARK_GREEN = 2
	DARK_CYAN = 3
	DARK_RED = 4
	PURPLE = 5
	GOLD = 6
	GRAY = 7
	DARK_GRAY = 8
	BLUE = 9
	BRIGHT_GREEN = 0xA
	CYAN = 0xB
	RED = 0xC
	PINK = 0xD
	YELLOW = 0xE
	WHITE = 0xF

	def to_str(self) -> str:
		return "§" + hex(self.value)[3]

class ChatComponent:
	__slots__ = ("_body",)

	def __init__(self) -> None:
		self._body: Dict[str, ChatComponent] = {}

	@staticmethod
	def bool_to_string(b) -> str:
		return "true" if b else "false"

	def set_text(self, text: str) -> None:
		self._body["text"] = text

	def set_bold(self, enabled: bool) -> None:
		self._body["bold"] = self.bool_to_string(enabled)

	def set_italic(self, enabled: bool) -> None:
		self._body["italic"] = self.bool_to_string(enabled)

	def set_underlined(self, enabled: bool) -> None:
		self._body["underlined"] = self.bool_to_string(enabled)

	def set_strikethrough(self, enabled: bool) -> None:
		self._body["strikethrough"] = self.bool_to_string(enabled)

	def set_obfuscated(self, enabled: bool) -> None:
		self._body["obfuscated"] = self.bool_to_string(enabled)

	def set_color(self, color: ChatColor) -> None:
		self._body["color"] = color.to_str()

	def add_component(self, component) -> None:
		if "extra" not in self._body:
			self._body["extra"] = []

		self._body["extra"].append(component)

	def to_json(self) -> str:
		return json.dumps(self._body)

	def __repr__(self) -> str:
		return self.to_json()

	def __str__(self) -> str:
		return self.to_json()

@dataclass(slots = True)
class ChatString(PacketField):
	root_component: ChatComponent = ChatComponent()

	def setter(self, value: ChatComponent) -> None:
		self.root_component = value

	def getter(self) -> ChatComponent:
		return self.root_component

	# TODO
	@staticmethod
	async def _read_from_impl(self, stream: IStreamReader) -> Any:
		raise NotImplementedError()

	def write_to(self, stream: IStreamWriter) -> None:
		json_data = self.root_component.to_json().encode("utf-8")
		VarInt.write_to(len(json_data), stream)
		stream.write(json_data)

class InvalidIdentifierError(ValueError):
	pass

@_auto_getset
class Identifier(PacketField):
	__slots__ = ("_value",)

	# pylint: disable=super-init-not-called
	def __init__(self) -> None:
		self._value = ""

	@property
	def value(self) -> str:
		return self._value

	@value.setter
	def value(self, identifier) -> None:
		valid_chars = "01​​234​5​6​78​9abcdefghijklmnopqrstuvwxyz-_"
		if any([char not in valid_chars for char in identifier]):
			raise InvalidIdentifierError()

		self._value = identifier

	@staticmethod
	async def _read_from_impl(self, stream: IStreamReader) -> Any:
		length = await VarInt.read_from(stream)
		self._value = await stream.read_exactly(length)

	def write_to(self, stream: IStreamWriter) -> None:
		VarInt.write_to(len(self.value), stream)
		stream.write(self.value.encode("utf-8"))
