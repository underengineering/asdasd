
from enum import IntEnum

class PacketDirection(IntEnum):
	CLIENTBOUND = 0
	SERVERBOUND = 1

class ProtocolState(IntEnum):
	HANDSHAKING = 0
	STATUS = 1
	LOGIN = 2
	PLAY = 3
