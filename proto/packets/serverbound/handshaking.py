
from enum import IntEnum

from asyncraft.proto.packet import Packet, packet
from asyncraft.proto.fields import String, UShort, VarIntField

class NextHandshakeState(IntEnum):
	STATUS = 1
	LOGIN = 2

@packet
class Handshake(Packet):
	proto_version: VarIntField
	server_address: String
	server_port: UShort
	next_state: VarIntField
