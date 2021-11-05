
from dataclasses import dataclass
from enum import IntEnum

from asyncraft.proto.packet import Packet
from asyncraft.proto.fields import String, UShort, VarIntField

class NextHandshakeState(IntEnum):
	STATUS = 1
	LOGIN = 2

@dataclass
class Handshake(Packet):
	proto_version: VarIntField
	server_address: String
	server_port: UShort
	next_state: VarIntField
