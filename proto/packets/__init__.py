
import logging
from typing import Type

from asyncraft.proto.packets.clientbound import *
from asyncraft.proto.packets.serverbound import *

from asyncraft.utils import Version
from asyncraft.proto import ProtocolState
from asyncraft.proto.packet import PacketDirection
from asyncraft.proto.packetparser import PacketParser

_packet_types = {
	PacketDirection.CLIENTBOUND: {
		ProtocolState.HANDSHAKING: {},
		ProtocolState.LOGIN: {},
		ProtocolState.PLAY: {}
	},
	PacketDirection.SERVERBOUND: {
		ProtocolState.HANDSHAKING: {},
		ProtocolState.LOGIN: {},
		ProtocolState.PLAY: {}
	}
}

def initialize_for(version: Version):
	""" Initializes packet ids
	"""

	import asyncraft.proto.packets as packets

	logging.info("Initializing asyncraft for version %s", version)

	packet_infos = PacketParser(version).parse()
	for packet_name in dir(packets):
		packet_class = getattr(packets, packet_name)
		if not isinstance(packet_class, type) or not issubclass(packet_class, Packet):
			continue

		submodules = packet_class.__module__.split(".")

		state = submodules[-1]
		direction = submodules[-2]

		for packet in packet_infos:
			if packet.state.name.lower() == state and				\
					packet.direction.name.lower() == direction and	\
					packet.name == packet_name:
				logging.debug("Setting up packet %s:%s:%s with id %s",
								packet.name,
								packet.state.name,
								packet.direction.name,
								hex(packet.id))

				_packet_types[packet.direction][packet.state][packet.id] = packet_class
				setattr(packet_class, "ID", packet.id)
				setattr(packet_class, "state", packet.state)
				setattr(packet_class, "direction", packet.direction)
				break

def get_packet_class(direction: PacketDirection, state: ProtocolState, packet_id: int) -> Type[Packet]:
	return _packet_types[direction][state][packet_id]
