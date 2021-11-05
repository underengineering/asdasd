
import dataclasses
from typing import Any, Type, TypeVar, overload

from asyncraft.proto.utils import PacketDirection, ProtocolState
from asyncraft.proto.fields import PacketField
from asyncraft.streams import IStreamReader, IStreamWriter, ByteArrayStreamWriter
from asyncraft.varint import VarInt

__all__ = (
	"Packet", "decorate_packet_type"
)

PacketT = TypeVar("PacketT", bound = "Packet")
class Packet:
	ID: int
	state: ProtocolState
	direction: PacketDirection

	@overload
	def get_field(self, name: str, default: Any = None) -> PacketField:
		...

	@classmethod
	async def read_from(cls: Type[PacketT], stream: IStreamReader) -> PacketT:
		""" Creates packet from stream
		"""

		new_packet = cls.__new__(cls)
		for field_name, field_type in cls.__annotations__.items():
			field_type: Type[PacketField] = field_type

			field: PacketField = await field_type.read_from(stream)
			setattr(new_packet, field_name, field)

		return new_packet

	def write_to(self, stream: IStreamWriter) -> None:
		""" Encodes packet's fields and writes it to stream
		"""

		VarInt.write_to(self.ID, stream)

		# pylint: disable=no-member
		for field_name in self.__annotations__:
			field = self.get_field(field_name)
			field.write_to(stream)

	# TODO
	def __to_bytes(self) -> bytes:
		""" Encodes packet's fields
		"""

		buffer = bytearray()
		stream = ByteArrayStreamWriter(buffer)
		for slot_name in self.__slots__: # pylint: disable=no-member
			slot_value: PacketField = super().__getattribute__(slot_name)
			slot_value.write_to(stream)

		return bytes(buffer)

	def __new__(cls: Type[PacketT], *args, **kwargs) -> PacketT: # pylint: disable=unused-argument
		decorate_packet_type(cls)
		return super(Packet, cls).__new__(cls)

def _create_descriptors(cls: Type[Packet]) -> None:
	for field in dataclasses.fields(cls):
		if not issubclass(field.type, PacketField):
			raise ValueError(f"Field {field.name!r} must inherit from PacketField")

		def create_descriptor(descriptor_name: str,
								field_name: str,
								field_type: Type[PacketField]) -> None:
			def getter(self: Packet) -> Any:
				field: PacketField = self.get_field(descriptor_name)
				return field.getter()

			def setter(self: Packet, value: Any) -> None:
				field: PacketField = self.get_field(descriptor_name)
				if field is None:
					field = field_type()
					setattr(self, field_name, field)

				field.setter(value)

			prop = property(fget = getter, fset = setter)
			setattr(cls, descriptor_name, prop)

		create_descriptor(field.name, "__" + field.name, field.type)

	# TODO: better method to get real fields
	def get_field_method(self, name: str, default: Any = None) -> PacketField:
		return getattr(self, "__" + name, default)

	setattr(cls, "get_field", get_field_method)

def decorate_packet_type(cls: Type[Packet] = None, /) -> Type[Packet]:
	""" Add descriptors to packet fields
	"""

	if cls is None:
		def decorator(cls: Type[Packet]) -> Type[Packet]:
			return decorate_packet_type(cls)

		return decorator

	if hasattr(cls, "__decorated"):
		return

	setattr(cls, "__decorated", True)

	_create_descriptors(cls)

	return cls
