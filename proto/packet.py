
import dataclasses
from typing import Any, Type

from asyncraft.proto.utils import PacketDirection, ProtocolState
from asyncraft.proto.fields import PacketField
from asyncraft.streams import IStreamReader, IStreamWriter, ByteArrayStreamWriter
from asyncraft.varint import VarInt

__all__ = (
	"Packet", "packet"
)

class Packet:
	ID: int
	state: ProtocolState
	direction: PacketDirection

	def get_field(self, name: str) -> PacketField:
		return 0 # Calm down pylance

	@classmethod
	async def read_from(cls, stream: IStreamReader) -> Any:
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

def _create_fields(cls: Type[Packet]):
	for field_name, field_type in cls.__annotations__.items():
		if not issubclass(field_type, PacketField):
			raise ValueError(f"Field {field_name} must inherit from PacketField")

		def create_property(field_name, field_type):
			original_field_name = "__" + field_name
			def fget(self) -> Any:
				field: PacketField = getattr(self, original_field_name)
				return field.getter()

			def fset(self, value: Any) -> None:
				field: PacketField = getattr(self, original_field_name, None)
				if field is None:
					field = field_type()
					setattr(self, original_field_name, field)

				field.setter(value)

			prop = property(fget = fget, fset = fset)
			setattr(cls, field_name, prop)

		create_property(field_name, field_type)

	# TODO: better method to get real fields?
	def get_field_method(self, name: str):
		return getattr(self, "__" + name)

	setattr(cls, "get_field", get_field_method)

def packet(cls: Type[Packet] = None, init = True):
	""" Decorate packets with this
	"""

	if cls is None:
		def decorator(cls):
			return packet(cls, init = init)

		return decorator

	cls = dataclasses.dataclass(cls)
	_create_fields(cls)

	return cls
