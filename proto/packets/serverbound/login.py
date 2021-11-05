
from dataclasses import dataclass

from asyncraft.proto.packet import Packet
from asyncraft.proto.fields import String

@dataclass
class LoginStart(Packet):
	user_name: String
