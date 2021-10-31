
import struct
import dataclasses
from typing import Any

from .fields import Byte, PacketField
from ..varint import VarInt

__all__ = (
	"Packet", "packet"
)

class Packet:
	def __init__(self) -> None:
		self._setattr = self.__setattr__
		self._getattribute = self.__getattribute__

	def read_from(self, buffer: bytearray):
		""" Reads fields from buffer
		"""

		for slot_name in self.__slots__: # pylint: disable=no-member
			slot_value: PacketField = super().__getattribute__(slot_name)
			slot_value.read_from(buffer)

	def to_bytes(self) -> bytes:
		""" Encodes packet's fields
		"""

		buffer = bytearray()
		for slot_name in self.__slots__: # pylint: disable=no-member
			slot_value: PacketField = super().__getattribute__(slot_name)
			slot_value.write_to(buffer)

		return bytes(buffer)

	def _lock_attributes(self):
		""" Makes fields classes accessable
		"""

		super().__setattr__("__setattr__", self._setattr)
		super().__setattr__("__getattribute__", self._getattribute)

	def _unlock_attributes(self):
		""" Makes fields accessable only by setter and getter methods
		"""

		super().__setattr__("__setattr__", super().__setattr__)
		super().__setattr__("__getattribute__", super().__getattribute__)

	@staticmethod
	def _unlocked_method(func):
		def wrapper(self, *args, **kwargs):
			self._unlock_attributes()
			result = func(*args, **kwargs)
			self._lock_attributes()

			return result

		return wrapper

	def __setattr__(self, name: str, value: Any) -> None:
		try:
			field: PacketField = super().__getattribute__(name)
		except AttributeError:
			field_type = self.__annotations__[name] # pylint: disable=no-member
			super().__setattr__(name, field_type())
			return

		if not isinstance(field, PacketField):
			super().__setattr__(name, field)
			return

		if isinstance(value, PacketField):
			super().__setattr__(name, value)
			return

		field.setter(value)

	def __getattribute__(self, name: str) -> Any:
		field: PacketField = super().__getattribute__(name)
		if not isinstance(field, PacketField):
			return field

		return field.getter()

# From https://github.com/python/cpython/blob/39b4d5938ce781af41f8c9da72dee46095a78642/Lib/dataclasses.py#L1116
def _add_slots(cls):
	# Need to create a new class, since we can't set __slots__
	#  after a class has been created.

	# Make sure __slots__ isn't already set.
	if '__slots__' in cls.__dict__:
		raise TypeError(f'{cls.__name__} already specifies __slots__')

	# Create a new dict for our new class.
	cls_dict = dict(cls.__dict__)
	field_names = tuple(f.name for f in dataclasses.fields(cls))
	cls_dict['__slots__'] = field_names
	for field_name in field_names:
		# Remove our attributes, if present. They'll still be
		#  available in _MARKER.
		cls_dict.pop(field_name, None)

	# Remove __dict__ itself.
	cls_dict.pop('__dict__', None)

	# And finally create the class.
	qualname = getattr(cls, '__qualname__', None)
	cls = type(cls)(cls.__name__, cls.__bases__, cls_dict)
	if qualname is not None:
		cls.__qualname__ = qualname

	return cls

def packet(cls, init = True):
	""" Decorate packets with this
	"""

	cls = dataclasses.dataclass(cls, init = init, eq = False, match_args = False)
	cls = _add_slots(cls)

	return cls
