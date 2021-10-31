
import struct
import json
from dataclasses import dataclass
from typing import Any, Dict, Tuple
from enum import IntEnum

from ..varint import VarInt, VarLong
from ..utils import unsigned_to_signed

__all__ = (
	"Bool", "Byte", "UByte",
	"Short", "UShort", "Int",
	"UInt", "Long", "ULong",
	"String"
)

class PacketField:
	def __init__(self, *args, **kwargs):
		raise NotImplementedError()

	def setter(self, value: Any) -> None:
		raise NotImplementedError()

	def getter(self) -> Any:
		raise NotImplementedError()

	def read_from(self, buffer: bytearray) -> None:
		raise NotImplementedError()

	def write_to(self, buffer: bytearray) -> None:
		buffer.extend(self.to_bytes())

	def to_bytes(self) -> bytes:
		raise NotImplementedError()

def _auto_pack(fmt: str):
	# All data sent over the network (except for VarInt and VarLong) is big-endian
	fmt = "!" + fmt

	def decorator(cls):
		def custom_read_from(self, buffer: bytearray) -> None:
			size = struct.calcsize(fmt)
			self.value = struct.unpack_from(fmt, buffer, 0)[0]
			del buffer[:size]

		def custom_write_to(self, buffer: bytearray) -> None:
			data = struct.pack(fmt, self.value)
			buffer.extend(data)

		def custom_to_bytes(self) -> None:
			return struct.pack(fmt, self.value)

		setattr(cls, "read_from", custom_read_from)
		setattr(cls, "write_to", custom_write_to)
		setattr(cls, "to_bytes", custom_to_bytes)

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

# pylint: disable=abstract-method

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
class String(PacketField):
	length: int = 0
	_text: str = ""

	# pylint: disable=super-init-not-called
	def __init__(self, text: str):
		self.length = len(text)
		self.text = text

	# pylint: disable=arguments-differ
	def setter(self, value: str) -> None:
		self.length = len(value.encode("utf-8"))
		self._text = value

	def getter(self) -> str:
		return self._text

	@property
	def text(self) -> str:
		return self._text

	@text.setter
	def text(self, text: str) -> None:
		self.length = len(text.encode("utf-8"))
		self._text = text

	def from_bytes(self, buffer: bytearray) -> None:
		self.length = VarInt.read_from(buffer)
		self._text = buffer[:self.length]
		del buffer[:self.length]

	def write_to(self, buffer: bytearray) -> None:
		VarInt.write_to(self.length, buffer)
		buffer.extend(self._text.encode("utf-8"))

	def to_bytes(self):
		return VarInt.encode(self.length) + self._text.encode("utf-8")

@dataclass(slots = True)
@_auto_getset
class VarIntField(PacketField, VarInt):
	value: int = 0

	def from_bytes(self, buffer: bytearray):
		self.value = super(__class__, VarInt).read_from(buffer)

	def to_bytes(self):
		return super(__class__, VarInt).to_bytes(self.value)

@dataclass(slots = True)
@_auto_getset
class VarLongField(PacketField, VarLong):
	value: int = 0

	def from_bytes(self, buffer: bytearray) -> None:
		self.value = super(__class__, VarLong).read_from(buffer)

	def to_bytes(self) -> bytes:
		return super(__class__, VarLong).to_bytes(self.value)

@dataclass(slots = True)
class Position(PacketField):
	x: int = 0
	y: int = 0
	z: int = 0

	def setter(self, value: Tuple[int, int, int]) -> None:
		self.x, self.y, self.z = value

	def getter(self):
		return self

	def from_bytes(self, buffer: bytearray):
		xyz = struct.unpack_from("!Q", buffer)

		self.x = unsigned_to_signed(xyz >> 38)
		self.y = unsigned_to_signed(xyz & 0xFFF)
		self.z = unsigned_to_signed(xyz << 26 >> 38)

	def write_to(self, buffer: bytearray) -> None:
		long = (self.x & 0x3FFFFFF) << 38	|	\
				(self.z & 0x3FFFFFF) << 12	|	\
				(self.y & 0xFFF)

		return struct.pack_into("!q", buffer, long)

	def to_bytes(self) -> bytes:
		long = (self.x & 0x3FFFFFF) << 38	|	\
				(self.z & 0x3FFFFFF) << 12	|	\
				(self.y & 0xFFF)

		return struct.pack("!q", long)

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

	def to_str(self):
		return "§" + hex(self.value)[3]

class ChatComponent:
	__slots__ = ("_body",)

	def __init__(self) -> None:
		self._body: Dict[str, ChatComponent] = {}

	@staticmethod
	def bool_to_string(b):
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

	def add_component(self, component):
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
class ChatString:
	root_component: ChatComponent = ChatComponent()

	def setter(self, component: ChatComponent) -> None:
		self.root_component = component

	def getter(self):
		return self.root_component

class InvalidIdentifierError(ValueError):
	pass

class Identifier:
	__slots__ = ("_value",)

	def __init__(self) -> None:
		self._value = ""

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, identifier):
		valid_chars = "01​​234​5​6​78​9abcdefghijklmnopqrstuvwxyz-_"
		if any([char not in valid_chars for char in identifier]):
			raise InvalidIdentifierError()

		self._value = identifier
